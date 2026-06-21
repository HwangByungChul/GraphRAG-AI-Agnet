"""Minimal workflow factory abstraction."""

from collections.abc import Callable
from typing import Any

from pydantic import BaseModel, Field


class WorkflowDefinition(BaseModel):
    """Workflow node order definition."""

    name: str
    nodes: list[str] = Field(default_factory=list)
    edges: list[tuple[str, str]] = Field(default_factory=list)


class WorkflowFactory:
    """Registry for workflow node callables.

    This is a lightweight bridge until LangGraph is added as an optional runtime
    dependency.
    """

    def __init__(self) -> None:
        self._nodes: dict[str, Callable[[dict[str, Any]], dict[str, Any]]] = {}

    def register_node(self, name: str, node: Callable[[dict[str, Any]], dict[str, Any]]) -> None:
        """Register a node callable by name."""

        self._nodes[name] = node

    def get_node(self, name: str) -> Callable[[dict[str, Any]], dict[str, Any]]:
        """Return a registered node."""

        try:
            return self._nodes[name]
        except KeyError as exc:
            raise KeyError(f"Workflow node is not registered: {name}") from exc

    def list_nodes(self) -> list[str]:
        """Return registered node names."""

        return sorted(self._nodes)

