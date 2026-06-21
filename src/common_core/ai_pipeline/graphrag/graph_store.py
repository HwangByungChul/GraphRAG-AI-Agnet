"""Graph store adapter contracts."""

from __future__ import annotations

from typing import Protocol

from pydantic import BaseModel, Field

from common_core.ai_pipeline.graphrag.schemas import (
    AuthContext,
    EvidenceBundle,
    EvidenceRecord,
    RelationCandidate,
    ResolvedEntity,
)


class EntityQuery(BaseModel):
    """Entity search query."""

    domain: str
    text: str | None = None
    entity_ids: list[str] = Field(default_factory=list)
    entity_types: list[str] = Field(default_factory=list)
    filters: dict = Field(default_factory=dict)
    limit: int = 20


class RelationQuery(BaseModel):
    """Relation search query."""

    domain: str
    source_entity_ids: list[str] = Field(default_factory=list)
    target_entity_ids: list[str] = Field(default_factory=list)
    relation_types: list[str] = Field(default_factory=list)
    filters: dict = Field(default_factory=dict)
    limit: int = 50


class EvidenceQuery(BaseModel):
    """Evidence search query."""

    domain: str
    evidence_ids: list[str] = Field(default_factory=list)
    target_type: str | None = None
    target_ids: list[str] = Field(default_factory=list)
    source_ids: list[str] = Field(default_factory=list)
    limit: int = 50


class GraphTraversalRequest(BaseModel):
    """Graph traversal request."""

    domain: str
    seed_entity_ids: list[str]
    relation_types: list[str] = Field(default_factory=list)
    max_depth: int = 2
    direction: str = "BOTH"
    limit: int = 100
    include_evidence: bool = True


class GraphTraversalResult(BaseModel):
    """Graph traversal result."""

    entities: list[ResolvedEntity] = Field(default_factory=list)
    relations: list[RelationCandidate] = Field(default_factory=list)
    evidence: list[EvidenceRecord] = Field(default_factory=list)
    paths: list[dict] = Field(default_factory=list)


class GraphDeleteResult(BaseModel):
    """Graph delete result."""

    deleted_entities: int = 0
    deleted_relations: int = 0
    deleted_evidence: int = 0


class GraphStoreAdapter(Protocol):
    """Provider-neutral graph store adapter."""

    def upsert_entities(self, entities: list[ResolvedEntity]) -> list[ResolvedEntity]:
        """Insert or update canonical entities."""

    def upsert_relations(self, relations: list[RelationCandidate]) -> list[RelationCandidate]:
        """Insert or update relations."""

    def upsert_evidence(self, bundle: EvidenceBundle) -> EvidenceBundle:
        """Insert or update evidence and links."""

    def find_entities(self, query: EntityQuery, auth: AuthContext) -> list[ResolvedEntity]:
        """Find entities visible to the requester."""

    def traverse(
        self,
        request: GraphTraversalRequest,
        auth: AuthContext,
    ) -> GraphTraversalResult:
        """Traverse graph from seed entities."""

    def delete_by_source(self, source_id: str, auth: AuthContext) -> GraphDeleteResult:
        """Delete graph data for one source."""


class InMemoryGraphStore:
    """Small in-memory graph store for tests and early local development."""

    def __init__(self) -> None:
        self.entities: list[ResolvedEntity] = []
        self.relations: list[RelationCandidate] = []
        self.evidence: list[EvidenceRecord] = []

    def upsert_entities(self, entities: list[ResolvedEntity]) -> list[ResolvedEntity]:
        self.entities.extend(entities)
        return entities

    def upsert_relations(self, relations: list[RelationCandidate]) -> list[RelationCandidate]:
        self.relations.extend(relations)
        return relations

    def upsert_evidence(self, bundle: EvidenceBundle) -> EvidenceBundle:
        self.evidence.extend(bundle.evidence)
        return bundle

    def find_entities(self, query: EntityQuery, auth: AuthContext) -> list[ResolvedEntity]:
        results = [entity for entity in self.entities if entity.domain == query.domain]
        if query.text:
            text = query.text.lower()
            results = [
                entity
                for entity in results
                if text in entity.normalized_name.lower() or text in entity.name.lower()
            ]
        if query.entity_types:
            allowed = set(query.entity_types)
            results = [entity for entity in results if entity.entity_type in allowed]
        return results[: query.limit]

    def traverse(
        self,
        request: GraphTraversalRequest,
        auth: AuthContext,
    ) -> GraphTraversalResult:
        seed_refs = set(request.seed_entity_ids)
        relations = [
            relation
            for relation in self.relations
            if relation.source_entity_ref in seed_refs or relation.target_entity_ref in seed_refs
        ][: request.limit]
        refs = seed_refs | {item.source_entity_ref for item in relations} | {
            item.target_entity_ref for item in relations
        }
        entities = [
            entity
            for entity in self.entities
            if (entity.entity_id or entity.normalized_name) in refs
        ]
        return GraphTraversalResult(entities=entities, relations=relations, evidence=self.evidence)

    def delete_by_source(self, source_id: str, auth: AuthContext) -> GraphDeleteResult:
        before_entities = len(self.entities)
        before_relations = len(self.relations)
        before_evidence = len(self.evidence)
        self.entities = [
            entity for entity in self.entities if source_id not in entity.evidence_chunk_ids
        ]
        self.relations = [relation for relation in self.relations if relation.source_id != source_id]
        self.evidence = [evidence for evidence in self.evidence if evidence.source_id != source_id]
        return GraphDeleteResult(
            deleted_entities=before_entities - len(self.entities),
            deleted_relations=before_relations - len(self.relations),
            deleted_evidence=before_evidence - len(self.evidence),
        )

