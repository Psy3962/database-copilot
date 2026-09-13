"""Bounded tools for schema inspection and read-only SQL execution."""

from __future__ import annotations

import asyncio
import functools
import json
import time

from pydantic_ai import RunContext

from app.assistant.deps import DatabaseAgentDeps
from app.assistant.progress import report_progress
from app.assistant.status import emit_tool_start
from app.database.target import (
    execute_readonly_query,
    inspect_database_schema,
    load_business_description,
)


async def _run_tool(deps: DatabaseAgentDeps, name: str, detail: str, fn, /, *args):
    emit_tool_start(deps, name, detail)
    started = time.perf_counter()
    result = await asyncio.to_thread(functools.partial(fn, *args))
    report_progress(f"tool {name} done in {time.perf_counter() - started:.2f}s")
    return result


async def get_database_context(ctx: RunContext[DatabaseAgentDeps]) -> str:
    """Inspect tables, columns, relationships, and the human business description."""
    schema, description = await asyncio.gather(
        _run_tool(ctx.deps, "inspect_schema", "configured schemas", inspect_database_schema),
        _run_tool(
            ctx.deps,
            "read_description",
            "business terminology",
            load_business_description,
        ),
    )
    return f"BUSINESS DESCRIPTION\n{description}\n\nDATABASE SCHEMA\n{schema}"


async def run_readonly_query(ctx: RunContext[DatabaseAgentDeps], sql: str) -> str:
    """Run one read-only PostgreSQL query. Data changes are blocked by the database transaction."""
    try:
        result = await _run_tool(
            ctx.deps,
            "run_readonly_query",
            "executing generated SQL",
            execute_readonly_query,
            sql,
        )
    except Exception as exc:
        return f"Query failed: {exc}"

    ctx.deps.registry.register(result)
    return json.dumps(
        {
            "query_id": str(result.query_id),
            "sql": result.sql,
            "columns": result.columns,
            "rows": result.rows,
            "row_count": result.row_count,
            "truncated": result.truncated,
            "elapsed_ms": result.elapsed_ms,
        },
        default=str,
        separators=(",", ":"),
    )
