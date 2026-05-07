"""Demo FHIR R4 REST client.

Emulates a tiny slice of the FHIR R4 RESTful API (`HL7 FHIR 4.0.1
<https://hl7.org/fhir/R4/http.html>`_) without making any network
calls. Useful for unit fixtures and to make the abstract REST connector
pattern legible in the context of payer/provider integrations.

The canned resources honour the FHIR R4 schema: each one carries a
``resourceType``, a stable ``id``, and a ``meta.versionId`` that bumps
on ``create``. Code values use real LOINC / SNOMED CT / RxNorm /
ICD-10-CM codes drawn from USCDI v3 reference material.

Production swap-out::

    # Heavy:
    from fhir.resources.patient import Patient
    from fhirclient import client as fhirclient
    settings = {"app_id": "domain-explorer", "api_base": "https://fhir.example/R4"}
    smart = fhirclient.FHIRClient(settings=settings)
    p = Patient.read("123", smart.server)

    # Light, sync:
    import requests
    requests.get("https://fhir.example/R4/Patient/123",
                 headers={"Authorization": "Bearer ..."}).json()
"""

from __future__ import annotations

import copy
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional, Tuple


# -- types --------------------------------------------------------------------


class FhirError(Exception):
    """Base error mirroring the structure of an OperationOutcome."""

    def __init__(self, status: int, severity: str, code: str, diagnostics: str):
        self.status = status
        self.severity = severity
        self.code = code
        self.diagnostics = diagnostics
        super().__init__(f"FHIR {status} {code}: {diagnostics}")

    def operation_outcome(self) -> Dict[str, Any]:
        return {
            "resourceType": "OperationOutcome",
            "issue": [
                {
                    "severity": self.severity,
                    "code": self.code,
                    "diagnostics": self.diagnostics,
                }
            ],
        }


@dataclass
class FhirAuth:
    """Trivial bearer-token auth holder. Real clients add SMART on FHIR
    OAuth2, JWT-bearer, mTLS, etc."""

    bearer_token: Optional[str] = None
    headers: Dict[str, str] = field(default_factory=dict)

    def apply(self, request_headers: Dict[str, str]) -> Dict[str, str]:
        h = dict(request_headers)
        if self.bearer_token:
            h["Authorization"] = f"Bearer {self.bearer_token}"
        h.update(self.headers)
        return h


# -- canned resources ---------------------------------------------------------


def _now_iso() -> str:
    return datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%S+00:00")


def _patient_123() -> Dict[str, Any]:
    return {
        "resourceType": "Patient",
        "id": "123",
        "meta": {"versionId": "4", "lastUpdated": "2026-04-30T10:11:00+00:00"},
        "identifier": [
            {
                "system": "urn:oid:2.16.840.1.113883.4.1",
                "value": "999-22-1234",
                "type": {
                    "coding": [
                        {
                            "system": "http://terminology.hl7.org/CodeSystem/v2-0203",
                            "code": "SS",
                            "display": "Social Security number",
                        }
                    ]
                },
            },
            {"system": "https://example.org/mrn", "value": "MRN-77123"},
        ],
        "active": True,
        "name": [{"use": "official", "family": "Patel", "given": ["Anjali", "R"]}],
        "gender": "female",
        "birthDate": "1989-11-02",
        "address": [
            {
                "use": "home",
                "line": ["742 Evergreen Terrace"],
                "city": "Springfield",
                "state": "IL",
                "postalCode": "62701",
                "country": "US",
            }
        ],
        "communication": [
            {
                "language": {
                    "coding": [
                        {
                            "system": "urn:ietf:bcp:47",
                            "code": "en-US",
                            "display": "English (United States)",
                        }
                    ]
                },
                "preferred": True,
            }
        ],
    }


def _encounter_456() -> Dict[str, Any]:
    return {
        "resourceType": "Encounter",
        "id": "456",
        "meta": {"versionId": "1", "lastUpdated": "2026-05-04T14:22:09+00:00"},
        "status": "finished",
        "class": {
            "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
            "code": "AMB",
            "display": "ambulatory",
        },
        "type": [
            {
                "coding": [
                    {
                        "system": "http://snomed.info/sct",
                        "code": "185349003",
                        "display": "Encounter for check up",
                    }
                ]
            }
        ],
        "subject": {"reference": "Patient/123", "display": "Anjali Patel"},
        "period": {"start": "2026-05-04T13:30:00+00:00", "end": "2026-05-04T14:00:00+00:00"},
        "reasonCode": [
            {
                "coding": [
                    {
                        "system": "http://hl7.org/fhir/sid/icd-10-cm",
                        "code": "Z00.00",
                        "display": "Encounter for general adult medical examination",
                    }
                ]
            }
        ],
    }


