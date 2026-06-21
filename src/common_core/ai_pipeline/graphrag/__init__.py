"""GraphRAG core contracts and default lightweight implementations."""

from common_core.ai_pipeline.graphrag.context_assembler import ContextAssembler
from common_core.ai_pipeline.graphrag.entity_extractor import EntityExtractor
from common_core.ai_pipeline.graphrag.evidence_linker import EvidenceLinker
from common_core.ai_pipeline.graphrag.hybrid_retriever import HybridRetriever
from common_core.ai_pipeline.graphrag.relation_extractor import RelationExtractor
from common_core.ai_pipeline.graphrag.schema_registry import SchemaRegistry
from common_core.ai_pipeline.graphrag.schemas import (
    AuthContext,
    ChunkInput,
    ContextAssembleRequest,
    ContextAssembleResult,
    DomainSchema,
    EntityCandidate,
    EvidenceBundle,
    EvidenceRecord,
    RelationCandidate,
    RetrievalItem,
    RetrievalRequest,
    RetrievalResponse,
)

__all__ = [
    "AuthContext",
    "ChunkInput",
    "ContextAssembler",
    "ContextAssembleRequest",
    "ContextAssembleResult",
    "DomainSchema",
    "EntityCandidate",
    "EntityExtractor",
    "EvidenceBundle",
    "EvidenceLinker",
    "EvidenceRecord",
    "HybridRetriever",
    "RelationCandidate",
    "RelationExtractor",
    "RetrievalItem",
    "RetrievalRequest",
    "RetrievalResponse",
    "SchemaRegistry",
]

