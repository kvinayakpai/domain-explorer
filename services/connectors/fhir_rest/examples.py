"""Runnable demonstration of :class:`FhirRestClient`.

::

    python -m services.connectors.fhir_rest.examples

Exercises the three RESTful operations from the FHIR R4 HTTP API:
``read``, ``search``, and ``create``. Uses canned data only — no
network is opened.
"""

from __future__ import annotations

import json

from .client import FhirAuth, FhirError, FhirRestClient


def _banner(title: str) -> None:
    bar = "=" * len(title)
    print(f"\n{bar}\n{title}\n{bar}")


def main() -> None:
    client = FhirRestClient(
        base_url="https://fhir.example.org/R4",
        auth=FhirAuth(bearer_token="<smart-on-fhir-jwt>"),
    )

    _banner("read Patient/123")
    patient = client.read("Patient", "123")
    print(json.dumps(patient, indent=2))

    _banner("read Patient/9999 — not found")
    try:
        client.read("Patient", "9999")
    except FhirError as exc:
        print("OperationOutcome ↓")
        print(json.dumps(exc.operation_outcome(), indent=2))

    _banner("search Observation?patient=123 — vital signs + glucose")
    bundle = client.search("Observation", patient="123", _count="10")
    print(f"Bundle.total = {bundle['total']}")
    for e in bundle["entry"]:
        r = e["resource"]
        code = (r.get("code") or {}).get("coding", [{}])[0]
        print(f"  - Observation/{r['id']}  {code.get('code'):>10s}  {code.get('display')}")

    _banner("search Observation?code=http://loinc.org|85354-9 — only BP panel")
    bundle = client.search("Observation", code="http://loinc.org|85354-9")
    for e in bundle["entry"]:
        r = e["resource"]
        coding = (r.get("code") or {}).get("coding", [{}])[0]
        print(f"  - Observation/{r['id']}  {coding.get('display')}")

    _banner("create Condition (new diagnosis on Patient/123)")
    new_condition = {
        "resourceType": "Condition",
        "clinicalStatus": {
            "coding": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/condition-clinical",
                    "code": "active",
                    "display": "Active",
                }
            ]
        },
        "verificationStatus": {
            "coding": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/condition-ver-status",
                    "code": "confirmed",
                    "display": "Confirmed",
                }
            ]
        },
        "category": [
            {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/condition-category",
                        "code": "encounter-diagnosis",
                        "display": "Encounter Diagnosis",
                    }
                ]
            }
        ],
        "code": {
            "coding": [
                {
                    "system": "http://hl7.org/fhir/sid/icd-10-cm",
                    "code": "E11.9",
                    "display": "Type 2 diabetes mellitus without complications",
                }
            ]
        },
        "subject": {"reference": "Patient/123"},
        "encounter": {"reference": "Encounter/456"},
        "recordedDate": "2026-05-04",
    }
    created = client.create(new_condition)
    print(f"server-assigned id      : {created['id']}")
    print(f"server-assigned version : {created['meta']['versionId']}")
    print(f"lastUpdated             : {created['meta']['lastUpdated']}")
    print()
    print(json.dumps(created, indent=2))

    _banner("read the just-created Condition by id")
    fetched = client.read("Condition", created["id"])
    coding = fetched["code"]["coding"][0]
    print(f"  Condition/{fetched['id']}  {coding['code']}  {coding['display']}")


if __name__ == "__main__":
    main()
