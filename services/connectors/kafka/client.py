"""Demo Kafka producer / consumer.

Emulates the surface area of the confluent-kafka-python and kafka-python
clients without opening a real network connection. Messages are routed
through an in-memory broker shared by every client constructed against
the same ``bootstrap_servers`` value, so producer/consumer pairs in the
same process can exchange messages end-to-end.

Production swap-out::

    # confluent-kafka-python (librdkafka under the hood):
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

    # kafka-python (pure Python):
    from kafka import KafkaProducer, KafkaConsumer
    KafkaProducer(bootstrap_servers="broker:9092",
                  security_protocol="SASL_SSL",
                  sasl_mechanism="SCRAM-SHA-512",
                  compression_type="lz4")
"""

from __future__ import annotations

import collections
import itertools
import json
import threading
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Iterator, List, Optional, Tuple


# -- exceptions ---------------------------------------------------------------


class KafkaError(Exception):
    """Base class for stub Kafka errors. Mirrors ``confluent_kafka.KafkaException``."""


class KafkaAuthError(KafkaError):
    """Raised when an unsupported auth mechanism is requested."""


# Auth mechanisms accepted by the stub. The real client supports more —
# this is just the common "production" set used in the registry.
_VALID_AUTH = {"PLAINTEXT", "PLAIN", "SCRAM-SHA-256", "SCRAM-SHA-512", "OAUTHBEARER", "GSSAPI"}
_VALID_COMPRESSION = {"none", "gzip", "snappy", "lz4", "zstd"}


# -- in-memory broker --------------------------------------------------------


@dataclass
class KafkaMessage:
    """One delivered Kafka record. Mirrors ``confluent_kafka.Message`` shape."""

    topic: str
    partition: int
    offset: int
    key: Optional[bytes]
    value: bytes
    headers: Dict[str, bytes] = field(default_factory=dict)
    timestamp_ms: int = 0

    def value_json(self) -> Any:
        """Convenience: decode value as JSON."""
        return json.loads(self.value.decode("utf-8"))


