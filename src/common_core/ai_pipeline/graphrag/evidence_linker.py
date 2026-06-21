"""Evidence linking for GraphRAG extraction results."""

from pydantic import BaseModel

from common_core.ai_pipeline.graphrag.schemas import (
    ChunkInput,
    EvidenceBundle,
    EvidenceLinkRecord,
    EvidenceRecord,
    RelationCandidate,
    ResolvedEntity,
)


class EvidenceLinkOptions(BaseModel):
    """Options for evidence linking."""

    quote_window_chars: int = 300
    require_relation_evidence: bool = True
    default_support_type: str = "SUPPORTS"


class EvidenceLinker:
    """Create evidence records and target links for entities and relations."""

    def link(
        self,
        chunk: ChunkInput,
        entities: list[ResolvedEntity],
        relations: list[RelationCandidate],
        options: EvidenceLinkOptions | None = None,
    ) -> EvidenceBundle:
        """Link a chunk quote to extracted entities and relations."""

        options = options or EvidenceLinkOptions()
        quote = chunk.content[: options.quote_window_chars].strip()
        if not quote:
            return EvidenceBundle(warnings=[{"code": "EMPTY_CHUNK", "chunk_id": chunk.chunk_id}])

        evidence = EvidenceRecord(
            source_id=chunk.source_id,
            document_id=chunk.document_id,
            chunk_id=chunk.chunk_id,
            quote_text=quote,
            confidence_score=1.0,
            extraction_method="RULE",
        )

        links: list[EvidenceLinkRecord] = []
        for entity in entities:
            links.append(
                EvidenceLinkRecord(
                    target_type="ENTITY",
                    target_ref=entity.entity_id or entity.normalized_name,
                    support_type=options.default_support_type,
                    confidence_score=entity.confidence_score,
                )
            )
        for relation in relations:
            links.append(
                EvidenceLinkRecord(
                    target_type="RELATION",
                    target_ref=relation.candidate_id,
                    support_type=options.default_support_type,
                    confidence_score=relation.confidence_score,
                )
            )

        return EvidenceBundle(evidence=[evidence], links=links)