def _observation_bp() -> Dict[str, Any]:
    return {
        "resourceType": "Observation",
        "id": "obs-bp-1",
        "meta": {"versionId": "1", "lastUpdated": "2026-05-04T13:35:00+00:00"},
        "status": "final",
        "category": [
            {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                        "code": "vital-signs",
                        "display": "Vital Signs",
                    }
                ]
            }
        ],
        "code": {
            "coding": [
                {
                    "system": "http://loinc.org",
                    "code": "85354-9",
                    "display": "Blood pressure panel",
                }
            ]
        },
        "subject": {"reference": "Patient/123"},
        "encounter": {"reference": "Encounter/456"},
        "effectiveDateTime": "2026-05-04T13:35:00+00:00",
        "component": [
            {
                "code": {
                    "coding": [
                        {"system": "http://loinc.org", "code": "8480-6",
                         "display": "Systolic blood pressure"}
                    ]
                },
                "valueQuantity": {
                    "value": 122, "unit": "mm[Hg]", "system": "http://unitsofmeasure.org",
                    "code": "mm[Hg]",
                },
            },
            {
                "code": {
                    "coding": [
                        {"system": "http://loinc.org", "code": "8462-4",
                         "display": "Diastolic blood pressure"}
                    ]
                },
                "valueQuantity": {
                    "value": 78, "unit": "mm[Hg]", "system": "http://unitsofmeasure.org",
                    "code": "mm[Hg]",
                },
            },
        ],
    }


def _observation_glucose() -> Dict[str, Any]:
    return {
        "resourceType": "Observation",
        "id": "obs-glu-1",
        "meta": {"versionId": "1", "lastUpdated": "2026-05-04T13:36:00+00:00"},
        "status": "final",
        "code": {
            "coding": [
                {"system": "http://loinc.org", "code": "2345-7",
                 "display": "Glucose [Mass/volume] in Serum or Plasma"}
            ]
        },
        "subject": {"reference": "Patient/123"},
        "encounter": {"reference": "Encounter/456"},
        "effectiveDateTime": "2026-05-04T13:36:00+00:00",
        "valueQuantity": {
            "value": 92, "unit": "mg/dL", "system": "http://unitsofmeasure.org", "code": "mg/dL"
        },
        "referenceRange": [
            {
                "low": {"value": 70, "unit": "mg/dL"},
                "high": {"value": 99, "unit": "mg/dL"},
                "type": {"text": "fasting"},
            }
        ],
    }


_CANNED: Dict[Tuple[str, str], Dict[str, Any]] = {
    ("Patient", "123"): _patient_123(),
    ("Encounter", "456"): _encounter_456(),
    ("Observation", "obs-bp-1"): _observation_bp(),
    ("Observation", "obs-glu-1"): _observation_glucose(),
}


# -- client -------------------------------------------------------------------


