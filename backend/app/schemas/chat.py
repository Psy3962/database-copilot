"""Pydantic models for chat API request and response bodies."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class TextPart(BaseModel):
    type: Literal["text"] = "text"
    text: str


class QueryResultPayload(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    query_id: uuid.UUID = Field(alias="queryId")
    sql: str
    columns: list[str]
    rows: list[list[Any]]
    row_count: int = Field(alias="rowCount")
    truncated: bool
    elapsed_ms: int = Field(alias="elapsedMs")


class QueryResultPart(BaseModel):
    type: Literal["data-query-result"] = "data-query-result"
    id: str | None = None
    data: QueryResultPayload


class StatusPayload(BaseModel):
    stage: str
    message: str


class StatusPart(BaseModel):
    type: Literal["data-status"] = "data-status"
    data: StatusPayload


MessagePart = Annotated[TextPart | QueryResultPart, Field(discriminator="type")]


class UIMessage(BaseModel):
    id: str | None = None
    role: Literal["user", "assistant", "system"]
    parts: list[MessagePart]


class CreateThreadRequest(BaseModel):
    title: str | None = None


class ThreadResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: uuid.UUID
    title: str
    created_at: datetime = Field(serialization_alias="createdAt")
    updated_at: datetime = Field(serialization_alias="updatedAt")


class ThreadListResponse(BaseModel):
    threads: list[ThreadResponse]


class MessageHistoryResponse(BaseModel):
    messages: list[UIMessage]


class StreamRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    thread_id: uuid.UUID = Field(validation_alias="threadId")
    messages: list[UIMessage]


def thread_row_to_response(row: dict[str, Any]) -> ThreadResponse:
    return ThreadResponse(
        id=uuid.UUID(str(row["id"])),
        title=row["title"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )
