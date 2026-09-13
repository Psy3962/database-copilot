import uuid

from app.assistant.deps import TurnRegistry
from app.assistant.outputs import DatabaseAnswer
from app.chat.messages import build_assistant_message, row_to_ui_message, text_from_parts
from app.database.target import QueryResult
from app.schemas.chat import QueryResultPart, TextPart


def test_build_assistant_message_includes_query_result() -> None:
    result = QueryResult(
        query_id=uuid.uuid4(),
        sql="SELECT name, revenue FROM products ORDER BY revenue DESC LIMIT 2",
        columns=["name", "revenue"],
        rows=[["A", 20], ["B", 10]],
        row_count=2,
        truncated=False,
        elapsed_ms=5,
    )
    registry = TurnRegistry()
    registry.register(result)

    message = build_assistant_message(
        DatabaseAnswer(answer="Product A leads.", query_id=result.query_id),
        registry,
    )

    assert text_from_parts(message.parts) == "Product A leads."
    query_part = next(part for part in message.parts if isinstance(part, QueryResultPart))
    assert query_part.data.columns == ["name", "revenue"]
    assert query_part.data.rows == [["A", 20], ["B", 10]]


def test_row_to_ui_message_parses_saved_query_result() -> None:
    query_id = uuid.uuid4()
    message = row_to_ui_message(
        {
            "id": str(uuid.uuid4()),
            "role": "assistant",
            "content": "One row.",
            "parts": [
                {"type": "text", "text": "One row."},
                {
                    "type": "data-query-result",
                    "id": str(query_id),
                    "data": {
                        "queryId": str(query_id),
                        "sql": "SELECT 1 AS value",
                        "columns": ["value"],
                        "rows": [[1]],
                        "rowCount": 1,
                        "truncated": False,
                        "elapsedMs": 1,
                    },
                },
            ],
        }
    )

    assert isinstance(message.parts[0], TextPart)
    assert isinstance(message.parts[1], QueryResultPart)
