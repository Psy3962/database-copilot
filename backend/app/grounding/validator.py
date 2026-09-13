"""Fail-closed validation that answers reference an executed query."""

from __future__ import annotations

from dataclasses import dataclass

from app.assistant.deps import TurnRegistry
from app.assistant.outputs import DatabaseAnswer


@dataclass(frozen=True, slots=True)
class ValidationResult:
    ok: bool
    error: str | None = None


class QueryResultValidator:
    async def validate(
        self,
        answer: DatabaseAnswer,
        registry: TurnRegistry,
    ) -> ValidationResult:
        if not answer.answer.strip():
            return ValidationResult(ok=False, error="Answer text is empty.")

        if answer.cannot_answer:
            if answer.query_id is not None:
                return ValidationResult(
                    ok=False,
                    error="cannot_answer responses must not reference a query.",
                )
            return ValidationResult(ok=True)

        if answer.query_id is None:
            return ValidationResult(
                ok=False,
                error="A database answer must reference an executed query.",
            )

        if answer.query_id not in registry.results_by_query_id:
            return ValidationResult(
                ok=False,
                error="The answer references a query that was not executed this turn.",
            )

        return ValidationResult(ok=True)
