"""The tools as an MCP server, and the client-side conversions (A2). YOURS, except the __main__ block.

MCP (Model Context Protocol) is how agents discover and call tools that live in another process. Here the
server wraps the same functions as tools.py, and mcp_bridge.MCPToolBox connects your agent to it:

    server = build_mcp_server(task_dir)          # yours
    tools = MCPToolBox(server)                   # provided; uses mcp_tools_to_openai + call_result_to_text
    run_agent(task_dir, llm_fn, tools=tools)     # the agent cannot tell the difference

`python -m pa4.mcp_server TASK_DIR` serves one task over stdio, so any MCP client can use your tools. (The Section B
team calls the tools in-process and does not need MCP.)
"""
from __future__ import annotations

import sys
from pathlib import Path

from mcp import types
from mcp.server.fastmcp import FastMCP

from . import tools as T


def build_mcp_server(task_dir) -> FastMCP:
    """Return a FastMCP server named "pa4-tools" exposing the six tools of tools.py for task_dir.

    Each MCP tool has the same name, the same parameter names, types and defaults (minus task_dir) and the
    same description as its entry in tools.TOOL_SPECS, and calls the tools.py function. A ToolError must
    reach the client as an MCP tool error (CallToolResult.isError is True), not as a normal result.
    """
    raise NotImplementedError("TODO A2: build_mcp_server")


def mcp_tools_to_openai(mcp_tools: list[types.Tool]) -> list[dict]:
    """Convert the result of an MCP tools/list into OpenAI function specs.

    One spec per tool, in order: {"type": "function", "function": {"name": tool.name, "description":
    tool.description or "", "parameters": tool.inputSchema}}. Copy the schema; do not mutate the input.
    """
    raise NotImplementedError("TODO A2: mcp_tools_to_openai")


def call_result_to_text(result: types.CallToolResult) -> str:
    """Turn an MCP CallToolResult into the string the model sees.

    Join the .text of every TextContent item with "\\n"; any other content item becomes
    f"[{item.type} content omitted]". If result.isError is true, prefix the whole thing with "ERROR: " so the
    agent loop treats it like any other tool error.
    """
    raise NotImplementedError("TODO A2: call_result_to_text")


if __name__ == "__main__":  # PROVIDED: serve one task over stdio, for any MCP client
    build_mcp_server(sys.argv[1]).run()
