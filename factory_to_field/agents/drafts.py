"""Draft store: agents propose, named humans in the right role approve. Nothing leaves as 'sent' without that."""
from __future__ import annotations

import itertools
from dataclasses import dataclass, field
from datetime import datetime

APPROVER_ROLES = {
    "sap_pm.notification": "maintenance_planner",
    "sap_pm.stock_transfer": "materials_planner",
    "qms.warranty_claim": "quality_engineer",
    "qms.eightd": "quality_manager",
    "qms.customer_notice": "quality_manager",
    "rigs.request": "production_engineer",
    "ops.operator_request": "shift_supervisor",
}
_ids = itertools.count(1)


@dataclass
class Draft:
    id: str
    kind: str
    title: str
    payload: dict
    rationale: str
    evidence: list[str]
    approver_role: str
    created_at: datetime
    status: str = "draft"            # draft -> approved | rejected
    decided_by: str | None = None
    decided_role: str | None = None
    history: list[str] = field(default_factory=list)


class DraftStore:
    def __init__(self) -> None:
        self.items: dict[str, Draft] = {}

    def create(self, kind, title, payload, rationale, evidence, case_clock) -> Draft:
        d = Draft(f"DRAFT-{next(_ids):04d}", kind, title, payload, rationale, list(evidence), APPROVER_ROLES[kind], case_clock)
        d.history.append(f"created as draft; awaiting {d.approver_role}")
        self.items[d.id] = d
        return d

    def approve(self, draft_id: str, person: str, role: str) -> Draft:
        """Human path only: there is deliberately no agent tool that calls this."""
        d = self.items[draft_id]
        if not person.strip():
            raise PermissionError("approval needs a named person")
        if role != d.approver_role:
            raise PermissionError(f"{d.kind} must be approved by a {d.approver_role}, not a {role}")
        if not d.evidence:
            raise PermissionError("a draft without evidence cannot be approved")
        d.status, d.decided_by, d.decided_role = "approved", person, role
        d.history.append(f"approved by {person} ({role})")
        return d

    def reject(self, draft_id: str, person: str, role: str, reason: str) -> Draft:
        d = self.items[draft_id]
        d.status, d.decided_by, d.decided_role = "rejected", person, role
        d.history.append(f"rejected by {person}: {reason}")
        return d

    def pending(self) -> list[Draft]:
        return [d for d in self.items.values() if d.status == "draft"]
