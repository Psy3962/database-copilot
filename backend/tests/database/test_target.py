import pytest

from app.database.target import _validate_sql


@pytest.mark.parametrize(
    "sql",
    [
        "SELECT id FROM public.customers",
        "WITH totals AS (SELECT count(*) AS n FROM orders) SELECT n FROM totals",
        "EXPLAIN SELECT id FROM customers",
        "SHOW timezone",
    ],
)
def test_validate_sql_accepts_single_read_statement(sql: str) -> None:
    assert _validate_sql(sql) == sql


@pytest.mark.parametrize(
    "sql",
    [
        "DELETE FROM customers",
        "UPDATE customers SET email = 'x'",
        "DROP TABLE customers",
        "SELECT 1; SELECT 2",
        "",
    ],
)
def test_validate_sql_rejects_unsafe_statement(sql: str) -> None:
    with pytest.raises(ValueError):
        _validate_sql(sql)
