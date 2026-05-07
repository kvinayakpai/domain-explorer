"""Runnable demonstration of :class:`MqttClient` (Sparkplug B-aware).

::

    python -m services.connectors.mqtt.examples

Publishes 3 Sparkplug B NDATA messages and subscribes with a wildcard
filter at QoS 1.
"""

from __future__ import annotations

import time
from typing import List

from .client import (
    MqttClient,
    MqttMessage,
    SparkplugBPayload,
    make_sparkplug_topic,
)


def _banner(title: str) -> None:
    bar = "=" * len(title)
    print(f"\n{bar}\n{title}\n{bar}")


def main() -> None:
    received: List[MqttMessage] = []

    def on_message(msg: MqttMessage) -> None:
        received.append(msg)
        print(f"  [qos={msg.qos} retain={msg.retain}] {msg.topic}")

    # Subscriber connects first.
    sub = MqttClient(
        broker_host="broker.iot.example.internal",
        broker_port=8883,
        client_id="finops-edge-collector",
        username="finops-edge",
        password="<not-used>",
        use_tls=True,
        protocol_version=5,
    ).connect()

    _banner("Subscribe spBv1.0/Plant1/NDATA/+/#  (QoS 1)")
    sub.subscribe("spBv1.0/Plant1/NDATA/+/#", on_message, qos=1)

    pub = MqttClient(
        broker_host="broker.iot.example.internal",
        broker_port=8883,
        client_id="edge-node-001",
        username="edge-node-001",
        password="<not-used>",
        use_tls=True,
        protocol_version=5,
    ).connect()

    _banner("Publish 3 Sparkplug B NDATA messages")
    base_ts = int(time.time() * 1000)
    for i, edge_node in enumerate(("EdgeNode1", "EdgeNode2", "EdgeNode1")):
        topic = make_sparkplug_topic(
            group_id="Plant1",
            message_type="NDATA",
            edge_node=edge_node,
            device="Boiler" if i != 1 else "Conveyor",
        )
        payload = SparkplugBPayload(
            seq=i,
            timestamp_ms=base_ts + i * 100,
            metrics=[
                {"name": "temp_C",   "alias": 1, "value": 78.4 + i, "datatype": "Double"},
                {"name": "pressure", "alias": 2, "value": 2.4,      "datatype": "Double"},
            ],
        )
        pub.publish(
            topic=topic,
            payload=payload,
            qos=1,
            user_properties={"schema": "spBv1.0", "edge": edge_node},
        )
        print(f"  published -> {topic}")

    _banner("Decoded subscription messages")
    print(f"received {len(received)} message(s)")
    for msg in received:
        decoded = SparkplugBPayload.from_bytes(msg.payload)
        names = ", ".join(m["name"] for m in decoded.metrics)
        edge_prop = msg.user_properties.get("edge", "?")
        print(f"  topic={msg.topic} edge={edge_prop} seq={decoded.seq} metrics=[{names}]")

    _banner("Plain MQTT publish — non-Sparkplug topic")
    pub.publish(
        topic="factory/lineA/heartbeat",
        payload={"ok": True, "uptime_s": 9999},
        qos=0,
        retain=True,
    )
    print("  published heartbeat (qos=0, retain=true)")


if __name__ == "__main__":
    main()
