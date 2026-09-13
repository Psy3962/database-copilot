import json
import uuid
from unittest.mock import MagicMock, patch

import pytest

from app.assistant.deps import DatabaseAgentDeps, TurnRegistry
from app.assistant.tools import run_readonly_query
from app.database.target import QueryResult


@pytest.mark.anyio
async def test_run_readonly_query_registers_result() -> None:
    registry = TurnRegistry()
    deps = DatabaseAgentDeps(
        registry=registry,
        thread_id=uuid.uuid4(),
        user_id=uuid.uuid4(),
    )
    ctx = MagicMock(deps=deps)
    result = QueryResult(
        query_id=uuid.uuid4(),
        sql="SELECT count(*) AS total FROM orders",
        columns=["total"],
        rows=[[12]],
        row_count=1,
        truncated=False,
        elapsed_ms=2,
    )

    with patch("app.assistant.tools.execute_readonly_query", return_value=result):
        payload = json.loads(
            await run_readonly_query(ctx, "SELECT count(*) AS total FROM orders")
        )

    assert payload["query_id"] == str(result.query_id)
    assert registry.results_by_query_id[result.query_id] == result


@pytest.mark.anyio
async def test_run_readonly_query_returns_safe_error_to_agent() -> None:
    deps = DatabaseAgentDeps(
        registry=TurnRegistry(),
        thread_id=uuid.uuid4(),
        user_id=uuid.uuid4(),
    )
    ctx = MagicMock(deps=deps)

    with patch(
        "app.assistant.tools.execute_readonly_query",
        side_effect=ValueError("Only SELECT is allowed."),
    ):
        payload = await run_readonly_query(ctx, "DELETE FROM orders")

    assert payload == "Query failed: Only SELECT is allowed."
    assert not deps.registry.results_by_query_id
