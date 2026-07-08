"""Dependency graph for Project Bible, EOs, specs, prompts, and Case Files."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class DependencyNodeType(str, Enum):
    """Supported dependency graph node types."""

    PROJECT_BIBLE = "PB"
    ENGINEERING_ORDER = "EO"
    STAFF_SPECIFICATION = "SP"
    INTERFACE_SPECIFICATION = "IF"
    DATABASE_SPECIFICATION = "DB"
    API_SPECIFICATION = "API"
    TEST_SPECIFICATION = "TS"
    PROMPT = "PROMPT"
    CASE_FILE = "CF"


@dataclass(frozen=True)
class DependencyNode:
    """Dependency graph node."""

    node_id: str
    node_type: DependencyNodeType
    title: str


class DependencyGraph:
    """Directed dependency graph."""

    def __init__(self) -> None:
        self._nodes: dict[str, DependencyNode] = {}
        self._edges: dict[str, set[str]] = {}

    def add_node(self, node: DependencyNode) -> None:
        """Add or replace a node definition."""
        self._nodes[node.node_id] = node
        self._edges.setdefault(node.node_id, set())

    def add_dependency(self, node_id: str, depends_on_id: str) -> None:
        """Declare that node_id depends on depends_on_id."""
        if node_id not in self._nodes:
            raise ValueError(f"unknown dependency node: {node_id}")
        if depends_on_id not in self._nodes:
            raise ValueError(f"unknown dependency target: {depends_on_id}")
        self._edges.setdefault(node_id, set()).add(depends_on_id)

    def dependencies_for(self, node_id: str) -> tuple[str, ...]:
        """Return direct dependencies."""
        return tuple(sorted(self._edges.get(node_id, set())))

    def dependents_of(self, node_id: str) -> tuple[str, ...]:
        """Return direct dependents."""
        return tuple(sorted(source for source, targets in self._edges.items() if node_id in targets))

    def transitive_dependencies_for(self, node_id: str) -> tuple[str, ...]:
        """Return transitive dependencies in deterministic order."""
        visited: set[str] = set()

        def visit(current: str) -> None:
            for dependency in sorted(self._edges.get(current, set())):
                if dependency not in visited:
                    visited.add(dependency)
                    visit(dependency)

        visit(node_id)
        return tuple(sorted(visited))

    def search(self, text: str) -> tuple[DependencyNode, ...]:
        """Search graph nodes by ID or title."""
        needle = text.lower()
        return tuple(
            node
            for node in sorted(self._nodes.values(), key=lambda item: item.node_id)
            if needle in node.node_id.lower() or needle in node.title.lower()
        )

