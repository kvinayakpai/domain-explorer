"""Unified Namespace replay over MQTT: alarms published on the wire open agent cases.

    python -m factory_to_field.pilot.uns            # replay the last six hours as fast as possible
    python -m factory_to_field.pilot.uns --speed 60 # one minute of plant time per second

The world renders `uns_replay.jsonl`: the last six hours of the two alarmed signals as Sparkplug-flavoured
JSON, on ISA-95 topics such as `aurelia/r1/cdu1/10-p-101a/vibration_de`. This module starts an MQTT broker
(amqtt), publishes the replay to it (paho-mqtt), and runs an alarm listener subscribed to `aurelia/#`. For
each topic the listener resolves the historian or SCADA tag from the UNS naming convention, reads the tag's
alarm limit from the PI Web API or the OPC UA gateway, and the first time a value goes above it, opens a
case for the agent with the alarm's own timestamp as the case clock. The agent then reads the plant systems
exactly as it does for the gold cases; it still cannot write to OT.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import queue
import socket
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import paho.mqtt.client as mqtt

ROOT_TOPIC = "aurelia"
# Part of the plant's UNS naming convention: the last topic level names the measured quantity, and the
# historian tag carries a fixed suffix for it. A pilot reads this from the namespace registry.
SUFFIX = {"vibration_de": "VIB_DE", "vibration_nde": "VIB_NDE", "bearing_temp": "BRG_T", "suction_pressure": "SUCT_P",
          "motor_temperature": "MTR_T", "intake_pressure": "PIP", "motor_current": "AMPS", "drive_frequency": "HZ"}


def tag_for_topic(topic: str) -> str | None:
    """`aurelia/r1/cdu1/10-p-101a/vibration_de` -> `10P101A.VIB_DE`; `aurelia/fa/p3/a-07-esp/motor_temperature` -> `A07_MTR_T`."""
    parts = topic.split("/")
    if len(parts) != 5 or parts[0] != ROOT_TOPIC or parts[4] not in SUFFIX:
        return None
    site, node, quantity = parts[1], parts[3], parts[4]
    if site == "fa":                                   # field SCADA: well id, underscore, suffix
        well = node.removesuffix("-esp").replace("-", "").upper()
        return f"{well}_{SUFFIX[quantity]}"
    return f"{node.replace('-', '').upper()}.{SUFFIX[quantity]}"   # refinery PI: tag without dashes, dot, suffix


def free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])


class BrokerThread:
    """An amqtt broker on its own event loop in a background thread."""

    def __init__(self, port: int | None = None) -> None:
        self.port = port or free_port()
        self._ready = threading.Event()
        self._loop: asyncio.AbstractEventLoop | None = None
        self._broker: Any = None
        self._error: BaseException | None = None

    def start(self) -> BrokerThread:
        threading.Thread(target=self._run, daemon=True).start()
        if not self._ready.wait(15):
            raise RuntimeError("MQTT broker did not start")
        if self._error:
            raise RuntimeError(f"MQTT broker failed: {self._error}")
        return self

    def _run(self) -> None:
        from amqtt.broker import Broker
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        cfg = {"listeners": {"default": {"type": "tcp", "bind": f"127.0.0.1:{self.port}"}},
               "plugins": {"amqtt.plugins.authentication.AnonymousAuthPlugin": {"allow_anonymous": True}}}
        try:
            self._broker = Broker(cfg, loop=self._loop)
            self._loop.run_until_complete(self._broker.start())
        except BaseException as e:   # surface start-up errors to the caller
            self._error = e
            self._ready.set()
            return
        self._ready.set()
        self._loop.run_forever()

    def stop(self) -> None:
        if self._loop and self._broker:
            asyncio.run_coroutine_threadsafe(self._broker.shutdown(), self._loop).result(10)
            self._loop.call_soon_threadsafe(self._loop.stop)


def _client(name: str) -> mqtt.Client:
    return mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=f"{name}-{int(time.time() * 1000) % 100000}")


@dataclass
class Opened:
    topic: str
    tag: str
    at: str
    value: float
    limit: float
    case_id: str
    summary: str = ""
    answer: dict[str, Any] = field(default_factory=dict)
    drafts: list[str] = field(default_factory=list)
    tool_calls: int = 0


class AlarmListener:
    """Subscribes to the namespace and turns the first alarm on each topic into an agent case."""

    def __init__(self, port: int, agent: Any, src: Any) -> None:
        self.agent, self.src = agent, src
        self.inbox: queue.Queue[dict[str, Any]] = queue.Queue()
        self.limits: dict[str, float | None] = {}
        self.opened: dict[str, Opened] = {}
        self.messages = 0
        self.c = _client("ftf-alarm-listener")
        self.c.on_message = lambda c, u, m: self.inbox.put({"topic": m.topic, **json.loads(m.payload)})
        self.c.on_connect = lambda c, u, f, rc, p: c.subscribe(f"{ROOT_TOPIC}/#", qos=1)
        self.c.connect("127.0.0.1", port)
        self.c.loop_start()

    def _limit(self, tag: str) -> float | None:
        if tag not in self.limits:
            p = self.src.point(tag)
            self.limits[tag] = float(p["alarm_high"]) if p and p.get("alarm_high") is not None else None
        return self.limits[tag]

    def handle(self, msg: dict[str, Any]) -> Opened | None:
        from ..agents.agent import Case
        self.messages += 1
        topic, value = msg["topic"], float(msg["value"])
        if topic in self.opened or msg.get("quality") != "Good":
            return None
        tag = tag_for_topic(topic)
        limit = self._limit(tag) if tag else None
        if tag is None or limit is None or value <= limit:
            return None
        case = Case(f"UNS-{len(self.opened) + 1:03d}",
                    f"Alarm on {tag}: {value} {msg.get('unit', '')} is above its high limit of {limit} at {msg['ts']}. What is wrong and what should we do?",
                    msg["ts"], trigger_tag=tag)
        rep, _s = self.agent.run(case)
        op = Opened(topic, tag, msg["ts"], value, limit, case.id, rep.summary, dict(rep.answer), list(rep.drafts), rep.tool_calls)
        self.opened[topic] = op
        return op

    def drain(self, idle_s: float = 1.0) -> None:
        """Process messages until none has arrived for `idle_s` seconds."""
        while True:
            try:
                self.handle(self.inbox.get(timeout=idle_s))
            except queue.Empty:
                return

    def close(self) -> None:
        self.c.loop_stop()
        self.c.disconnect()


def publish(port: int, replay: Path, speed: float = 0.0) -> int:
    """Publish the replay file; speed 0 means as fast as possible, otherwise plant seconds per wall second."""
    pub = _client("ftf-uns-replay")
    pub.connect("127.0.0.1", port)
    pub.loop_start()
    lines = [json.loads(x) for x in replay.read_text().splitlines() if x.strip()]
    prev = None
    for rec in lines:
        ts = time.mktime(time.strptime(rec["ts"][:19], "%Y-%m-%dT%H:%M:%S"))
        if speed and prev is not None:
            time.sleep(max(0.0, (ts - prev) / speed))
        prev = ts
        payload = {k: v for k, v in rec.items() if k != "topic"}
        pub.publish(rec["topic"], json.dumps(payload), qos=1).wait_for_publish(5)
    pub.loop_stop()
    pub.disconnect()
    return len(lines)


def run_replay(agent: Any, src: Any, replay: Path, speed: float = 0.0) -> tuple[list[Opened], int]:
    broker = BrokerThread().start()
    try:
        listener = AlarmListener(broker.port, agent, src)
        time.sleep(0.3)                        # let the subscription land before the first publish
        sent = publish(broker.port, replay, speed)
        listener.drain(idle_s=1.5)
        listener.close()
        return list(listener.opened.values()), sent
    finally:
        broker.stop()


def main() -> None:
    from ..agents.agent import Agent
    from ..agents.core import DEFAULT_KG, DEFAULT_WORLD
    from ..agents.sources import HttpSource
    from ..demo import ensure_built
    from ..kg.store import KG
    from ..sim.server import serve_in_thread

    ap = argparse.ArgumentParser()
    ap.add_argument("--speed", type=float, default=0.0)
    a = ap.parse_args()
    ensure_built()
    _srv, url = serve_in_thread()
    src = HttpSource(url)
    agent = Agent(kg=KG(DEFAULT_KG, read_only=True), src=src)
    opened, sent = run_replay(agent, src, Path(DEFAULT_WORLD) / "uns_replay.jsonl", a.speed)
    print(f"replayed {sent} UNS messages; {len(opened)} alarms opened cases")
    for o in opened:
        print(f"  {o.at}  {o.tag} {o.value} > {o.limit}  ->  {o.case_id}: {o.summary}  ({o.tool_calls} tool calls, drafts {', '.join(o.drafts) or 'none'})")


if __name__ == "__main__":
    main()
