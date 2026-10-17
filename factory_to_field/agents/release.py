"""The human path: an approved draft is released to the target system's API. Agents never import or call this.

Only a draft that a named person in the right role has approved can be released, and the simulator checks the headers again.
"""
from __future__ import annotations

from .drafts import Draft, DraftStore
from .sources import HttpSource

TARGETS = {
    "sap_pm.notification": "/sap/opu/odata/sap/API_MAINTNOTIFICATION/MaintenanceNotification",
    "sap_pm.stock_transfer": "/sap/opu/odata/sap/API_MATERIAL_DOCUMENT_SRV/A_MaterialDocumentHeader",
    "qms.warranty_claim": "/qms/api/claims",
    "qms.eightd": "/qms/api/eightd",
    "qms.customer_notice": "/qms/api/customer-notices",
    "rigs.request": "/prod/api/rigs/requests",
    "ops.operator_request": "/ops/api/operator-requests",
}


def release(store: DraftStore, draft_id: str, system: HttpSource, release_token: str = "release") -> dict:
    d: Draft = store.items[draft_id]
    if d.status != "approved" or not d.decided_by:
        raise PermissionError(f"{draft_id} is {d.status}: only approved drafts can be released")
    rec = system.post(TARGETS[d.kind], {"title": d.title, **d.payload, "rationale": d.rationale, "evidence": d.evidence}, token=release_token,
                      headers={"X-Approved-By": f"{d.decided_by} ({d.decided_role})", "X-Draft-Id": d.id})
    d.status = "released"
    d.history.append(f"released to {rec['system']} as {rec['id']}")
    return rec
