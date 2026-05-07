"""Demo OPC UA client.

Emulates the surface area of `asyncua` / `opcua-asyncio` for industrial
IoT integrations: ``connect`` with a security policy, ``read_node`` for
single-shot reads, ``subscribe`` for monitored items, and
``browse_namespace`` for discovery.

The stub's address space is hand-built and contains a small set of MES
nodes you'd typically see on a brownfield boiler / conveyor / oven
floor. No network is opened; subscriptions deliver synthetic values via
an in-process timer.

Production swap-out::

    import asyncio
    from asyncua import Client
    async def run():
        async with Client(
            url="opc.tcp://plc.example.internal:4840",
            timeout=30,
        ) as c:
            await c.set_security_string(
                "Basic256Sha256,SignAndEncrypt,client.der,client.pem"
            )
            n = c.get_node("ns=2;s=Boiler.Temp")
            print(await n.read_value())
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple


# -- exceptions ---------------------------------------------------------------


class OpcUaError(Exception):
    """Base class for stub OPC UA errors. Mirrors asyncua.ua.UaError."""


# -- types -------------------------------------------------------------------


_VALID_SECURITY_POLICIES = {
    "None",
    "Basic128Rsa15",
    "Basic256",
    "Basic256Sha256",
    "Aes128Sha256RsaOaep",
    "Aes256Sha256RsaPss",
}


@dataclass
class NodeValue:
    """Mirrors asyncua's DataValue shape."""

    node_id: str
    value: Any
    data_type: str
    source_timestamp_ms: int
    server_timestamp_ms: int
    quality: str = "Good"


# -- canned address space ----------------------------------------------------


# Nodes are keyed by their full NodeId string and carry a "next value"
# generator that a subscription can pump on each interval.

def _osc(base: float, amp: float, period_s: float) -> Callable[[int], float]:
    """Deterministic oscillator for a given (base, amplitude, period)."""
    import math

    def f(i: int) -> float:
        return round(base + amp * math.sin((i / max(period_s, 1)) * 2 * math.pi), 2)
    return f


_ADDRESS_SPACE: Dict[str, Dict[str, Any]] = {
    "ns=2;s=Boiler.Temp":     {"type": "Double",  "unit": "degC",  "gen": _osc(78.0, 4.0, 30)},
    "ns=2;s=Boiler.Pressure": {"type": "Double",  "unit": "bar",   "gen": _osc(2.4, 0.3, 60)},
    "ns=2;s=ConveyorSpeed":   {"type": "Double",  "unit": "m/s",   "gen": _osc(1.2, 0.1, 15)},
    "ns=2;s=Oven.Setpoint":   {"type": "Double",  "unit": "degC",  "gen": lambda _i: 220.0},
    "ns=2;s=Oven.Actual":     {"type": "Double",  "unit": "degC",  "gen": _osc(218.5, 1.5, 20)},
    "ns=2;s=PackerCount":     {"type": "Int32",   "unit": "count", "gen": lambda i: 1000 + i},
    "ns=2;s=PackerStatus":    {"type": "String",  "unit": None,    "gen": lambda i: ("RUN", "IDLE", "RUN")[i % 3]},
    "ns=2;s=Plant.Heartbeat": {"type": "Boolean", "unit": None,    "gen": lambda i: i % 2 == 0},
}


# -- subscription manager ----------------------------------------------------


@dataclass
class _Subscription:
    node_id: str
    interval_ms: int
    callback: Callable[[NodeValue], None]
    _thread: Optional[threading.Thread] = field(default=None, init=False, repr=False)
    _stop: threading.Event = field(default_factory=threading.Event, init=False, repr=False)

    def start(self, max_samples: int) -> None:
        """Run synchronously to a known number of samples — keeps the demo
        deterministic without needing an async loop."""
        delta = max(self.interval_ms / 1000.0, 0.0)
        node = _ADDRESS_SPACE.get(self.node_id)
        if node is None:
            raise OpcUaError(f"unknown node_id={self.node_id}")
        for i in range(max_samples):
            ts = int(time.time() * 1000)
            value = node["gen"](i)
            self.callback(
                NodeValue(
                    node_id=self.node_id,
                    value=value,
                    data_type=node["type"],
                    source_timestamp_ms=ts,
                    server_timestamp_ms=ts,
                )
            )
            if delta > 0:
                time.sleep(delta)
            if self._stop.is_set():
                return


# -- client ------------------------------------------------------------------


@dataclass
class OpcUaClient:
    """Minimal demo OPC UA client."""

    endpoint_url: str
    security_policy: str = "Basic256Sha256"
    username: Optional[str] = None
    password: Optional[str] = field(default=None, repr=False)
    application_uri: str = "urn:domain-explorer:stub-client"
    _connected: bool = field(default=False, init=False, repr=False)
    _counter: int = field(default=0, init=False, repr=False)

    def __post_init__(self) -> None:
        if self.security_policy not in _VALID_SECURITY_POLICIES:
            raise OpcUaError(
                f"unsupported security_policy={self.security_policy!r}; "
                f"expected one of {sorted(_VALID_SECURITY_POLICIES)}"
            )

    # --- lifecycle ---

    def connect(self) -> "OpcUaClient":
        if not self.endpoint_url.startswith(("opc.tcp://", "opc.https://")):
            raise OpcUaError(
                f"invalid endpoint_url={self.endpoint_url!r}; expected opc.tcp:// scheme"
            )
        self._connected = True
        return self

    def disconnect(self) -> None:
        self._connected = False

    def __enter__(self) -> "OpcUaClient":
        return self.connect()

    def __exit__(self, *exc: Any) -> None:
        self.disconnect()

    # --- public API ---

    def browse_namespace(self) -> List[Tuple[str, str, str]]:
        """Return ``[(node_id, data_type, unit)]`` for every node in the
        canned namespace. Mirrors asyncua's ``Node.get_children()``
        recursive walk."""
        if not self._connected:
            self.connect()
        return [
            (node_id, info["type"], info.get("unit") or "")
            for node_id, info in _ADDRESS_SPACE.items()
        ]

    def read_node(self, node_id: str) -> NodeValue:
        """Read a single node's current value. Mirrors ``Node.read_data_value()``."""
        if not self._connected:
            self.connect()
        info = _ADDRESS_SPACE.get(node_id)
        if info is None:
            raise OpcUaError(f"BadNodeIdUnknown: {node_id}")
        ts = int(time.time() * 1000)
        self._counter += 1
        return NodeValue(
            node_id=node_id,
            value=info["gen"](self._counter),
            data_type=info["type"],
            source_timestamp_ms=ts,
            server_timestamp_ms=ts,
        )

    def subscribe(
        self,
        node_id: str,
        interval_ms: int,
        callback: Callable[[NodeValue], None],
        max_samples: int = 5,
    ) -> _Subscription:
        """Create a monitored item on ``node_id`` that fires ``callback``
        every ``interval_ms``. The demo runs synchronously for
        ``max_samples`` then returns; production callers would let the
        subscription run indefinitely."""
        if not self._connected:
            self.connect()
        sub = _Subscription(node_id=node_id, interval_ms=interval_ms, callback=callback)
        sub.start(max_samples=max_samples)
        return sub
