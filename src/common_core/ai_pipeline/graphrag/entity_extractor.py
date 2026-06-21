"""Entity extraction contracts and a lightweight rule based implementation."""

from __future__ import annotations

import re
import unicodedata

from pydantic import BaseModel

from common_core.ai_pipeline.graphrag.schemas import ChunkInput, DomainSchema, EntityCandidate


class EntityExtractionOptions(BaseModel):
    """Options for entity extraction."""

    use_rule: bool = True
    use_llm: bool = False
    confidence_threshold: float = 0.60
    max_entities_per_chunk: int = 30
    language: str = "ko"
    model: str | None = None


class EntityExtractor:
    """Extract entity candidates from chunks.

    The first implementation is intentionally deterministic. LLM based
    extraction can be added behind the same interface in the next task.
    """

    def extract(
        self,
        chunk: ChunkInput,
        schema: DomainSchema,
        options: EntityExtractionOptions | None = None,
    ) -> list[EntityCandidate]:
        """Extract candidates from one chunk."""

        options = options or EntityExtractionOptions()
        if not chunk.content.strip() or not options.use_rule:
            return []

        content = unicodedata.normalize("NFC", chunk.content)
        candidates: list[EntityCandidate] = []
        seen: set[tuple[str, str, int]] = set()

        for entity_type in schema.entity_types:
            terms = [entity_type.type, *entity_type.aliases]
            for term in terms:
                if not term:
                    continue
                for match in re.finditer(re.escape(term), content, flags=re.IGNORECASE):
                    key = (entity_type.type, match.group(0).lower(), match.start())
                    if key in seen:
                        continue
                    seen.add(key)
                    candidates.append(
                        EntityCandidate(
                            domain=chunk.domain,
                            entity_type=entity_type.type,
                            name=match.group(0),
                            normalized_name=self.normalize_name(match.group(0)),
                            mention_text=match.group(0),
                            chunk_id=chunk.chunk_id,
                            source_id=chunk.source_id,
                            start_offset=match.start(),
                            end_offset=match.end(),
                            confidence_score=0.80,
                            extraction_method="RULE",
                        )
                    )
                    if len(candidates) >= options.max_entities_per_chunk:
                        return candidates
        return [
            candidate
            for candidate in candidates
            if candidate.confidence_score >= options.confidence_threshold
        ]

    @staticmethod
    def normalize_name(name: str) -> str:
        """Normalize an entity name for matching."""

        normalized = unicodedata.normalize("NFC", name)
        normalized = re.sub(r"\s+", " ", normalized).strip()
        return normalized.lower()

