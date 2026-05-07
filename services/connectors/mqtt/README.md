# mqtt — demo MQTT client (Sparkplug B-aware)

Demonstrates the **MQTT** and **Sparkplug B** connector patterns from
the registry (`conn.mqtt`, `conn.sparkplug_b` in
[`data/connectors/connectors.yaml`](../../../data/connectors/connectors.yaml)).

## What's here

```
mqtt/
├── __init__.py    # re-exports MqttClient, MqttMessage, SparkplugBPayload, MqttError
├── client.py      # client + in-memory broker + Sparkplug B helpers
├── examples.py    # runnable: python -m services.connectors.mqtt.examples
└── README.md      # you are here
```

## What it does

| Surface                                              | Notes                                                  |
| ---------------------------------------------------- | ------------------------------------------------------ |
| `connect()` / `disconnect()`                         | Validates protocol version (3, 4, or 5).               |
| `publish(topic, payload, qos, retain, user_props)`   | QoS 0/1/2, retained messages, MQTT 5 user properties.  |
| `subscribe(topic_filter, callback, qos)`             | `+` and `#` wildcard matching.                         |
| `make_sparkplug_topic(group, type, edge, device)`    | Builds `spBv1.0/<group>/<TYPE>/<edge>[/<device>]`.     |
| `SparkplugBPayload(seq, timestamp_ms, metrics)`      | Builder for the Tahu Payload (JSON-encoded in stub).   |

In-process publishers and subscribers exchange messages through a
thread-safe broker keyed by `host:port`, so the demo can show
end-to-end flows including retained messages and wildcard subscriptions
without a real broker.

Sparkplug B message types validated by `make_sparkplug_topic`:

```
NBIRTH  NDATA  NDEATH
DBIRTH  DDATA  DDEATH
NCMD    DCMD   STATE
```

## Production swap-out

Two main Python options:

- **`paho-mqtt`** — the canonical synchronous client. Used by most
  industrial gateways.
  ```python
  import paho.mqtt.client as mqtt
  c = mqtt.Client(client_id="edge-01", protocol=mqtt.MQTTv5)
  c.tls_set(ca_certs="ca.pem")
  c.username_pw_set("edge-01", "<password>")
  c.connect("broker.example.internal", 8883)
  c.publish("spBv1.0/Plant1/NDATA/EdgeNode1/Boiler", payload, qos=1)
  ```
- **`aiomqtt`** — async wrapper around paho, for IoT ingestion services.
  ```python
  async with aiomqtt.Client("broker.example.internal", 8883) as client:
      await client.subscribe("spBv1.0/Plant1/#")
      async for msg in client.messages:
          ...
  ```

For Sparkplug B Payload encoding, production code should use the
official Tahu protobuf bindings (`tahu` on PyPI) instead of the JSON
shape this stub emits. The field names line up so swap-out is a one-
liner per call site.

## Why this is a stub

MQTT + Sparkplug B is the standard for industrial IoT and Smart Metering
flows the Domain Explorer references. The stub gives subdomain demos
something to publish into and consume from without standing up a real
broker (Mosquitto, EMQX, HiveMQ, Cirrus Link), which has nontrivial
config (TLS, ACLs, persistence) the demos don't otherwise need.
