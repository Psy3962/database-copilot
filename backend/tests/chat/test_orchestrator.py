import json
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.assistant.outputs import DatabaseAnswer
from app.auth.dependencies import CurrentUser
from app.chat.orchestrator import run_turn
from app.database.target import QueryResult
from app.schemas.chat import TextPart, UIMessage


def _payload(event: str) -> dict[str, object]:
    return json.loads(event.removeprefix("data: ").strip())


@pytest.mark.anyio
async def test_revenue_question_returns_expected_answer_sql_and_rows() -> None:
    query_result = QueryResult(
        query_id=uuid.uuid4(),
        sql=(
            "SELECT product, SUM(net_amount) AS revenue "
            "FROM public.orders WHERE status <> 'cancelled' "
            "GROUP BY product ORDER BY revenue DESC"
        ),
        columns=["product", "revenue"],
        rows=[["Pro", 120], ["Basic", 80]],
        row_count=2,
        truncated=False,
        elapsed_ms=4,
    )
    expected_answer = (
        "Total revenue is 200. Pro contributes 120 and Basic contributes 80."
    )

    def fake_agent(_question: str, deps) -> DatabaseAnswer:
        deps.registry.register(query_result)
        return DatabaseAnswer(
            answer=expected_answer,
            query_id=query_result.query_id,
        )

    persist = AsyncMock()
    with (
        patch("app.chat.orchestrator.run_database_agent", fake_agent),
        patch("app.chat.streaming.append_database_turn", persist),
    ):
        events = [
            _payload(event)
            async for event in run_turn(
                client=MagicMock(),
                thread_id=uuid.uuid4(),
                user=CurrentUser(id=uuid.uuid4(), email="analyst@example.com"),
                user_message=UIMessage(
                    role="user",
                    parts=[TextPart(text="What is total revenue by product?")],
                ),
                thread_title="New chat",
            )
        ]

    streamed_text = "".join(
        str(event["delta"]) for event in events if event["type"] == "text-delta"
    ).strip()
    query_payload = next(
        event["data"] for event in events if event["type"] == "data-query-result"
    )

    assert streamed_text == expected_answer
    assert query_payload == {
        "queryId": str(query_result.query_id),
        "sql": query_result.sql,
        "columns": ["product", "revenue"],
        "rows": [["Pro", 120], ["Basic", 80]],
        "rowCount": 2,
        "truncated": False,
        "elapsedMs": 4,
    }
    persist.assert_awaited_once()
