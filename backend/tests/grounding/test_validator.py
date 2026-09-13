import asyncio
import uuid

from app.assistant.deps import TurnRegistry
from app.assistant.outputs import DatabaseAnswer
from app.database.target import QueryResult
from app.grounding.validator import QueryResultValidator


def _result() -> QueryResult:
    return QueryResult(
        query_id=uuid.uuid4(),
        sql="SELECT count(*) AS customer_count FROM customers",
        columns=["customer_count"],
        rows=[[42]],
        row_count=1,
        truncated=False,
        elapsed_ms=3,
    )


def test_validator_accepts_registered_query_result() -> None:
    result = _result()
    registry = TurnRegistry()
    registry.register(result)
    answer = DatabaseAnswer(answer="There are 42 customers.", query_id=result.query_id)

    validation = asyncio.run(QueryResultValidator().validate(answer, registry))

    assert validation.ok


def test_validator_rejects_unexecuted_query_id() -> None:
    answer = DatabaseAnswer(answer="There are 42 customers.", query_id=uuid.uuid4())

    validation = asyncio.run(QueryResultValidator().validate(answer, TurnRegistry()))

    assert not validation.ok


def test_validator_accepts_explicit_cannot_answer() -> None:
    answer = DatabaseAnswer(
        answer="The schema does not contain revenue.",
        cannot_answer=True,
    )

    validation = asyncio.run(QueryResultValidator().validate(answer, TurnRegistry()))

    assert validation.ok
