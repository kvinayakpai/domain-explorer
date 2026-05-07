"""Runnable demo connector stubs.

The Domain Explorer ships a typed registry of 23 connector patterns in
``data/connectors/connectors.yaml``. That registry is intentionally
abstract — protocol, auth, latency, modes — and is deliberately kept
language-agnostic so it can be referenced from any subdomain.

This Python package complements the registry with eight runnable, self-
contained demo stubs that show the *shape* of a real implementation for
the highest-leverage patterns:

- ``sap_rfc``    — synchronous BAPI calls over an RFC-style transport
  (registry id ``conn.sap_rfc``).
- ``swift_mt``   — parsing of legacy SWIFT MT block-structured messages
  (registry id ``conn.swift_iso20022``).
- ``fhir_rest``  — RESTful FHIR R4 resource access against an EHR or
  payer FHIR server (closest analogue is ``conn.rest`` plus FHIR resources).
- ``kafka``      — Kafka producer + consumer with SASL/SCRAM, OAuthbearer,
  and zstd/lz4/snappy compression (registry id ``conn.cdc_kafka``).
- ``rest_json``  — generic REST/JSON client with OAuth2, retry, pagination,
  and JSON-Schema validation (registry id ``conn.rest``).
- ``odbc``       — ODBC adapter with parameterised execute, executemany,
  and chunked fetch_iter for big result sets.
- ``opc_ua``     — OPC UA client with security policies, namespace browse,
  read, and subscriptions (registry id ``conn.opc_ua``).
- ``mqtt``       — MQTT 5 publisher/subscriber with QoS 0/1/2, wildcard
  topics, and Sparkplug B helpers (registry ids ``conn.mqtt``,
  ``conn.sparkplug_b``).

None of these stubs make real network calls. They return canned, schema-
shaped responses suitable for use in unit tests, demos, and reference
material. Each module's ``examples.py`` script is runnable end-to-end
with no external dependencies and no credentials.
"""

__all__ = [
    "sap_rfc",
    "swift_mt",
    "fhir_rest",
    "kafka",
    "rest_json",
    "odbc",
    "opc_ua",
    "mqtt",
]
__version__ = "0.2.0"
