"""Approve, reject and release drafts with a signed identity, and record every step in the audit log.

The draft store already refuses an approval from the wrong role. Before, the console passed a typed name
and role; here the name and roles come from a token the identity provider signed, so nobody can approve as
someone else, and the plant-system simulators check the same token again before they accept the write.
"""
from __future__ import annotations

from collections.abc import Callable
from typing import Any

from ..agents.drafts import Draft, DraftStore
from ..agents.release import TARGETS
from ..agents.sources import HttpSource
from .audit import AuditLog

Verify = Callable[[str], dict[str, Any]]


def _who(token: str, verify: Verify, audit: AuditLog, action: str, draft_id: str) -> dict[str, Any]:
    try:
        return verify(token)
    except PermissionError as e:
        audit.append("unknown", None, f"{action}_refused", draft_id, {"reason": str(e)})
        raise


def approve(store: DraftStore, draft_id: str, token: str, verify: Verify, audit: AuditLog) -> Draft:
    claims = _who(token, verify, audit, "approve", draft_id)
    d = store.items[draft_id]
    roles = claims.get("roles", [])
    if d.approver_role not in roles:
        audit.append(claims["name"], ",".join(roles), "approve_refused", draft_id,
                     {"needs": d.approver_role, "kind": d.kind, "sub": claims.get("sub")})
        raise PermissionError(f"{d.kind} must be approved by a {d.approver_role}; {claims['name']} holds {', '.join(roles) or 'no roles'}")
    store.approve(draft_id, claims["name"], d.approver_role)
    audit.append(claims["name"], d.approver_role, "approve", draft_id,
                 {"kind": d.kind, "title": d.title, "evidence": d.evidence, "sub": claims.get("sub"), "token_id": claims.get("jti")})
    return d


def reject(store: DraftStore, draft_id: str, token: str, reason: str, verify: Verify, audit: AuditLog) -> Draft:
    claims = _who(token, verify, audit, "reject", draft_id)
    d = store.items[draft_id]
    if d.approver_role not in claims.get("roles", []):
        raise PermissionError(f"only a {d.approver_role} can reject {d.kind}")
    store.reject(draft_id, claims["name"], d.approver_role, reason)
    audit.append(claims["name"], d.approver_role, "reject", draft_id, {"reason": reason, "sub": claims.get("sub")})
    return d


def release(store: DraftStore, draft_id: str, system: HttpSource, token: str, verify: Verify, audit: AuditLog) -> dict[str, Any]:
    """Post an approved draft to its target system with the releasing person's own token."""
    claims = _who(token, verify, audit, "release", draft_id)
    d = store.items[draft_id]
    if d.status != "approved" or not d.decided_by:
        audit.append(claims["name"], None, "release_refused", draft_id, {"status": d.status})
        raise PermissionError(f"{draft_id} is {d.status}: only approved drafts can be released")
    if d.approver_role not in claims.get("roles", []):
        audit.append(claims["name"], None, "release_refused", draft_id, {"needs": d.approver_role})
        raise PermissionError(f"releasing {d.kind} needs a {d.approver_role}")
    rec = system.post(TARGETS[d.kind], {"title": d.title, **d.payload, "rationale": d.rationale, "evidence": d.evidence},
                      token=token, headers={"X-Draft-Id": d.id})
    d.status = "released"
    d.history.append(f"released to {rec['system']} as {rec['id']} by {claims['name']}")
    audit.append(claims["name"], d.approver_role, "release", draft_id, {"record": rec["id"], "system": rec["system"], "sub": claims.get("sub")})
    return rec
