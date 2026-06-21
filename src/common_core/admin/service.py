"""Dependency-free Admin MVP service."""

from __future__ import annotations

from uuid import uuid4

from common_core.admin.schemas import (
    GraphRAGSearchTestRequest,
    IndexJobRequest,
    IndexJobResponse,
    IndexJobStatus,
    SourceCreateRequest,
    SourceResponse,
    SourceStatus,
)
from common_core.ai_pipeline.document import DocumentPipeline, DocumentSource
from common_core.ai_pipeline.graphrag import (
    AuthContext,
    EntityResolver,
    EvidenceLinker,
    HybridRetriever,
    InMemoryGraphStore,
    RelationExtractor,
    RetrievalRequest,
    RetrievalStrategy,
    SchemaRegistry,
)
from common_core.ai_pipeline.graphrag.entity_extractor import EntityExtractor
from common_core.ai_pipeline.vectorstores import InMemoryVectorStore, VectorWriteOptions


class AdminService:
    """In-memory admin service for MVP API and screen integration tests."""

    def __init__(
        self,
        document_pipeline: DocumentPipeline | None = None,
        vector_store: InMemoryVectorStore | None = None,
        graph_store: InMemoryGraphStore | None = None,
        schema_registry: SchemaRegistry | None = None,
    ) -> None:
        self.document_pipeline = document_pipeline or DocumentPipeline()
        self.vector_store = vector_store or InMemoryVectorStore()
        self.graph_store = graph_store or InMemoryGraphStore()
        self.schema_registry = schema_registry or SchemaRegistry.with_defaults()
        self.entity_extractor = EntityExtractor()
        self.entity_resolver = EntityResolver()
        self.relation_extractor = RelationExtractor()
        self.evidence_linker = EvidenceLinker()
        self.sources: dict[str, SourceCreateRequest] = {}
        self.source_status: dict[str, SourceResponse] = {}
        self.jobs: dict[str, IndexJobResponse] = {}

    def create_source(self, request: SourceCreateRequest) -> SourceResponse:
        """Register source content."""

        source_id = str(uuid4())
        self.sources[source_id] = request
        response = SourceResponse(
            source_id=source_id,
            domain=request.domain,
            source_type=request.source_type,
            name=request.name,
            status=SourceStatus.REGISTERED,
            metadata=request.metadata,
        )
        self.source_status[source_id] = response
        return response

    def list_sources(self) -> list[SourceResponse]:
        """List active sources."""

        return [
            source
            for source in self.source_status.values()
            if source.status != SourceStatus.DELETED
        ]

    def get_source(self, source_id: str) -> SourceResponse:
        """Return source status."""

        return self.source_status[source_id]

    def delete_source(self, source_id: str) -> SourceResponse:
        """Mark source deleted and remove indexed data."""

        source = self.source_status[source_id]
        self.vector_store.delete_by_source(source_id, AuthContext(roles=["ADMIN"]))
        self.graph_store.delete_by_source(source_id, AuthContext(roles=["ADMIN"]))
        deleted = source.model_copy(update={"status": SourceStatus.DELETED})
        self.source_status[source_id] = deleted
        return deleted

    def create_index_job(self, request: IndexJobRequest) -> IndexJobResponse:
        """Create an index job."""

        job_id = str(uuid4())
        job = IndexJobResponse(
            job_id=job_id,
            source_id=request.source_id,
            status=IndexJobStatus.PENDING,
            step="PENDING",
        )
        self.jobs[job_id] = job
        return job

    def run_index_job(self, job_id: str) -> IndexJobResponse:
        """Run an index job synchronously for MVP."""

        job = self.jobs[job_id].model_copy(update={"status": IndexJobStatus.RUNNING, "step": "PIPELINE"})
        self.jobs[job_id] = job
        source_request = self.sources[job.source_id]
        source = DocumentSource(
            source_id=job.source_id,
            domain=source_request.domain,
            source_type=source_request.source_type,
            name=source_request.name,
            content=source_request.content,
            metadata=source_request.metadata,
            tenant_id=source_request.tenant_id,
            user_id=source_request.user_id,
            scope=source_request.scope,
        )

        try:
            pipeline_result = self.document_pipeline.process(source)
            self.vector_store.add_chunks(
                pipeline_result.chunks,
                VectorWriteOptions(collection_name="default"),
            )
            schema = self.schema_registry.get(source.domain)
            entity_count = 0
            relation_count = 0
            for chunk in pipeline_result.chunks:
                candidates = self.entity_extractor.extract(chunk, schema)
                resolved = self.entity_resolver.resolve(candidates, schema)
                upserted_entities = self.graph_store.upsert_entities(resolved)
                entity_count += len(upserted_entities)
                entity_by_name = {entity.normalized_name: entity for entity in upserted_entities}
                resolved_with_ids = [
                    entity.model_copy(update={"entity_id": entity_by_name[entity.normalized_name].entity_id})
                    for entity in resolved
                    if entity.normalized_name in entity_by_name
                ]
                relations = self.relation_extractor.extract(chunk, resolved_with_ids, schema)
                upserted_relations = self.graph_store.upsert_relations(relations)
                relation_count += len(upserted_relations)
                self.graph_store.upsert_evidence(
                    self.evidence_linker.link(chunk, resolved_with_ids, upserted_relations)
                )

            source_status = self.source_status[job.source_id].model_copy(
                update={
                    "status": SourceStatus.INDEXED,
                    "chunk_count": len(pipeline_result.chunks),
                    "entity_count": entity_count,
                    "relation_count": relation_count,
                }
            )
            self.source_status[job.source_id] = source_status
            completed = job.model_copy(
                update={
                    "status": IndexJobStatus.COMPLETED,
                    "step": "COMPLETED",
                    "message": "index completed",
                    "metrics": {
                        "document_count": len(pipeline_result.documents),
                        "chunk_count": len(pipeline_result.chunks),
                        "entity_count": entity_count,
                        "relation_count": relation_count,
                    },
                }
            )
            self.jobs[job_id] = completed
            return completed
        except Exception as exc:
            failed = job.model_copy(
                update={
                    "status": IndexJobStatus.FAILED,
                    "step": "FAILED",
                    "message": "index failed",
                    "error": {"code": "INDEX_FAILED", "detail": str(exc)},
                }
            )
            self.jobs[job_id] = failed
            self.source_status[job.source_id] = self.source_status[job.source_id].model_copy(
                update={"status": SourceStatus.FAILED}
            )
            return failed

    def get_index_job(self, job_id: str) -> IndexJobResponse:
        """Return index job status."""

        return self.jobs[job_id]

    def list_index_jobs(self) -> list[IndexJobResponse]:
        """List index jobs."""

        return list(self.jobs.values())

    def search_test(self, request: GraphRAGSearchTestRequest):
        """Run GraphRAG search test."""

        retriever = HybridRetriever(
            vector_store=self.vector_store,
            graph_store=self.graph_store,
        )
        return retriever.search(
            RetrievalRequest(
                domain=request.domain,
                query=request.query,
                top_k=request.top_k,
                strategy=RetrievalStrategy(request.strategy),
                filters=request.filters,
                auth=AuthContext(roles=["ADMIN"]),
            )
        )

