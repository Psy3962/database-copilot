"""Schema inspection and guarded read-only access to the target database."""

from __future__ import annotations

import json
import re
import time
import uuid
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from app.config import settings

_engine: Engine | None = None
_SAFE_START_RE = re.compile(r"^\s*(?:select|with|explain|show)\b", re.IGNORECASE)


@dataclass(frozen=True, slots=True)
class QueryResult:
    query_id: uuid.UUID
    sql: str
    columns: list[str]
    rows: list[list[Any]]
    row_count: int
    truncated: bool
    elapsed_ms: int


def get_target_engine() -> Engine:
    global _engine
    if _engine is None:
        _engine = create_engine(
            settings.sqlalchemy_target_database_url,
            pool_pre_ping=True,
        )
    return _engine


def _qualified_name(schema: str, table: str) -> str:
    quoted_schema = schema.replace('"', '""')
    quoted_table = table.replace('"', '""')
    return f'"{quoted_schema}"."{quoted_table}"'


def inspect_database_schema() -> str:
    """Return a compact schema description suitable for an LLM prompt."""
    schemas = settings.target_schemas
    with get_target_engine().connect() as connection:
        columns = connection.execute(
            text(
                """
                SELECT table_schema, table_name, column_name, data_type,
                       is_nullable, column_default, ordinal_position
                FROM information_schema.columns
                WHERE table_schema = ANY(:schemas)
                ORDER BY table_schema, table_name, ordinal_position
                """
            ),
            {"schemas": schemas},
        ).mappings()
        foreign_keys = connection.execute(
            text(
                """
                SELECT tc.table_schema, tc.table_name, kcu.column_name,
                       ccu.table_schema AS foreign_schema,
                       ccu.table_name AS foreign_table,
                       ccu.column_name AS foreign_column
                FROM information_schema.table_constraints tc
                JOIN information_schema.key_column_usage kcu
                  ON tc.constraint_name = kcu.constraint_name
                 AND tc.table_schema = kcu.table_schema
                JOIN information_schema.constraint_column_usage ccu
                  ON ccu.constraint_name = tc.constraint_name
                 AND ccu.table_schema = tc.table_schema
                WHERE tc.constraint_type = 'FOREIGN KEY'
                  AND tc.table_schema = ANY(:schemas)
                ORDER BY tc.table_schema, tc.table_name, kcu.ordinal_position
                """
            ),
            {"schemas": schemas},
        ).mappings()

        tables: dict[tuple[str, str], list[str]] = {}
        for column in columns:
            nullable = "" if column["is_nullable"] == "YES" else " not null"
            default = (
                f" default {column['column_default']}"
                if column["column_default"] is not None
                else ""
            )
            tables.setdefault(
                (column["table_schema"], column["table_name"]), []
            ).append(
                f"{column['column_name']} {column['data_type']}{nullable}{default}"
            )

        relationships: dict[tuple[str, str], list[str]] = {}
        for key in foreign_keys:
            relationships.setdefault(
                (key["table_schema"], key["table_name"]), []
            ).append(
                f"{key['column_name']} -> "
                f"{key['foreign_schema']}.{key['foreign_table']}.{key['foreign_column']}"
            )

    sections = []
    for (schema, table), table_columns in tables.items():
        lines = [f"TABLE {_qualified_name(schema, table)}", *table_columns]
        lines.extend(f"FK {relationship}" for relationship in relationships.get((schema, table), []))
        sections.append("\n".join(lines))

    if not sections:
        return "No tables were found in the configured schemas."
    return "\n\n".join(sections)


def load_business_description() -> str:
    path = settings.database_description_path
    if not path.exists():
        return "No additional business description has been provided."
    content = path.read_text(encoding="utf-8").strip()
    return content or "No additional business description has been provided."


def _validate_sql(sql: str) -> str:
    statement = sql.strip()
    if not statement:
        raise ValueError("SQL must not be empty.")
    if not _SAFE_START_RE.match(statement):
        raise ValueError("Only SELECT, WITH, EXPLAIN, and SHOW statements are allowed.")
    without_trailing = statement.rstrip(";").rstrip()
    if ";" in without_trailing:
        raise ValueError("Only one SQL statement may be executed at a time.")
    return without_trailing


def _json_value(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, (date, datetime, Decimal, uuid.UUID)):
        return str(value)
    if isinstance(value, (dict, list)):
        return json.loads(json.dumps(value, default=str))
    return str(value)


def execute_readonly_query(sql: str) -> QueryResult:
    """Execute one statement inside a database-enforced read-only transaction."""
    statement = _validate_sql(sql)
    started = time.perf_counter()
    with get_target_engine().connect() as connection:
        transaction = connection.begin()
        try:
            connection.execute(text("SET TRANSACTION READ ONLY"))
            connection.execute(
                text("SELECT set_config('statement_timeout', :timeout, true)"),
                {"timeout": f"{settings.query_timeout_ms}ms"},
            )
            cursor = connection.execute(text(statement))
            columns = list(cursor.keys())
            raw_rows = cursor.fetchmany(settings.query_max_rows + 1) if cursor.returns_rows else []
        finally:
            transaction.rollback()

    truncated = len(raw_rows) > settings.query_max_rows
    rows = [
        [_json_value(value) for value in row]
        for row in raw_rows[: settings.query_max_rows]
    ]
    return QueryResult(
        query_id=uuid.uuid4(),
        sql=statement,
        columns=columns,
        rows=rows,
        row_count=len(rows),
        truncated=truncated,
        elapsed_ms=round((time.perf_counter() - started) * 1000),
    )
