"""Gateway from the API to the calculator MCP server.

Each call opens a short stdio session with the server. If MCP is unavailable for any reason the
gateway runs the same pure function in process, so a result is always returned.
"""
from __future__ import annotations

import asyncio
import json
import logging
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Awaitable, Callable

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from mcp_server import calculator

log = logging.getLogger(__name__)

BACKEND_ROOT = Path(__file__).resolve().parents[2]
LOCAL_TOOLS: dict[str, Callable[..., dict]] = {
    "calculate_coverage_need": calculator.coverage_need,
    "project_need_over_time": calculator.project_need,
    "compare_term_vs_permanent": calculator.compare_term_vs_permanent,
    "full_assessment": calculator.full_assessment,
    "what_if": calculator.what_if,
}


@dataclass(frozen=True)
class ToolSpec:
    name: str
    description: str
    input_schema: dict[str, Any]


class CalculatorGateway:
    def __init__(self, server_module: str = "mcp_server.server", timeout: float = 10.0):
        self._server = StdioServerParameters(
            command=sys.executable, args=["-m", server_module], cwd=str(BACKEND_ROOT)
        )
        self._timeout = timeout
        self._tools: list[ToolSpec] | None = None

    def tools(self) -> list[ToolSpec]:
        """Tool definitions as published by the MCP server (cached after the first call)."""
        if self._tools is None:
            listed = self._run(lambda session: session.list_tools())
            self._tools = [ToolSpec(t.name, t.description or "", t.inputSchema) for t in listed.tools]
        return self._tools

    def call(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        """Run a calculator tool. Validation problems come back as `{"error", "field"}`."""
        if name not in LOCAL_TOOLS:
            raise KeyError(f"Unknown calculator tool: {name}")
        try:
            return self._run(lambda session: self._call_tool(session, name, arguments))
        except Exception as exc:
            log.warning("MCP call %s failed (%s); using in-process calculator", name, exc)
            return LOCAL_TOOLS[name](**arguments)

    def _run(self, action: Callable[[ClientSession], Awaitable[Any]]) -> Any:
        async def session_scope() -> Any:
            async with stdio_client(self._server) as (read, write), ClientSession(read, write) as session:
                await session.initialize()
                return await action(session)

        return asyncio.run(asyncio.wait_for(session_scope(), self._timeout))

    @staticmethod
    async def _call_tool(session: ClientSession, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        result = await session.call_tool(name, arguments)
        if result.isError:
            raise RuntimeError(result.content[0].text if result.content else "tool error")
        if result.structuredContent is not None:
            return result.structuredContent
        return json.loads(result.content[0].text)
