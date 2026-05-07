"""Demo MQTT client (Sparkplug B-aware).

Emulates the surface area of `paho-mqtt` / `aiomqtt`:

* `connect` / `disconnect`
* `publish(topic, payload, qos)` with QoS 0, 1, or 2
* `subscribe(topic, callback)` with single-level (`+`) and multi-level (`#`)
  wildcard matching
* MQTT 5 user-properties carried alongside the payload
* Sparkplug B namespace helpers — `make_sparkplug_topic` and
  `SparkplugBPayload` for building NDATA / DDATA messages

Like the other stubs in this package, no network is opened. A
thread-safe in-process broker keyed by ``host:port`` carries messages
between publishers and subscribers in the same process.

Production swap-out::

    # paho-mqtt:
    import paho.mqtt.client as mqtt
    c = mqtt.Client(client_id="edge-01", protocol=mqtt.MQTTv5)
    c.tls_set(ca_certs="ca.pem")
    c.username_pw_set("edge-01", "<password>")
    c.connect("broker.example.internal", 8883)
    c.publish("spBv1.0/Plant1/NDATA/EdgeNode1/Boiler", payload, qos=1)

    # aiomqtt (async):
    async with aiomqtt.Client("broker.example.internal", 8883) as client:
        await client.subscribe("spBv1.0/Plant1/#")
        async for msg in client.messages:
            ...
"""

from __future__ import annotations

import collections
import json
import re
import threading
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Mapping, Optional


# -- exceptions ---------------------------------------------------------------


class MqttError(Exception):
    """Mirrors paho.mqtt.MQTTException."""


# -- types -------------------------------------------------------------------


@dataclass
class MqttMessage:
    """Mirrors paho's MQTTMessage shape."""

    topic: str
    payload: bytes
    qos: int = 0
    retain: bool = False
    user_properties: Dict[str, str] = field(default_factory=dict)
    timestamp_ms: int = 0

    def payload_json(self) -> Any:
        return json.loads(self.payload.decode("utf-8"))


# -- Sparkplug B helpers -----------------------------------------------------


@dataclass
class SparkplugBPayload:
    """Tiny Sparkplug B Payload builder.

    The real Sparkplug B Payload is a Google protobuf message
    (`org.eclipse.tahu.protobuf.Payload`) with a `seq` number and
    `metrics` array of typed values. We emit a JSON shape that carries
    the same field names so callers can swap to protobuf without
    changing call sites.
    """

    seq: int
    timestamp_ms: int
    metrics: List[Dict[str, Any]] = field(default_factory=list)

    def to_bytes(self) -> bytes:
        return json.dumps(
            {"seq": self.seq, "timestamp": self.timestamp_ms, "metrics": list(self.metrics)},
            separators=(",", ":"),
        ).encode("utf-8")

    @classmethod
    def from_bytes(cls, raw: bytes) -> "SparkplugBPayload":
        body = json.loads(raw.decode("utf-8"))
        return cls(
            seq=int(body.get("seq", 0)),
            timestamp_ms=int(body.get("timestamp", 0)),
            metrics=list(body.get("metrics", [])),
        )


def make_sparkplug_topic(
    *,
    group_id: str,
    message_type: str,
    edge_node: str,
    device: Optional[str] = None,
    namespace: str = "spBv1.0",
) -> str:
    """Build a Sparkplug B topic of the form
    ``spBv1.0/<group>/<NDATA|DDATA|...>/<edge_node>[/<device>]``.

    Valid message types: ``NBIRTH``, ``NDATA``, ``NDEATH``, ``DBIRTH``,
    ``DDATA``, ``DDEATH``, ``NCMD``, ``DCMD``, ``STATE``.
    """
    valid = {"NBIRTH", "NDATA", "NDEATH", "DBIRTH", "DDATA", "DDEATH", "NCMD", "DCMD", "STATE"}
    if message_type not in valid:
        raise MqttError(f"unsupported sparkplug B message_type={message_type!r}")
    if device:
        return f"{namespace}/{group_id}/{message_type}/{edge_node}/{device}"
    return f"{namespace}/{group_id}/{message_type}/{edge_node}"


# -- in-memory broker --------------------------------------------------------


