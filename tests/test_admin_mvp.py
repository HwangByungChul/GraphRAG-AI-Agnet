from common_core.admin import AdminService, GraphRAGSearchTestRequest, SourceCreateRequest
from common_core.admin.schemas import IndexJobRequest, IndexJobStatus, SourceStatus


def test_admin_service_source_index_and_search_flow():
    service = AdminService()
    source = service.create_source(
        SourceCreateRequest(
            domain="sol_bat",
            name="guide",
            content=(
                "Tomato disease prevention guide. "
                "Humid weather can cause disease and action can prevent disease."
            ),
        )
    )

    job = service.create_index_job(IndexJobRequest(source_id=source.source_id))
    completed = service.run_index_job(job.job_id)
    search = service.search_test(
        GraphRAGSearchTestRequest(domain="sol_bat", query="tomato disease", strategy="HYBRID")
    )

    assert service.get_source(source.source_id).status == SourceStatus.INDEXED
    assert completed.status == IndexJobStatus.COMPLETED
    assert completed.metrics["chunk_count"] >= 1
    assert search.status == "HIT"
    assert search.metrics["result_count"] >= 1


def test_admin_service_delete_source_removes_from_list():
    service = AdminService()
    source = service.create_source(SourceCreateRequest(domain="sol_bat", name="guide", content="Tomato guide"))

    deleted = service.delete_source(source.source_id)

    assert deleted.status == SourceStatus.DELETED
    assert service.list_sources() == []

