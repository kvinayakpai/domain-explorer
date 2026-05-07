# opc_ua — demo OPC UA client

Demonstrates the **OPC UA** connector pattern from the registry
(`conn.opc_ua` in
[`data/connectors/connectors.yaml`](../../../data/connectors/connectors.yaml)).
OPC UA is the standard for industrial IoT integrations — Siemens
Opcenter, Rockwell FactoryTalk, GE Proficy, and most modern PLCs and
historians expose data through it.

## What's here

```
opc_ua/
├── __init__.py    # re-exports OpcUaClient, NodeValue, OpcUaError
├── client.py      # the demo client + canned MES address space
├── examples.py    # runnable: python -m services.connectors.opc_ua.examples
└── README.md      # you are here
```

## What it does

| Surface                                              | Notes                                                  |
| ---------------------------------------------------- | ------------------------------------------------------ |
| `connect()` / `disconnect()`                         | Validates endpoint URL + security policy.              |
| `browse_namespace()`                                 | Returns all canned `(node_id, data_type, unit)` tuples.|
| `read_node(node_id)`                                 | One-shot read returning a `NodeValue`.                 |
| `subscribe(node_id, interval_ms, callback, max=N)`   | Monitored item; runs synchronously to N samples.       |

The canned address space includes the kind of tags you'd find in a real
MES floor — boiler temperature, conveyor speed, packer counts, oven
setpoints, plant heartbeat — with realistic data types (`Double`,
`Int32`, `String`, `Boolean`) and oscillating value generators so the
subscription demo shows non-constant data.

Security policies validated by the constructor:

- `None`
- `Basic128Rsa15`
- `Basic256`
- `Basic256Sha256` (default — the most-deployed policy)
- `Aes128Sha256RsaOaep`
- `Aes256Sha256RsaPss`

## Production swap-out

Two main Python options:

- **`asyncua`** (formerly `opcua-asyncio`) — fully async client, the
  modern default.
  ```python
  import asyncio
  from asyncua import Client

  async def run():
      async with Client(url="opc.tcp://plc.example.internal:4840") as c:
          await c.set_security_string(
              "Basic256Sha256,SignAndEncrypt,client.der,client.pem"
          )
          temp = await c.get_node("ns=2;s=Boiler.Temp").read_value()
  ```
- **`python-opcua`** — older synchronous client, still in production
  use where async isn't available.

`OpcUaClient.read_node` and `OpcUaClient.subscribe` mirror the asyncua
ergonomic surface so swap-out is mostly mechanical (plus an `await`).

## Why this is a stub

The Domain Explorer references OPC UA from MES / Quality / Smart
Metering / EV Charging subdomains — none of which can be demonstrated
without a PLC or historian on the other end. This stub provides a
realistic-looking address space so subdomain demos can show
end-to-end "tag → KPI" flows without a real industrial endpoint.
