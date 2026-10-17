"""JSON schemas for registry tools, derived from their signatures (used by the LLM planner and the MCP servers)."""
from __future__ import annotations

import inspect
import typing

from .core import REGISTRY, Tool


def _js(tp) -> dict:
    origin = typing.get_origin(tp)
    if origin in (typing.Union, getattr(__import__("types"), "UnionType", None)):
        args = [a for a in typing.get_args(tp) if a is not type(None)]
        return _js(args[0])
    if tp is str:
        return {"type": "string"}
    if tp is int:
        return {"type": "integer"}
    if tp is float:
        return {"type": "number"}
    if tp is bool:
        return {"type": "boolean"}
    if tp is dict or origin is dict:
        return {"type": "object"}
    if origin is list:
        a = typing.get_args(tp)
        return {"type": "array", "items": _js(a[0]) if a else {}}
    return {}


def input_schema(t: Tool) -> dict:
    sig = inspect.signature(t.fn)
    hints = typing.get_type_hints(t.fn)
    props, req = {}, []
    for name, p in list(sig.parameters.items())[1:]:  # first is ctx
        props[name] = _js(hints.get(name, str))
        if p.default is inspect._empty:
            req.append(name)
    return {"type": "object", "properties": props, "required": req}


def anthropic_tools(names: list[str] | None = None) -> list[dict]:
    out = []
    for n, t in REGISTRY.items():
        if names is not None and n not in names:
            continue
        out.append({"name": n.replace(".", "__"), "description": t.doc, "input_schema": input_schema(t)})
    return out
