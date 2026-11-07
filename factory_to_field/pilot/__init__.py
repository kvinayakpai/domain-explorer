"""Pilot readiness (gate G5) pieces that do not need real plant systems.

    audit.py      tamper-evident audit log (hash-chained JSON lines, persisted to disk)
    idp.py        OIDC-style identity provider simulator: signed RS256 tokens for named people and
                  for the agent's service client, with a JWKS endpoint resource servers verify against
    approvals.py  approve, reject and release drafts with a signed identity instead of a typed name
    review.py     review workflow for the identity-resolution queue, fed back into the KG build
    uns.py        Unified Namespace replay over MQTT: alarms on the wire open agent cases
    connectors.py hardened HTTP client for the real-system dialects: OAuth2 client credentials,
                  retries with back-off, paging, SAP CSRF tokens, OSDU data partitions

Everything here runs against the simulators. Real systems (SAP PM, PI, OSDU, PLM/MES), a corporate
identity provider and real reviewers are what remain for the gate itself.
"""
