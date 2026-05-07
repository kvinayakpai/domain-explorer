# sap_rfc — demo SAP RFC / BAPI client

Demonstrates the **SAP RFC / BAPI** connector pattern from the registry
(`conn.sap_rfc` in
[`data/connectors/connectors.yaml`](../../../data/connectors/connectors.yaml)).

## What's here

```
sap_rfc/
├── __init__.py    # re-exports SapRfcClient
├── client.py      # the demo client, with three canned BAPIs
├── examples.py    # runnable: python -m services.connectors.sap_rfc.examples
└── README.md      # you are here
```

## What it does

`SapRfcClient` exposes a tiny subset of the surface area of an SAP
NetWeaver RFC client:

- `connect()` / `disconnect()` (and a context-manager interface).
- `call_function(fn_name, **params)` for synchronous BAPI calls.

Three function modules are recognised, with shapes faithful to the real
ABAP DDIC types:

| Function module             | What it does                          |
| --------------------------- | -------------------------------------- |
| `BAPI_MATERIAL_GET_DETAIL`  | Material master read, returns `MATERIAL_GENERAL_DATA` + `RETURN` |
| `BAPI_CUSTOMER_GETLIST`     | Customer master list with optional `CUSTOMER_IDS` filter |
| `RFC_READ_TABLE`            | Generic table reader for transparent tables (canned: `T001`) |

Any other function module raises `NotImplementedError`.

## Production swap-out

The signature of `call_function` matches `pyrfc.Connection.call`
deliberately, so a real implementation looks like:

```python
from pyrfc import Connection

conn = Connection(
    ashost=host, sysnr=sysnr, client=client,
    user=user, passwd=password,
)
result = conn.call("BAPI_MATERIAL_GET_DETAIL", MATERIAL="000000000000000123")
```

`pyrfc` requires the SAP NetWeaver RFC SDK installed locally — that's
why teams often gate this connector behind a lightweight Python service
running where the SDK is licensed. Alternatives:

- [`sap_rfc`](https://pypi.org/project/sap-rfc/) — pure-Python wire
  protocol implementation (limited BAPI surface).
- The **SAP Cloud SDK** for cloud-resident workloads.
- The **OData v4 / SAP Gateway** path when synchronous BAPI semantics
  aren't required — usually a better long-term choice.

## Why this is a stub

The Domain Explorer is not a runtime integration platform; it's a
metadata browser for understanding how subdomains map to source systems
and connectors. This stub exists to make the abstract registry row
concrete: you can see what a BAPI call looks like, what fields come
back, and how to wire it into a pipeline. Real ELT happens elsewhere.
