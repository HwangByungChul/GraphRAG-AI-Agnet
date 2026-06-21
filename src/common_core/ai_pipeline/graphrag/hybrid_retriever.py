"""Hybrid retrieval orchestration."""

from common_core.ai_pipeline.graphrag.context_assembler import ContextAssembler
from common_core.ai_pipeline.graphrag.graph_store import (
    EntityQuery,
    GraphStoreAdapter,
    GraphTraversalRequest,
)
from common_core.ai_pipeline.graphrag.schemas import (
    AuthContext,
    ContextAssembleRequest,
    RetrievalItem,
    RetrievalRequest,
    RetrievalResponse,
    RetrievalStatus,
    RetrievalStrategy,
)
from common_core.ai_pipeline.graphrag.scoring import calculate_hybrid_score
from common_core.ai_pipeline.vectorstores.base import VectorSearchRequest, VectorStoreAdapter


class HybridRetriever:
    """Combine vector search, graph traversal, evidence, and context assembly."""

    def __init__(
        self,
        vector_store: VectorStoreAdapter | None = None,
        graph_store: GraphStoreAdapter | None = None,
        context_assembler: ContextAssembler | None = None,
    ) -> None:
        self.vector_store = vector_store
        self.graph_store = graph_store
        self.context_assembler = context_assembler or ContextAssembler()

    def search(self, request: RetrievalRequest) -> RetrievalResponse:
        """Run retrieval and return evidence-aware context."""

        auth = request.auth or AuthContext()
        items: list[RetrievalItem] = []
        evidence = []

        if request.strategy in {RetrievalStrategy.VECTOR_ONLY, RetrievalStrategy.HYBRID}:
            if self.vector_store:
                vector_results = self.vector_store.search(
                    VectorSearchRequest(
                        domain=request.domain,
                        query=request.query,
                        filters=request.filters,
                        top_k=request.top_k,
                        auth=auth,
                    )
                )
                for result in vector_results:
                    score = calculate_hybrid_score(vector_score=result.score)
                    items.append(
                        RetrievalItem(
                            rank=0,
                            result_type="CHUNK",
                            chunk_id=result.chunk_id,
                            text=result.text,
                            score=score.final_score,
                            vector_score=result.score,
                            metadata={**result.metadata, "source_id": result.source_id},
                        )
                    )

        if request.strategy in {RetrievalStrategy.GRAPH_ONLY, RetrievalStrategy.HYBRID}:
            if self.graph_store:
                seed_entities = self.graph_store.find_entities(
                    EntityQuery(domain=request.domain, text=request.query, limit=request.top_k),
                    auth,
                )
                seed_ids = [entity.entity_id or entity.normalized_name for entity in seed_entities]
                if seed_ids:
                    graph_result = self.graph_store.traverse(
                        GraphTraversalRequest(
                            domain=request.domain,
                            seed_entity_ids=seed_ids,
                            max_depth=request.max_graph_depth,
                            limit=request.top_k * 5,
                        ),
                        auth,
                    )
                    evidence.extend(graph_result.evidence)
                    for relation in graph_result.relations:
                        score = calculate_hybrid_score(
                            graph_score=relation.confidence_score,
                            evidence_score=0.5 if graph_result.evidence else 0.0,
                        )
                        items.append(
                            RetrievalItem(
                                rank=0,
                                result_type="RELATION",
                                relation_id=relation.candidate_id,
                                text=relation.rationale or relation.relation_type,
                                score=score.final_score,
                                graph_score=relation.confidence_score,
                                evidence_score=0.5 if graph_result.evidence else 0.0,
                                metadata={"source_id": relation.source_id},
                            )
                        )

        ranked = sorted(items, key=lambda item: item.score, reverse=True)[: request.top_k]
        ranked = [item.model_copy(update={"rank": index}) for index, item in enumerate(ranked, 1)]
        context = self.context_assembler.assemble(
            ContextAssembleRequest(
                query=request.query,
                domain=request.domain,
                items=ranked,
                evidence=evidence,
            )
        )

        status = RetrievalStatus.HIT if ranked else RetrievalStatus.MISS
        return RetrievalResponse(
            domain=request.domain,
            query=request.query,
            status=status,
            results=ranked,
            context=context.context,
            evidence=evidence,
            metrics={"result_count": len(ranked), "strategy": request.strategy.value},
        )

