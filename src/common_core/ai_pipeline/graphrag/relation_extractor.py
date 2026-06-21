"""Relation extraction contracts and a deterministic baseline."""

from __future__ import annotations

from pydantic import BaseModel

from common_core.ai_pipeline.graphrag.schemas import (
    ChunkInput,
    DomainSchema,
    RelationCandidate,
    ResolvedEntity,
)


class RelationExtractionOptions(BaseModel):
    """Options for relation extraction."""

    use_llm: bool = False
    confidence_threshold: float = 0.60
    max_relations_per_chunk: int = 40
    allow_inferred_relation: bool = False
    model: str | None = None


class RelationExtractor:
    """Extract relation candidates between resolved entities."""

    def extract(
        self,
        chunk: ChunkInput,
        entities: list[ResolvedEntity],
        schema: DomainSchema,
        options: RelationExtractionOptions | None = None,
    ) -> list[RelationCandidate]:
        """Return schema-valid relation candidates for entities in the same chunk."""

        options = options or RelationExtractionOptions()
        if len(entities) < 2:
            return []

        candidates: list[RelationCandidate] = []
        for relation_type in schema.relation_types:
            for source in entities:
                for target in entities:
                    if source is target:
                        continue
                    if source.entity_type not in relation_type.source_types:
                        continue
                    if target.entity_type not in relation_type.target_types:
                        continue

                    candidates.append(
                        RelationCandidate(
                            domain=chunk.domain,
                            relation_type=relation_type.type,
                            source_entity_ref=source.entity_id or source.normalized_name,
                            target_entity_ref=target.entity_id or target.normalized_name,
                            source_entity_type=source.entity_type,
                            target_entity_type=target.entity_type,
                            chunk_id=chunk.chunk_id,
                            source_id=chunk.source_id,
                            confidence_score=0.65,
                            extraction_method="RULE",
                            rationale="Matched allowed relation pair in domain schema.",
                        )
                    )
                    if len(candidates) >= options.max_relations_per_chunk:
                        return candidates

        return [
            candidate
            for candidate in candidates
            if candidate.confidence_score >= options.confidence_threshold
        ]

