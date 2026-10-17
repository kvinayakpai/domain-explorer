"""Checks a report against the tool-call log: citations exist, quoted numbers came from tool output, no write slipped through."""
from __future__ import annotations

from .agent import Report
from .core import REGISTRY, Session
from .tools import STORE


def verify(rep: Report, s: Session) -> list[str]:
    problems: list[str] = []
    have, vals = s.evidence, s.flat_values()
    for f in rep.findings:
        if not f.evidence:
            problems.append(f"finding without evidence: {f.text[:60]}")
        for e in f.evidence:
            if e not in have:
                problems.append(f"cited evidence not in the tool log: {e}")
        for k, v in f.facts.items():
            if str(v) not in vals:
                problems.append(f"quoted value {k}={v} does not appear in any tool result")
    for did in rep.drafts:
        d = STORE.items.get(did)
        if d is None:
            problems.append(f"unknown draft {did}")
            continue
        if d.status != "draft":
            problems.append(f"{did} is {d.status}: agents may only leave drafts")
        if not d.evidence or any(e not in have for e in d.evidence):
            problems.append(f"{did} cites evidence that is not in the tool log")
    for c in s.log:
        t = REGISTRY[c.tool]
        if t.access == "ot_write" and not c.result.refused:
            problems.append(f"OT write was not refused: {c.tool}")
    return problems
