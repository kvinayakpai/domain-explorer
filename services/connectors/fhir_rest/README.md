# fhir_rest — demo FHIR R4 REST client

Demonstrates the **FHIR R4 REST** integration pattern used in modern
payer/provider and EHR-integration subdomains. Aligns with the abstract
`conn.rest` row in
[`data/connectors/connectors.yaml`](../../../data/connectors/connectors.yaml),
specialised for the FHIR resource model (HL7 FHIR 4.0.1).

## What's here

```
fhir_rest/
├── __init__.py    # re-exports FhirRestClient, FhirAuth, FhirError
├── client.py      # the demo client + canned Patient / Encounter / Observations
├── examples.py    # runnable: python -m services.connectors.fhir_rest.examples
└── README.md      # you are here
```

## What it does

Implements three of the FHIR HTTP API interactions:

| Method                          | HTTP                                  |
| ------------------------------- | ------------------------------------- |
| `client.read(type, id)`         | `GET [base]/[type]/[id]`              |
| `client.search(type, **params)` | `GET [base]/[type]?[search params]`   |
| `client.create(resource)`       | `POST [base]/[type]` (with body)      |

`search` returns a `Bundle` of type `searchset` with proper
`Bundle.entry.fullUrl` and `Bundle.link` shape, and supports the most
common search parameters: `patient` / `subject`, `encounter`, `_id`,
`_count`, `status`, and token searches against `code` / `category`
(e.g. `code=http://loinc.org|85354-9`).

The canned resources use real terminology codes drawn from USCDI v3:

| Resource     | Codes                                                  |
| ------------ | ------------------------------------------------------ |
| `Patient/123` | v2-0203 SS identifier, BCP-47 language `en-US`         |
| `Encounter/456` | v3-ActCode `AMB`, SNOMED CT `185349003`, ICD-10-CM `Z00.00` |
| `Observation/obs-bp-1` | LOINC `85354-9` (BP panel) + components `8480-6`, `8462-4` |
| `Observation/obs-glu-1` | LOINC `2345-7` Glucose, UCUM `mg/dL`           |

## Why FHIR R4

FHIR R4 is the baseline for ONC's USCDI mandates (2015 Edition Cures
Update), CMS Patient Access (CMS-9115-F), Da Vinci use cases, and
nearly every modern payer/provider integration the Domain Explorer
references. R5 exists but is not yet the regulatory floor in the U.S.;
many shops are pinned at R4 for exactly that reason.

## Production swap-out

Two production options, depending on how strict you want your client to
be about the FHIR schema:

- **`fhir.resources` + `requests`** — pydantic models for every FHIR
  resource, hand-rolled HTTP. Full validation, opinionated.
  ```python
  from fhir.resources.patient import Patient
  import requests
  body = requests.get(f"{base}/Patient/123", headers=auth).json()
  patient = Patient(**body)
  ```
- **`fhirclient`** — the official SMART-on-FHIR Python client. Bundles
  OAuth2 + SMART app launch.
  ```python
  from fhirclient import client as fhirclient
  smart = fhirclient.FHIRClient(settings={
      "app_id": "domain-explorer",
      "api_base": "https://fhir.example/R4",
  })
  patient = Patient.read("123", smart.server)
  ```

The shape of `FhirRestClient.read` / `.search` / `.create` matches the
ergonomic surface both libraries expose, so swap-out is mechanical.
