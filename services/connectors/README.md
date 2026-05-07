# services/connectors

Runnable demo connector stubs that complement the abstract connector
registry in [`data/connectors/connectors.yaml`](../../data/connectors/connectors.yaml).

The registry is intentionally **language-agnostic** — it captures the
protocol, auth, latency, and modes of each connector pattern but says
nothing about implementation. These stubs show the *shape* of a real
client for the eight highest-leverage patterns. Each one is self-
contained, uses only the Python standard library, and ships with a
runnable `examples.py`.

## Stubs

| Folder                    | Registry id(s)                          | What it demonstrates                                                  |
| ------------------------- | --------------------------------------- | --------------------------------------------------------------------- |
| [`sap_rfc/`](sap_rfc)     | `conn.sap_rfc`                          | Synchronous BAPI / RFC calls (BAPI_MATERIAL_GET_DETAIL, RFC_READ_TABLE) |
| [`swift_mt/`](swift_mt)   | `conn.swift_iso20022`                   | Block-structured MT103 / MT202 parsing into named field dicts         |
| [`fhir_rest/`](fhir_rest) | `conn.rest` (FHIR R4)                   | `read` / `search` / `create` against Patient, Encounter, Observation  |
| [`kafka/`](kafka)         | `conn.cdc_kafka`                        | Producer + consumer, SASL/SCRAM/OAUTHBEARER auth, offset commits      |
| [`rest_json/`](rest_json) | `conn.rest`                             | OAuth2, retry/backoff, pagination iterator, JSON-Schema validation    |
| [`odbc/`](odbc)           | (generic ODBC)                          | Parameterised execute, executemany, chunked fetch_iter                |
| [`opc_ua/`](opc_ua)       | `conn.opc_ua`                           | Endpoint + security policy, namespace browse, read, subscribe         |
| [`mqtt/`](mqtt)           | `conn.mqtt`, `conn.sparkplug_b`         | MQTT 5 pub/sub, QoS levels, wildcards, Sparkplug B topics + payloads  |

Each folder has:

- `client.py` (or `parser.py` for swift_mt) — the connector class with
  type hints, docstrings, and canned responses that honor the underlying
  standard.
- `examples.py` — a `python -m` runnable script that demonstrates the
  three or four most common operations and prints sample output.
- `README.md` — pointers to production-grade libraries you would reach
  for in a real implementation, plus the registry reference.

## Why stubs

The Domain Explorer is a metadata browser, not a runtime integration
hub. Real implementations of these connectors live in customer-side
ELT pipelines (Boomi, Mulesoft, Informatica, Fivetran, custom Python).
The stubs exist for three reasons:

1. **Concreteness.** Showing a working `SwiftMtParser` or `KafkaProducer`
   makes the abstract row in `connectors.yaml` legible — you can see
   what the data really looks like coming off the wire.
2. **Testing.** Subdomains that reference these patterns (cross-border
   payments, FHIR-based payer/provider integration, SAP-driven supply
   chain, MES quality, smart metering) can pull in the stubs as
   fixtures for their own tests.
3. **Onboarding.** Engineers new to a vertical see one canonical
   reference instead of having to reverse-engineer a customer's
   pipeline.

## Production swap-out

When swapping a stub for a production client, the public surface should
remain the same so callers don't have to change. Each stub's
`client.py` documents the production library it would delegate to:

- `sap_rfc`    → [`pyrfc`](https://github.com/SAP/PyRFC) (SAP NW RFC SDK)
- `swift_mt`   → [`mt-940`](https://pypi.org/project/mt-940/),
  [`swift-parser`](https://github.com/anchormarine/swift-parser)
- `fhir_rest`  → [`fhir.resources`](https://pypi.org/project/fhir.resources/)
  + [`fhirclient`](https://pypi.org/project/fhirclient/)
- `kafka`      → [`confluent-kafka-python`](https://github.com/confluentinc/confluent-kafka-python)
  or [`kafka-python`](https://github.com/dpkp/kafka-python)
- `rest_json`  → [`httpx`](https://www.python-httpx.org/) +
  [`tenacity`](https://github.com/jd/tenacity) +
  [`jsonschema`](https://python-jsonschema.readthedocs.io/)
- `odbc`       → [`pyodbc`](https://github.com/mkleehammer/pyodbc) or
  [`SQLAlchemy`](https://www.sqlalchemy.org/) with an ODBC dialect
- `opc_ua`     → [`asyncua`](https://github.com/FreeOpcUa/opcua-asyncio)
  (or the older `python-opcua`)
- `mqtt`       → [`paho-mqtt`](https://github.com/eclipse/paho.mqtt.python)
  or [`aiomqtt`](https://github.com/sbtinstruments/aiomqtt); add
  [`tahu`](https://github.com/eclipse-tahu/tahu) for the protobuf
  Sparkplug B Payload.

## Running the examples

From the repo root:

```bash
python -m services.connectors.sap_rfc.examples
python -m services.connectors.swift_mt.examples
python -m services.connectors.fhir_rest.examples
python -m services.connectors.kafka.examples
python -m services.connectors.rest_json.examples
python -m services.connectors.odbc.examples
python -m services.connectors.opc_ua.examples
python -m services.connectors.mqtt.examples
```

No third-party packages required.
