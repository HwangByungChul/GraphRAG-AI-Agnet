"""Build evidence-aware context for LLM and Agent workflows."""

from common_core.ai_pipeline.graphrag.schemas import (
    ContextAssembleRequest,
    ContextAssembleResult,
)


class ContextAssembler:
    """Assemble retrieval items and evidence into a compact context block."""

    def assemble(self, request: ContextAssembleRequest) -> ContextAssembleResult:
        """Create context text with simple citation markers."""

        lines = [
            "[Question]",
            request.query,
            "",
            "[Retrieved Evidence]",
        ]
        citations: list[dict] = []
        token_estimate = 0
        truncated = False

        evidence_by_chunk = {
            evidence.chunk_id: evidence for evidence in request.evidence if evidence.chunk_id
        }

        for index, item in enumerate(sorted(request.items, key=lambda value: value.score, reverse=True), 1):
            citation_id = f"E{index}"
            evidence = evidence_by_chunk.get(item.chunk_id)
            snippet = evidence.quote_text if evidence else item.text
            line = f"({citation_id}) {snippet}"
            token_estimate += max(1, len(line) // 4)
            if token_estimate > request.max_tokens:
                truncated = True
                break
            lines.append(line)
            lines.append(f"source={item.metadata.get('source_id', '')} chunk={item.chunk_id or ''}")
            citations.append(
                {
                    "citation_id": citation_id,
                    "chunk_id": item.chunk_id,
                    "evidence_id": evidence.evidence_id if evidence else None,
                    "score": item.score,
                }
            )

        if not citations:
            lines.append("No retrieval evidence was found.")

        return ContextAssembleResult(
            context="\n".join(lines),
            citations=citations,
            evidence=request.evidence,
            token_estimate=token_estimate,
            truncated=truncated,
        )

