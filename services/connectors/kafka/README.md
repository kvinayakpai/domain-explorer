# kafka — demo Kafka producer / consumer

Demonstrates the **CDC via Kafka** connector pattern from the registry
(`conn.cdc_kafka` in
[`data/connectors/connectors.yaml`](../../../data/connectors/connectors.yaml)).

## What's here

```
kafka/
├── __init__.py    # re-exports KafkaProducer, KafkaConsumer, KafkaMessage, KafkaError
├── client.py      # producer + consumer + in-memory broker
├── examples.py    # runnable: python -m services.connectors.kafka.examples
└── README.md      # you are here
```

## What it does

`KafkaProducer.publish(topic, key, value)` and
`KafkaConsumer.subscribe(topic, callback)` go through a thread-safe
in-process broker keyed by `bootstrap_servers`. Producer/consumer pairs
in the same process exchange real messages end-to-end so the demo can
show offset commits without needing a real broker.

| Surface                                  | Notes                                                              |
| ---------------------------------------- | ------------------------------------------------------------------ |
| `KafkaProducer.publish(topic, key, val)` | Returns the assigned offset. JSON-encodes Python values.           |
| `KafkaProducer.flush(timeout)`           | No-op in the stub (synchronous).                                   |
| `KafkaConsumer.subscribe(topic, cb)`     | Subscribe + optional drain via callback.                           |
| `KafkaConsumer.poll(max_messages)`       | Pull-style consume; commits offsets on success.                    |
| `KafkaMessage.value_json()`              | Helper for the common JSON-payload case.                           |

The constructor takes the same options you'd hit on a real client:

- `bootstrap_servers` — comma-separated broker list.
- `auth_mechanism` — `PLAINTEXT`, `PLAIN`, `SCRAM-SHA-256`,
  `SCRAM-SHA-512`, `OAUTHBEARER`, or `GSSAPI`.
- `compression_type` — `none`, `gzip`, `snappy`, `lz4`, `zstd`.
- `sasl_username` / `sasl_password`.
- `client_id`.
- (Consumer) `group_id`, `auto_offset_reset`.

Anything not in those lists raises `KafkaAuthError` / `KafkaError` so
the contract is checked even without a real broker.

## Production swap-out

Two production clients are common:

- **`confluent-kafka-python`** — librdkafka wrapper, the default for new
  Python pipelines.
  ```python
  from confluent_kafka import Producer, Consumer
  p = Producer({
      "bootstrap.servers": "broker:9092",
      "security.protocol": "SASL_SSL",
      "sasl.mechanism": "SCRAM-SHA-512",
      "sasl.username": "...", "sasl.password": "...",
      "compression.type": "zstd",
  })
  p.produce("payments.captured.v1", key=b"id", value=b"...")
  p.flush()
  ```
- **`kafka-python`** — pure-Python, used where librdkafka is awkward
  (Lambda layers, restricted CI).

Both libraries expose `produce` / `subscribe` / `poll` shapes that match
this stub's surface, so swap-out is mechanical.

## Why this is a stub

The Domain Explorer is not a runtime integration platform. Real CDC
pipelines pair a producer-side connector (Debezium, Confluent CDC
connectors, AWS DMS) with a consumer-side worker. This stub exists to
let pipeline authors prototype the consumer side against a known
message shape (`payments.captured.v1`) without needing a broker.