class _InMemoryBroker:
    """Threadsafe message bus keyed by broker address."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        # subs[address] = list[(topic_filter, callback)]
        self._subs: Dict[str, List[tuple]] = collections.defaultdict(list)
        # retained[address][topic] = MqttMessage
        self._retained: Dict[str, Dict[str, MqttMessage]] = collections.defaultdict(dict)

    def subscribe(self, address: str, topic_filter: str,
                  callback: Callable[[MqttMessage], None]) -> None:
        with self._lock:
            self._subs[address].append((topic_filter, callback))
            # Replay retained messages that match.
            for t, msg in list(self._retained[address].items()):
                if _topic_matches(topic_filter, t):
                    callback(msg)

    def publish(self, address: str, msg: MqttMessage) -> None:
        with self._lock:
            if msg.retain:
                self._retained[address][msg.topic] = msg
            for topic_filter, cb in list(self._subs[address]):
                if _topic_matches(topic_filter, msg.topic):
                    cb(msg)


_BROKER = _InMemoryBroker()


_WILDCARD_RE = re.compile(r"^[\w/+#\-.]+$")


def _topic_matches(topic_filter: str, topic: str) -> bool:
    """Standard MQTT wildcard match.

    ``+`` matches exactly one level, ``#`` matches zero or more levels
    (and must be the last character of the filter).
    """
    if not _WILDCARD_RE.match(topic_filter):
        return False
    f_parts = topic_filter.split("/")
    t_parts = topic.split("/")
    for i, fp in enumerate(f_parts):
        if fp == "#":
            return True
        if i >= len(t_parts):
            return False
        if fp == "+":
            continue
        if fp != t_parts[i]:
            return False
    return len(f_parts) == len(t_parts)


# -- client ------------------------------------------------------------------


@dataclass
class MqttClient:
    """Minimal demo MQTT client.

    Constructor parameters mirror paho-mqtt.Client + MQTT 5 connect-time
    options. Nothing is validated — this is a stub.
    """

    broker_host: str
    broker_port: int = 8883
    client_id: str = "domain-explorer-stub-client"
    username: Optional[str] = None
    password: Optional[str] = field(default=None, repr=False)
    use_tls: bool = True
    keepalive_s: int = 60
    protocol_version: int = 5  # MQTT 5
    _connected: bool = field(default=False, init=False, repr=False)

    @property
    def address(self) -> str:
        scheme = "mqtts" if self.use_tls else "mqtt"
        return f"{scheme}://{self.broker_host}:{self.broker_port}"

    # --- lifecycle ---

    def connect(self) -> "MqttClient":
        if self.protocol_version not in (3, 4, 5):
            raise MqttError(f"unsupported protocol_version={self.protocol_version}")
        self._connected = True
        return self

    def disconnect(self) -> None:
        self._connected = False

    def __enter__(self) -> "MqttClient":
        return self.connect()

    def __exit__(self, *exc: Any) -> None:
        self.disconnect()

    # --- public API ---

    def publish(
        self,
        topic: str,
        payload: Any,
        qos: int = 0,
        retain: bool = False,
        user_properties: Optional[Mapping[str, str]] = None,
    ) -> None:
        """Publish a message. ``payload`` may be bytes, str, or a JSON-
        serialisable Python value."""
        if not self._connected:
            self.connect()
        if qos not in (0, 1, 2):
            raise MqttError(f"qos must be 0, 1, or 2; got {qos}")
        body = _encode(payload)
        msg = MqttMessage(
            topic=topic,
            payload=body,
            qos=qos,
            retain=retain,
            user_properties=dict(user_properties or {}),
            timestamp_ms=int(time.time() * 1000),
        )
        _BROKER.publish(self.address, msg)

    def subscribe(
        self,
        topic_filter: str,
        callback: Callable[[MqttMessage], None],
        qos: int = 0,
    ) -> None:
        """Subscribe to a topic filter. ``callback`` is invoked
        synchronously per message in the same process."""
        if not self._connected:
            self.connect()
        if qos not in (0, 1, 2):
            raise MqttError(f"qos must be 0, 1, or 2; got {qos}")
        _BROKER.subscribe(self.address, topic_filter, callback)


# -- helpers -----------------------------------------------------------------


def _encode(value: Any) -> bytes:
    if value is None:
        return b""
    if isinstance(value, bytes):
        return value
    if isinstance(value, str):
        return value.encode("utf-8")
    if isinstance(value, SparkplugBPayload):
        return value.to_bytes()
    return json.dumps(value, separators=(",", ":")).encode("utf-8")
