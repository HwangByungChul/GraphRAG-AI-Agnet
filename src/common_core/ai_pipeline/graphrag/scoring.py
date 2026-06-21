"""GraphRAG scoring helpers."""

from pydantic import BaseModel


class HybridScore(BaseModel):
    """Score parts used by hybrid retrieval."""

    vector_score: float = 0.0
    graph_score: float = 0.0
    evidence_score: float = 0.0
    recency_score: float = 0.0
    final_score: float = 0.0
    reason: str = ""


def calculate_hybrid_score(
    vector_score: float = 0.0,
    graph_score: float = 0.0,
    evidence_score: float = 0.0,
    recency_score: float = 0.0,
) -> HybridScore:
    """Calculate the default weighted hybrid retrieval score."""

    final_score = (
        vector_score * 0.60
        + graph_score * 0.25
        + evidence_score * 0.10
        + recency_score * 0.05
    )
    return HybridScore(
        vector_score=vector_score,
        graph_score=graph_score,
        evidence_score=evidence_score,
        recency_score=recency_score,
        final_score=final_score,
        reason="default_weighted_sum",
    )

