"""Live console: runs the real agent against the system simulators and lets named people approve and release drafts.

    python -m factory_to_field.ui.live_app --port 8800

Nothing here is mocked: /api/run calls Agent.run over HTTP to the simulated PI, SAP PM, OSDU, PLM, MES and QMS with the
agent's own OAuth2 client-credentials token (read scope only). People sign in through the simulated identity provider
(/api/login); /api/approve and /api/release take that signed token, check the person's roles against the draft, and the
simulators check the same token again before accepting a write (the static release token is refused). Every approval,
release, refusal and review decision goes to a hash-chained audit log on disk (/api/audit). /api/review is the
identity-resolution review queue for data stewards, and /api/uns replays the plant's Unified Namespace over MQTT so
alarms open cases on their own.
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
from ..agents.sources import HttpSource, SourceError
from ..agents.verifier import verify
from ..kg.store import KG
from ..pilot import approvals
from ..pilot import idp as idp_mod
from ..pilot.audit import AuditLog
from ..pilot.connectors import ClientCredentials
from ..pilot.review import ReviewStore
from ..sim.server import serve_in_thread

HERE = Path(__file__).resolve().parent
LOCK = threading.Lock()
class App:
    def __init__(self, sim_url: str, idp_url: str, idp: idp_mod.IdentityProvider, audit: AuditLog | None = None,
                 review: ReviewStore | None = None) -> None:
        self.url, self.idp_url, self.idp = sim_url, idp_url, idp
        agent_cred = ClientCredentials(f"{idp_url}/oauth2/token", "ftf-agent", idp_mod.CLIENTS["ftf-agent"]["secret"])
        self.src = HttpSource(sim_url, token=agent_cred)          # the agent's own identity: read scope only
        self.writer = HttpSource(sim_url, token="none")            # used only with a person's token for releases
        self.agent = Agent(kg=KG(DEFAULT_KG, read_only=True), src=self.src)
        self.audit = audit or AuditLog()
        self.review = review or ReviewStore()
        self.kg_dir = Path(DEFAULT_KG).parent

    def state(self) -> dict:
        people = {u: {"name": p.name, "roles": list(p.roles)} for u, p in self.idp.directory.items()}
        return {"health": self.src.get("/sim/health"), "people": people,
                "cases": [{"id": g.case.id, "title": g.title, "question": g.case.question, "as_of": g.case.as_of} for g in GOLD]}

    def login(self, b: dict, token: str | None) -> dict:
        user = b.get("username", "")
        p = self.idp.directory.get(user)
        tok = self.idp.login(user, b.get("password") or (p.password if p else ""))   # demo passwords are filled in for the console
        self.audit.append(p.name if p else user, ",".join(p.roles) if p else None, "sign_in", user, {})
        return {"token": tok, "name": p.name if p else user, "roles": list(p.roles) if p else []}

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

    def approve(self, b: dict, token: str | None) -> dict:
        approvals.approve(tools.STORE, b["draft_id"], token or "", self.idp.verify, self.audit)
        return self.draft(b["draft_id"])

    def release(self, b: dict, token: str | None) -> dict:
        rec = approvals.release(tools.STORE, b["draft_id"], self.writer, token or "", self.idp.verify, self.audit)
        return {"record": rec, "draft": self.draft(b["draft_id"])}

    def audit_log(self) -> dict:
        ok, bad = self.audit.verify()
        return {"records": self.audit.records()[-50:], "count": len(self.audit.records()), "chain_ok": ok, "first_bad": bad}

    def review_queue(self) -> dict:
        q = self.kg_dir / "review_queue.json"
        return {"items": self.review.queue(q), "metrics": self.review.metrics(q)}

    def review_open(self, b: dict, token: str | None) -> dict:
        """A steward opened the queue: start the clock on each open item, for time per decision."""
        for item in b.get("item_ids", []):
            self.review.open(item, token or "", self.idp.verify)
        return {"opened": len(b.get("item_ids", []))}

    def review_decide(self, b: dict, token: str | None) -> dict:
        valid = None
        if b.get("link"):
            valid = {b["link"]} if self.agent.kg.props(b["link"]) else set()
        return self.review.decide(b["item_id"], token or "", self.idp.verify, self.audit, link=b.get("link") or None,
                                  dismiss=b.get("dismiss") or None, valid_canon=valid)

    def uns(self, b: dict, token: str | None) -> dict:
        from ..agents.core import DEFAULT_WORLD
        from ..pilot.uns import run_replay
        opened, sent = run_replay(self.agent, self.src, Path(DEFAULT_WORLD) / "uns_replay.jsonl")
        return {"sent": sent, "opened": [o.__dict__ | {"drafts": [self.draft(d) for d in o.drafts]} for o in opened]}

    def probe(self, b: dict, token: str | None = None) -> dict:
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
                if self.path == "/api/audit":
                    return self._send(200, app.audit_log())
                if self.path == "/api/review":
                    return self._send(200, app.review_queue())
            self._send(404, {"error": "not found"})

        def do_POST(self):
            b = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))) or b"{}")
            fn = {"/api/run": lambda b, t: app.run(b), "/api/login": app.login, "/api/approve": app.approve, "/api/release": app.release,
                  "/api/probe": app.probe, "/api/review/open": app.review_open, "/api/review/decide": app.review_decide, "/api/uns": app.uns}.get(self.path)
            if not fn:
                return self._send(404, {"error": "not found"})
            h = self.headers.get("Authorization", "")
            token = h[7:] if h.startswith("Bearer ") else None
            with LOCK:
                try:
                    self._send(200, fn(b, token))
                except PermissionError as e:
                    self._send(403, {"error": str(e)})
                except (SourceError, KeyError, ValueError) as e:
                    self._send(400, {"error": str(e)})
    return H


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8800)
    a = ap.parse_args()
    from ..demo import ensure_built
    ensure_built()
    _isrv, idp_url, idp = idp_mod.serve_in_thread()
    srv, url = serve_in_thread(verifier=idp_mod.JwksVerifier(idp_url, idp.issuer), require_identity=True)
    app = App(url, idp_url, idp)
    print(f"simulated plant systems at {url}\nidentity provider at {idp_url}\nlive console at http://127.0.0.1:{a.port}", flush=True)
    ThreadingHTTPServer(("127.0.0.1", a.port), make_handler(app)).serve_forever()


if __name__ == "__main__":
    main()
