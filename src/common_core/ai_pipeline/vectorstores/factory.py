"""Vector store adapter factory."""

from common_core.ai_pipeline.vectorstores.base import VectorStoreAdapter


class VectorStoreFactory:
    """Registry based factory for vector store adapters."""

    def __init__(self) -> None:
        self._providers: dict[str, VectorStoreAdapter] = {}

    def register(self, provider: str, adapter: VectorStoreAdapter) -> None:
        """Register a vector store adapter."""

        self._providers[provider.lower()] = adapter

    def get(self, provider: str) -> VectorStoreAdapter:
        """Return a registered adapter by provider name."""

        key = provider.lower()
        try:
            return self._providers[key]
        except KeyError as exc:
            raise KeyError(f"Vector store provider is not registered: {provider}") from exc

    def list_providers(self) -> list[str]:
        """Return registered provider names."""

        return sorted(self._providers)

