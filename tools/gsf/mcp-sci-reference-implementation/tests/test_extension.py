"""End-to-end over real MCP messages (in-memory transport, protocol 2026-07-28)."""
import anyio
import pytest
from mcp import ClientSession
from mcp.shared.memory import create_client_server_memory_streams

from mcp_sci.extension import EXTENSION_ID
from mcp_sci.server import mcp

pytestmark = pytest.mark.anyio


@pytest.fixture
def anyio_backend():
    return "asyncio"


async def _with_session(extensions, fn):
    async with create_client_server_memory_streams() as ((cr, cw), (sr, sw)):
        async with anyio.create_task_group() as tg:
            tg.start_soon(mcp._lowlevel_server.run, sr, sw, mcp._lowlevel_server.create_initialization_options())
            async with ClientSession(cr, cw, extensions=extensions) as s:
                await s.discover()
                await fn(s)
            tg.cancel_scope.cancel()


async def test_server_advertises_extension():
    async def check(s):
        assert s.protocol_version == "2026-07-28"
        assert EXTENSION_ID in s.discover_result.capabilities.extensions
    await _with_session({EXTENSION_ID: {}}, check)


async def test_tools_list_carries_disclosure_and_is_cacheable():
    async def check(s):
        res = await s.list_tools()
        d = res.tools[0].meta[EXTENSION_ID]
        assert d["methodology"]["id"] == "SCI-for-AI"
        assert d["functionalUnit"]["name"] == "request"
        assert d["boundary"]["persona"] == "consumer"
        assert "includes" in d["boundary"] and "excludes" in d["boundary"]
        assert d["typical"]["sci"]["unit"] == "gCO2e/request"
        assert res.ttl_ms > 0 and res.cache_scope == "public"
    await _with_session({EXTENSION_ID: {}}, check)


async def test_call_returns_attribution_when_opted_in():
    async def check(s):
        res = await s.call_tool("summarize", {"text": "one two three four five six", "max_words": 2})
        a = res.meta[EXTENSION_ID]
        e = a["emissions"]
        assert e["total"] == pytest.approx(e["operational"] + e["embodied"])
        assert a["sci"]["value"] == pytest.approx(e["total"] / a["functionalUnit"]["quantity"])
        assert a["energy"]["basis"] == "estimated"
        assert a["carbonIntensity"]["region"] == "europe-north1"
        assert a["details"]["outcome"] == "completed"
        # business content is untouched
        assert res.content[0].text.startswith("one two")
    await _with_session({EXTENSION_ID: {}}, check)


async def test_plain_client_gets_no_attribution():
    async def check(s):
        res = await s.call_tool("summarize", {"text": "one two three", "max_words": 2})
        assert EXTENSION_ID not in (res.meta or {})
        assert res.content[0].text.startswith("one two")
    await _with_session(None, check)
