"""Live console: runs the real agent against the system simulators and lets named people approve and release drafts.

    python -m factory_to_field.ui.live_app --port 8800

Nothing here is mocked: /api/run calls Agent.run over HTTP to the simulated PI, SAP PM, OSDU, PLM, MES and QMS using the
read-only credential; /api/approve uses the draft store's role check; /api/release posts to the simulated system with the release token.
"""
from __future__ import annotations

import argparse
import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from ..agents import tools
from ..agents.agent import Agent, Case
from ..agents.core import DEFAULT_KG
from ..agents.gold import GOLD, detail
from ..agents.release import release
from ..agents.sources import HttpSource, SourceError
from ..agents.verifier import verify
from ..kg.store import KG
from ..sim.server import serve_in_thread

HERE = Path(__file__).resolve().parent
LOCK = threading.Lock()
PEOPLE = {"maintenance_planner": "A. Rao", "materials_planner": "S. Iyer", "quality_engineer": "M. Das", "quality_manager": "R. Menon",
          "production_engineer": "K. Nair", "shift_supervisor": "T. Fernandes"}


class App:
    def __init__(self, sim_url: str) -> None:
        self.url = sim_url
        self.src = HttpSource(sim_url)
        self.admin = HttpSource(sim_url, token="release")
        self.agent = Agent(kg=KG(DEFAULT_KG, read_only=True), src=self.src)

    def state(self) -> dict:
        return {"health": self.src.get("/sim/health"), "people": PEOPLE,
                "cases": [{"id": g.case.id, "title": g.title, "question": g.case.question, "as_of": g.case.as_of} for g in GOLD]}

    def run(self, b: dict) -> dict:
        g = next((x for x in GOLD if x.case.id == b.get("case_id")), None)
        base = g.case if g else Case("ASK", b["question"], b.get("as_of") or "2026-10-17T06:00:00Z")
        case = Case(base.id, b.get("question") or base.question, base.as_of, base.position, base.trigger_tag, base.kind if g and not b.get("question_changed") else None)
        t = time.time()
        rep, s = self.agent.run(case)
        d = detail(rep, s)
        d.update(case=case.id, question=case.question, as_of=case.as_of, seconds=round(time.time() - t, 1), tool_calls=rep.tool_calls,
                 problems=verify(rep, s), drafts=[self.draft(x) for x in rep.drafts])
        return d

    def draft(self, did: str) -> dict:
        d = tools.STORE.items[did]
        return {"id": d.id, "kind": d.kind, "title": d.title, "role": d.approver_role, "status": d.status, "payload": d.payload, "rationale": d.rationale,
                "evidence": d.evidence, "history": d.history, "by": d.decided_by}

    def approve(self, b: dict) -> dict:
        tools.STORE.approve(b["draft_id"], b["person"], b["role"])
        return self.draft(b["draft_id"])

    def release(self, b: dict) -> dict:
        rec = release(tools.STORE, b["draft_id"], self.admin)
        return {"record": rec, "draft": self.draft(b["draft_id"])}

    def probe(self, b: dict) -> dict:
        paths = {"pi": "/piwebapi/points", "sap": "/sap/opu/odata/sap/API_MAINTNOTIFICATION/MaintenanceNotification"}
        try:
            self.src.post(paths[b["target"]], {"x": 1})
            return {"allowed": True}
        except SourceError as e:
            return {"allowed": False, "error": str(e)[:240]}


def make_handler(app: App):
    class H(BaseHTTPRequestHandler):
        def log_message(self, *a): pass

        def _send(self, code, body, ctype="application/json"):
            raw = body if isinstance(body, bytes) else json.dumps(body, default=str).encode()
            self.send_response(code); self.send_header("Content-Type", ctype); self.send_header("Content-Length", str(len(raw))); self.end_headers(); self.wfile.write(raw)

        def do_GET(self):
            if self.path in ("/", "/index.html"):
                return self._send(200, (HERE / "live_app.html").read_bytes(), "text/html; charset=utf-8")
            with LOCK:
                if self.path == "/api/state":
                    return self._send(200, app.state())
                if self.path == "/api/ledger":
                    return self._send(200, app.src.get("/sim/writes"))
            self._send(404, {"error": "not found"})

        def do_POST(self):
            b = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))) or b"{}")
            fn = {"/api/run": app.run, "/api/approve": app.approve, "/api/release": app.release, "/api/probe": app.probe}.get(self.path)
            if not fn:
                return self._send(404, {"error": "not found"})
            with LOCK:
                try:
                    self._send(200, fn(b))
                except (PermissionError, SourceError, KeyError, ValueError) as e:
                    self._send(400, {"error": str(e)})
    return H


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8800)
    a = ap.parse_args()
    from ..demo import ensure_built
    ensure_built()
    srv, url = serve_in_thread()
    app = App(url)
    print(f"simulated plant systems at {url}\nlive console at http://127.0.0.1:{a.port}", flush=True)
    ThreadingHTTPServer(("127.0.0.1", a.port), make_handler(app)).serve_forever()


if __name__ == "__main__":
    main()
