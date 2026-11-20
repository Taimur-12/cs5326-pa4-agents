"""PROVIDED. A tool box backed by a live MCP session, so the synchronous agent loop can use MCP tools.

The MCP client is async; the agent loop is not. MCPToolBox runs one client session on a private event loop in
a background thread and forwards each call to it. It uses YOUR conversions from mcp_server.py:
mcp_tools_to_openai (for .specs) and call_result_to_text (for .call).

    with MCPToolBox(build_mcp_server(task_dir)) as tools:
        result = run_agent(task_dir, llm_fn, tools=tools)

The server runs in memory (no subprocess); the session speaks the real MCP protocol, so discovery, argument
validation and error results behave exactly as they would over stdio.
"""
from __future__ import annotations

import asyncio
import concurrent.futures
import threading

from mcp.shared.memory import create_connected_server_and_client_session

from .mcp_server import call_result_to_text, mcp_tools_to_openai


class MCPToolBox:
    def __init__(self, server, timeout: float = 300):
        self.timeout = timeout
        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(target=self._loop.run_forever, daemon=True)
        self._thread.start()
        self._ready: concurrent.futures.Future = concurrent.futures.Future()
        self._queue: asyncio.Queue | None = None
        self._task = asyncio.run_coroutine_threadsafe(self._serve(server), self._loop)
        self.mcp_tools = self._ready.result(timeout=60)
        self.specs = mcp_tools_to_openai(self.mcp_tools)

    async def _serve(self, server) -> None:
        self._queue = asyncio.Queue()
        try:
            async with create_connected_server_and_client_session(server) as session:
                listed = await session.list_tools()
                self._ready.set_result(listed.tools)
                while (item := await self._queue.get()) is not None:
                    name, args, fut = item
                    try:
                        fut.set_result(await session.call_tool(name, args))
                    except Exception as e:  # noqa: BLE001
                        fut.set_exception(e)
        except Exception as e:  # noqa: BLE001
            if not self._ready.done():
                self._ready.set_exception(e)
            raise

    @property
    def names(self) -> list[str]:
        return [s["function"]["name"] for s in self.specs]

    def call(self, name: str, args: dict) -> str:
        fut: concurrent.futures.Future = concurrent.futures.Future()
        self._loop.call_soon_threadsafe(self._queue.put_nowait, (name, args, fut))
        return call_result_to_text(fut.result(timeout=self.timeout))

    def close(self) -> None:
        if self._loop.is_running():
            self._loop.call_soon_threadsafe(self._queue.put_nowait, None)
            try:
                self._task.result(timeout=10)
            except Exception:  # noqa: BLE001
                pass
            self._loop.call_soon_threadsafe(self._loop.stop)
            self._thread.join(timeout=10)

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()
