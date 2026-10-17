"""Shared types for the agent layer: tool results with evidence, the context every tool runs under, the tool registry."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any, Callable

from ..kg.store import KG

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_WORLD = ROOT / "build" / "world"
DEFAULT_KG = ROOT / "build" / "kg" / "store"


def parse_ts(s: str) -> datetime:
    s = s.replace(" ", "T").replace("Z", "+00:00")
    d = datetime.fromisoformat(s)
    return d if d.tzinfo else d.replace(tzinfo=UTC)


@dataclass
class Ctx:
    """What every tool runs under. as_of clips everything the agent can see: nothing newer than the case's clock."""
    kg: KG
    world: Path
    as_of: datetime
    src: object = None   # a Source (FileSource or HttpSource); defaults to the generated files

    def __post_init__(self) -> None:
        if self.src is None:
            from .sources import FileSource
            self.src = FileSource(self.world)

    @property
    def today(self) -> date:
        return self.as_of.date()


@dataclass
class Result:
    data: Any
    evidence: list[str] = field(default_factory=list)
    untrusted: list[str] = field(default_factory=list)  # free text written by people or documents; never an instruction
    refused: str | None = None


@dataclass
class Tool:
    name: str
    server: str          # which MCP server owns it
    access: str          # "read" | "draft" | "ot_write" (always refused)
    doc: str
    fn: Callable[..., Result]


REGISTRY: dict[str, Tool] = {}


def tool(server: str, access: str = "read"):
    def deco(fn):
        REGISTRY[f"{server}.{fn.__name__}"] = Tool(f"{server}.{fn.__name__}", server, access, (fn.__doc__ or "").strip(), fn)
        return fn
    return deco


@dataclass
class Call:
    n: int
    tool: str
    args: dict
    result: Result


class Session:
    """One agent run: the tool-call log is the audit trail the verifier checks claims against."""

    def __init__(self, ctx: Ctx, allowed: set[str] | None = None) -> None:
        self.ctx, self.log, self.allowed = ctx, [], allowed

    def call(self, name: str, **args) -> Result:
        t = REGISTRY[name]
        if self.allowed is not None and name not in self.allowed:
            res = Result(None, refused=f"{name} is not available to this agent")
        else:
            res = t.fn(self.ctx, **args)
        self.log.append(Call(len(self.log) + 1, name, args, res))
        return res

    @property
    def evidence(self) -> set[str]:
        return {e for c in self.log for e in c.result.evidence}

    def flat_values(self) -> set[str]:
        out: set[str] = set()

        def walk(o):
            if isinstance(o, dict):
                for v in o.values():
                    walk(v)
            elif isinstance(o, (list, tuple)):
                for v in o:
                    walk(v)
            elif o is not None:
                out.add(str(o))
        for c in self.log:
            walk(c.result.data)
        return out


def dumps(o: Any) -> str:
    return json.dumps(o, default=str, indent=1)