@dataclass
class FhirRestClient:
    """A minimal FHIR R4 REST client.

    The three core operations from the FHIR HTTP API are implemented:

    * ``read(resource_type, id)`` — `GET [base]/[type]/[id]`
    * ``search(resource_type, **params)`` — `GET [base]/[type]?...`
    * ``create(resource)`` — `POST [base]/[type]`

    No network is opened. The class keeps an in-memory store seeded with
    canned resources; ``create`` adds new resources to that store and
    returns them with a server-assigned ``id`` and ``versionId``.
    """

    base_url: str
    auth: Optional[FhirAuth] = None
    _store: Dict[Tuple[str, str], Dict[str, Any]] = field(default_factory=dict, init=False, repr=False)
    _next_id: int = field(default=1000, init=False, repr=False)

    def __post_init__(self) -> None:
        # Deep-copy the canned resources so callers can mutate freely.
        self._store = {k: copy.deepcopy(v) for k, v in _CANNED.items()}
        if self.auth is None:
            self.auth = FhirAuth()

    # --- low-level helpers ---

    def _build_url(self, resource_type: str, id: Optional[str] = None) -> str:
        url = self.base_url.rstrip("/") + "/" + resource_type
        if id:
            url += "/" + id
        return url

    def _request_headers(self, accept: str = "application/fhir+json") -> Dict[str, str]:
        h = {"Accept": accept, "User-Agent": "domain-explorer-stub/0.1"}
        if self.auth:
            h = self.auth.apply(h)
        return h

    # --- public API ---

    def read(self, resource_type: str, id: str) -> Dict[str, Any]:
        """`read` interaction. Returns the resource or raises 404."""
        # Force a header build so we exercise the auth surface.
        _ = self._request_headers()
        key = (resource_type, str(id))
        if key in self._store:
            return copy.deepcopy(self._store[key])
        raise FhirError(
            status=404,
            severity="error",
            code="not-found",
            diagnostics=f"Resource {resource_type}/{id} was not found.",
        )

    def search(self, resource_type: str, **params: Any) -> Dict[str, Any]:
        """`search` interaction. Supports the most common search parameters
        used in payer/provider workflows: ``patient``, ``subject``,
        ``encounter``, ``_id``, ``code``, ``category``, ``status``.

        Returns a Bundle of type ``searchset`` honouring FHIR R4 shape.
        """
        _ = self._request_headers()
        candidates = [
            r for k, r in self._store.items() if k[0] == resource_type
        ]
        candidates = list(filter(_search_predicate(params), candidates))
        # Apply _count if present.
        try:
            count = int(params.get("_count", "0"))
        except (TypeError, ValueError):
            count = 0
        if count > 0:
            candidates = candidates[:count]

        bundle = {
            "resourceType": "Bundle",
            "type": "searchset",
            "timestamp": _now_iso(),
            "total": len(candidates),
            "link": [
                {"relation": "self", "url": _format_search_url(self.base_url, resource_type, params)}
            ],
            "entry": [
                {
                    "fullUrl": f"{self.base_url.rstrip('/')}/{r['resourceType']}/{r['id']}",
                    "resource": copy.deepcopy(r),
                    "search": {"mode": "match"},
                }
                for r in candidates
            ],
        }
        return bundle

    def create(self, resource: Dict[str, Any]) -> Dict[str, Any]:
        """`create` interaction. Server assigns an id and versionId.
        Returns the created resource (mirrors the body of the
        ``201 Created`` response when ``Prefer: return=representation``
        is set)."""
        if not isinstance(resource, dict):
            raise FhirError(404, "error", "structure", "resource must be a JSON object")
        rtype = resource.get("resourceType")
        if not isinstance(rtype, str) or not rtype:
            raise FhirError(
                422, "error", "required", "resource.resourceType is required",
            )
        new_id = str(self._next_id)
        self._next_id += 1
        created = copy.deepcopy(resource)
        created["id"] = new_id
        created.setdefault("meta", {})
        created["meta"]["versionId"] = "1"
        created["meta"]["lastUpdated"] = _now_iso()
        self._store[(rtype, new_id)] = created
        return copy.deepcopy(created)


# -- search helpers -----------------------------------------------------------


def _search_predicate(params: Dict[str, Any]) -> Callable[[Dict[str, Any]], bool]:
    """Build a predicate over canned resources for the given search
    parameters. Only a subset of the FHIR search grammar is implemented."""

    def matches(resource: Dict[str, Any]) -> bool:
        for k, raw_v in params.items():
            if k.startswith("_") and k != "_id":
                continue
            v = str(raw_v)
            if k == "_id" and resource.get("id") != v:
                return False
            if k in ("patient", "subject"):
                ref = (resource.get("subject") or {}).get("reference", "")
                if not _matches_reference(ref, "Patient", v):
                    return False
            if k == "encounter":
                ref = (resource.get("encounter") or {}).get("reference", "")
                if not _matches_reference(ref, "Encounter", v):
                    return False
            if k == "status" and resource.get("status") != v:
                return False
            if k == "code":
                if not _matches_token(resource, "code", v):
                    return False
            if k == "category":
                if not _matches_token(resource, "category", v):
                    return False
        return True

    return matches


def _matches_reference(reference: str, expected_type: str, target: str) -> bool:
    """Match either ``Patient/123`` or just ``123``."""
    if not reference:
        return False
    expected = f"{expected_type}/{target}"
    return reference == expected or reference == target


_TOKEN_RE = re.compile(r"^(?:(?P<system>[^|]+)\|)?(?P<code>.+)$")


def _matches_token(resource: Dict[str, Any], field_name: str, raw: str) -> bool:
    """Token search like ``loinc.org|85354-9`` or ``85354-9``."""
    m = _TOKEN_RE.match(raw)
    if not m:
        return False
    target_system = (m.group("system") or "").strip()
    target_code = (m.group("code") or "").strip()
    field_value = resource.get(field_name)
    candidates: List[Dict[str, Any]] = []
    if isinstance(field_value, dict):
        candidates.append(field_value)
    elif isinstance(field_value, list):
        for v in field_value:
            if isinstance(v, dict):
                candidates.append(v)
    for c in candidates:
        for coding in c.get("coding", []) or []:
            if coding.get("code") != target_code:
                continue
            if target_system and target_system not in (coding.get("system") or ""):
                continue
            return True
    return False


def _format_search_url(base: str, rtype: str, params: Dict[str, Any]) -> str:
    parts = [f"{k}={v}" for k, v in params.items()]
    suffix = ("?" + "&".join(parts)) if parts else ""
    return f"{base.rstrip('/')}/{rtype}{suffix}"
