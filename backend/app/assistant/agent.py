"""PydanticAI database agent definition."""

from __future__ import annotations

from pathlib import Path

from pydantic_ai import Agent, UsageLimits
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider

from app.assistant.deps import DatabaseAgentDeps
from app.assistant.outputs import DatabaseAnswer
from app.assistant.status import emit_agent_done, emit_agent_start
from app.assistant.tools import (
    get_database_context,
    run_readonly_query,
)
from app.config import settings

_INSTRUCTIONS_PATH = Path(__file__).with_name("instructions.md")
INSTRUCTIONS = _INSTRUCTIONS_PATH.read_text(encoding="utf-8")

_database_agent: Agent[DatabaseAgentDeps, DatabaseAnswer] | None = None


def get_database_agent() -> Agent[DatabaseAgentDeps, DatabaseAnswer]:
    global _database_agent
    if _database_agent is None:
        model = OpenAIChatModel(
            settings.openai_chat_model,
            provider=OpenAIProvider(api_key=settings.openai_api_key),
        )
        _database_agent = Agent(
            model,
            deps_type=DatabaseAgentDeps,
            output_type=DatabaseAnswer,
            instructions=INSTRUCTIONS,
            tools=[get_database_context, run_readonly_query],
        )
    return _database_agent


def run_database_agent(query: str, deps: DatabaseAgentDeps) -> DatabaseAnswer:
    emit_agent_start(
        deps,
        model=settings.openai_chat_model,
        request_limit=settings.openai_agent_request_limit,
    )
    result = get_database_agent().run_sync(
        query,
        deps=deps,
        usage_limits=UsageLimits(request_limit=settings.openai_agent_request_limit),
    )
    usage = result.usage
    emit_agent_done(
        deps,
        requests=usage.requests or 0,
        tool_calls=usage.tool_calls or 0,
        input_tokens=usage.input_tokens,
        output_tokens=usage.output_tokens,
    )
    return result.output
