"""Runtime dependencies for the database agent."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from uuid import UUID

from app.database.target import QueryResult

StatusCallback = Callable[[str, str], None]


@dataclass
class TurnRegistry:
    """Tracks query results produced during a turn."""

    results_by_query_id: dict[UUID, QueryResult] = field(default_factory=dict)

    def register(self, result: QueryResult) -> None:
        self.results_by_query_id[result.query_id] = result


@dataclass
class DatabaseAgentDeps:
    registry: TurnRegistry
    thread_id: UUID
    user_id: UUID
    on_status: StatusCallback | None = None

    def emit_status(self, stage: str, message: str) -> None:
        if self.on_status is not None:
            self.on_status(stage, message)
