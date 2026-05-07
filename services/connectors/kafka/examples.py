"""Runnable demonstration of :class:`KafkaProducer` / :class:`KafkaConsumer`.

::

    python -m services.connectors.kafka.examples

Produces 5 events to ``payments.captured.v1`` and consumes them via a
group ``finops-aggregator-1`` with explicit offset commits.
"""

from __future__ import annotations

import json
from .client import KafkaConsumer, KafkaProducer


def _banner(title: str) -> None:
    bar = "=" * len(title)
    print(f"\n{bar}\n{title}\n{bar}")


TOPIC = "payments.captured.v1"
BOOTSTRAP = "broker-a.example.internal:9092,broker-b.example.internal:9092"


def main() -> None:
    _banner("Producer — publish 5 events to payments.captured.v1")
    with KafkaProducer(
        bootstrap_servers=BOOTSTRAP,
        auth_mechanism="SCRAM-SHA-512",
        sasl_username="payments-cdc",
        sasl_password="<not-used>",
        compression_type="zstd",
        client_id="payments-cdc-1",
    ) as producer:
        events = [
            {"payment_id": f"PAY{i:06d}", "amount": 49.95 + i, "currency": "USD",
             "rail": "CARD", "auth_status": "approved"}
            for i in range(1, 6)
        ]
        for e in events:
            offset = producer.publish(
                topic=TOPIC,
                key=e["payment_id"],
                value=e,
                headers={"source": "card-network", "schema": "payments.captured.v1"},
            )
            print(f"  produced {e['payment_id']} -> offset {offset}")
        producer.flush()

    _banner("Consumer — drain payments.captured.v1 with offset commits")
    with KafkaConsumer(
        bootstrap_servers=BOOTSTRAP,
        group_id="finops-aggregator-1",
        auth_mechanism="SCRAM-SHA-512",
        sasl_username="finops-aggregator",
        sasl_password="<not-used>",
        auto_offset_reset="earliest",
    ) as consumer:
        consumer.subscribe(TOPIC)
        batch = consumer.poll(max_messages=10)
        print(f"received {len(batch)} message(s)")
        for msg in batch:
            decoded = msg.value_json()
            key = msg.key.decode() if msg.key else None
            print(
                f"  [partition={msg.partition} offset={msg.offset} key={key}] "
                f"{json.dumps(decoded)}"
            )

    _banner("Consumer — second poll should be empty (offsets committed)")
    with KafkaConsumer(
        bootstrap_servers=BOOTSTRAP,
        group_id="finops-aggregator-1",
    ) as consumer:
        consumer.subscribe(TOPIC)
        leftover = consumer.poll(max_messages=10)
        print(f"received {len(leftover)} message(s) on re-poll")


if __name__ == "__main__":
    main()
