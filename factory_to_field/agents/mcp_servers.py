"""The same tools, exposed as MCP servers (one per system family) over FastMCP.

    python -m factory_to_field.agents.mcp_servers kg        # stdio server for the knowledge graph
    python -m factory_to_field.agents.mcp_servers historian

The servers are read-only by construction: the only mutating tools are drafts.create_draft (writes a draft) and ot.write_setpoint (always refuses).
A server is built per call to `build(server)`, so tests can list and call tools in-process.
"""
from __future__ import annotations

import inspect
import sys
import typing
from datetime import UTC, datetime

try:  # mcp 2.x renamed FastMCP to MCPServer
    from mcp.server.mcpserver import MCPServer as FastMCP
except ImportError:  # mcp 1.x
    from mcp.server.fastmcp import FastMCP

from ..kg.store import KG
from . import tools as _t  # noqa: F401
from .core import DEFAULT_KG, DEFAULT_WORLD, REGISTRY, Ctx

SERVERS = sorted({t.server for t in REGISTRY.values()})


def build(server: str, as_of: str | None = None, kg: KG | None = None, src=None) -> FastMCP:
    mcp = FastMCP(f"ftf-{server}")
    kg = kg or KG(DEFAULT_KG, read_only=True)
    clock = datetime.fromisoformat((as_of or "2026-10-17T06:00:00+00:00").replace("Z", "+00:00"))
    ctx = Ctx(kg, DEFAULT_WORLD, clock if clock.tzinfo else clock.replace(tzinfo=UTC))
    for name, t in REGISTRY.items():
        if t.server != server:
            continue
        hints = typing.get_type_hints(t.fn)
        params = list(inspect.signature(t.fn).parameters.values())[1:]

        def make(fn=t.fn):
            def wrapper(**kw):
                r = fn(ctx, **kw)
                return {"data": r.data, "evidence": r.evidence, "untrusted_text": [f"<untrusted>{x}</untrusted>" for x in r.untrusted], "refused": r.refused}
            return wrapper
        w = make()
        w.__name__ = t.fn.__name__
        w.__signature__ = inspect.Signature(params)
        w.__annotations__ = {p.name: hints.get(p.name, str) for p in params}
        mcp.add_tool(w, name=t.fn.__name__, description=t.doc)
    return mcp


if __name__ == "__main__":
    which = sys.argv[1] if len(sys.argv) > 1 else "kg"
    if which not in SERVERS:
        raise SystemExit(f"server must be one of {SERVERS}")
    import os

    from .sources import make_source
    build(which, src=make_source(DEFAULT_WORLD, os.environ.get("FTF_SIM_URL"))).run()  # FTF_SIM_URL=http://127.0.0.1:8765 to use the simulators