class _InMemoryBroker:
    """Threadsafe append-only log keyed by (bootstrap_servers, topic)."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        # topics[(bootstrap, topic)] = list[KafkaMessage]
        self._topics: Dict[Tuple[str, str], List[KafkaMessage]] = collections.defaultdict(list)
        # offsets[(bootstrap, group_id, topic)] = next-to-read offset
        self._offsets: Dict[Tuple[str, str, str], int] = collections.defaultdict(int)
        self._counter = itertools.count(1)

    def append(self, bootstrap: str, msg: KafkaMessage) -> int:
        with self._lock:
            log = self._topics[(bootstrap, msg.topic)]
            offset = len(log)
            stored = KafkaMessage(
                topic=msg.topic,
                partition=msg.partition,
                offset=offset,
                key=msg.key,
                value=msg.value,
                headers=dict(msg.headers),
                timestamp_ms=msg.timestamp_ms or int(time.time() * 1000),
            )
            log.append(stored)
            return offset

    def read(self, bootstrap: str, group_id: str, topic: str, max_messages: int) -> List[KafkaMessage]:
        with self._lock:
            log = self._topics.get((bootstrap, topic), [])
            offset = self._offsets[(bootstrap, group_id, topic)]
            slice_ = log[offset : offset + max_messages]
            return list(slice_)

    def commit(self, bootstrap: str, group_id: str, topic: str, new_offset: int) -> None:
        with self._lock:
            self._offsets[(bootstrap, group_id, topic)] = new_offset

    def topic_size(self, bootstrap: str, topic: str) -> int:
        with self._lock:
            return len(self._topics.get((bootstrap, topic), []))


_BROKER = _InMemoryBroker()


# -- producer ----------------------------------------------------------------


@dataclass
class KafkaProducer:
    """A minimal demo Kafka producer.

    The constructor parameters mirror the most-used confluent-kafka client
    options. Nothing is validated against a real broker — the producer
    appends messages to an in-process queue keyed by ``bootstrap_servers``.
    """

    bootstrap_servers: str
    auth_mechanism: str = "PLAINTEXT"
    sasl_username: Optional[str] = None
    sasl_password: Optional[str] = field(default=None, repr=False)
    compression_type: str = "none"
    client_id: str = "domain-explorer-stub-producer"
    _connected: bool = field(default=False, init=False, repr=False)

    def __post_init__(self) -> None:
        if self.auth_mechanism not in _VALID_AUTH:
            raise KafkaAuthError(
                f"unsupported auth_mechanism={self.auth_mechanism!r}; "
                f"expected one of {sorted(_VALID_AUTH)}"
            )
        if self.compression_type not in _VALID_COMPRESSION:
            raise KafkaError(
                f"unsupported compression_type={self.compression_type!r}; "
                f"expected one of {sorted(_VALID_COMPRESSION)}"
            )

    # --- lifecycle ---

    def connect(self) -> None:
        self._connected = True

    def flush(self, timeout: float = 0.0) -> int:
        """Flush any pending messages. The stub is synchronous so always 0."""
        _ = timeout
        return 0

    def close(self) -> None:
        self._connected = False

    def __enter__(self) -> "KafkaProducer":
        self.connect()
        return self

    def __exit__(self, *exc: Any) -> None:
        self.close()

    # --- public API ---

    def publish(
        self,
        topic: str,
        key: Optional[Any] = None,
        value: Any = None,
        headers: Optional[Dict[str, Any]] = None,
    ) -> int:
        """Publish one record. Returns the assigned offset.

        ``key`` and ``value`` are JSON-encoded if they aren't already bytes.
        """
        if not self._connected:
            self.connect()

        key_bytes = _encode(key)
        value_bytes = _encode(value)
        header_bytes: Dict[str, bytes] = {
            k: _encode(v) or b"" for k, v in (headers or {}).items()
        }

        msg = KafkaMessage(
            topic=topic,
            partition=0,
            offset=0,
            key=key_bytes,
            value=value_bytes or b"",
            headers=header_bytes,
        )
        return _BROKER.append(self.bootstrap_servers, msg)


# -- consumer ----------------------------------------------------------------


@dataclass
class KafkaConsumer:
    """A minimal demo Kafka consumer.

    Calls to :meth:`subscribe` register a topic for the consumer's group.
    :meth:`poll` returns the next batch of unread messages and advances
    the in-memory commit offset.
    """

    bootstrap_servers: str
    group_id: str
    auth_mechanism: str = "PLAINTEXT"
    sasl_username: Optional[str] = None
    sasl_password: Optional[str] = field(default=None, repr=False)
    auto_offset_reset: str = "earliest"
    client_id: str = "domain-explorer-stub-consumer"
    _topics: List[str] = field(default_factory=list, init=False, repr=False)
    _connected: bool = field(default=False, init=False, repr=False)

    def __post_init__(self) -> None:
        if self.auth_mechanism not in _VALID_AUTH:
            raise KafkaAuthError(
                f"unsupported auth_mechanism={self.auth_mechanism!r}; "
                f"expected one of {sorted(_VALID_AUTH)}"
            )

    def connect(self) -> None:
        self._connected = True

    def close(self) -> None:
        self._connected = False

    def __enter__(self) -> "KafkaConsumer":
        self.connect()
        return self

    def __exit__(self, *exc: Any) -> None:
        self.close()

    # --- public API ---

    def subscribe(
        self,
        topic: str,
        callback: Optional[Callable[[KafkaMessage], None]] = None,
    ) -> None:
        """Subscribe to a topic. If ``callback`` is supplied, immediately
        drain whatever is currently on the topic and invoke it per message.
        Otherwise, callers should drive consumption via :meth:`poll`."""
        if not self._connected:
            self.connect()
        if topic not in self._topics:
            self._topics.append(topic)
        if callback is not None:
            for msg in self._drain(topic, max_messages=10_000):
                callback(msg)

    def poll(self, max_messages: int = 100) -> List[KafkaMessage]:
        """Return up to ``max_messages`` records across subscribed topics
        and advance the committed offset to just past them."""
        if not self._connected:
            self.connect()
        out: List[KafkaMessage] = []
        for topic in self._topics:
            out.extend(self._drain(topic, max_messages - len(out)))
            if len(out) >= max_messages:
                break
        return out

    def consume(self, max_messages: int = 100) -> Iterator[KafkaMessage]:
        """Iterator-style alias for :meth:`poll`."""
        for msg in self.poll(max_messages=max_messages):
            yield msg

    # --- internal ---

    def _drain(self, topic: str, max_messages: int) -> List[KafkaMessage]:
        if max_messages <= 0:
            return []
        msgs = _BROKER.read(self.bootstrap_servers, self.group_id, topic, max_messages)
        if msgs:
            new_offset = msgs[-1].offset + 1
            _BROKER.commit(self.bootstrap_servers, self.group_id, topic, new_offset)
        return msgs


# -- helpers -----------------------------------------------------------------


def _encode(value: Any) -> Optional[bytes]:
    if value is None:
        return None
    if isinstance(value, bytes):
        return value
    if isinstance(value, str):
        return value.encode("utf-8")
    return json.dumps(value, separators=(",", ":")).encode("utf-8")
