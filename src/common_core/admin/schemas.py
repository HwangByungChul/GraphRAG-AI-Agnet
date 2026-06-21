"""Admin MVP DTOs."""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from common_core.ai_pipeline.document import SourceType


class AdminApiResponse(BaseModel):
    """Common admin API response envelope."""

    success: bool
    data: Any = None
    message: str = "ok"
    error: dict[str, Any] | None = None


class SourceStatus(str, Enum):
    """Source lifecycle status."""

    REGISTERED = "REGISTERED"
    INDEXING = "INDEXING"
    INDEXED = "INDEXED"
    FAILED = "FAILED"
    DELETED = "DELETED"


class IndexJobStatus(str, Enum):
    """Index job lifecycle status."""

    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class SourceCreateRequest(BaseModel):
    """Request to register source content."""

    domain: str
    source_type: SourceType = SourceType.TEXT
    name: str
    content: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    scope: str = "PRIVATE"
    tenant_id: str | None = None
    user_id: str | None = None


class SourceResponse(BaseModel):
    """Registered source response."""

    source_id: str
    domain: str
    source_type: SourceType
    name: str
    status: SourceStatus
    metadata: dict[str, Any] = Field(default_factory=dict)
    chunk_count: int = 0
    entity_count: int = 0
    relation_count: int = 0


class IndexJobRequest(BaseModel):
    """Index job request."""

    source_id: str
    job_type: str = "INDEX"
    options: dict[str, Any] = Field(default_factory=dict)


class IndexJobResponse(BaseModel):
    """Index job response."""

    job_id: str
    source_id: str
    status: IndexJobStatus
    step: str = "PENDING"
    message: str = ""
    metrics: dict[str, Any] = Field(default_factory=dict)
    error: dict[str, Any] | None = None


class GraphRAGSearchTestRequest(BaseModel):
    """Admin GraphRAG search test request."""

    domain: str
    query: str
    top_k: int = 5
    strategy: str = "HYBRID"
    filters: dict[str, Any] = Field(default_factory=dict)

