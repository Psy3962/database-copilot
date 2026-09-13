"""Structured output types for the database agent."""

from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, Field


class DatabaseAnswer(BaseModel):
    answer: str = Field(description="Plain-English explanation of the query result")
    query_id: UUID | None = Field(
        default=None,
        description="ID returned by run_readonly_query, if a query was executed",
    )
    cannot_answer: bool = Field(
        default=False,
        description="True when the schema or available data cannot answer the question",
    )
