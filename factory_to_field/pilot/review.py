"""Review workflow for the identity-resolution queue.

The KG build links records across systems automatically when it is confident; the rest (today: three orphan
historian tags) go to `review_queue.json`. Here a data steward, signed in through the identity provider,
decides each item: link it to a canonical node, or dismiss it with a reason (for example a retired tag).
Decisions persist in SQLite with who decided, when the item was opened and how long the decision took, every
step goes to the audit log, and `apply()` rebuilds the graph with the decisions so the queue shrinks.

    python -m factory_to_field.pilot.review list
    python -m factory_to_field.pilot.review decide "PI|tags|PT0098" --dismiss "tag retired in 2023" --user p.kulkarni
    python -m factory_to_field.pilot.review decide "PI|tags|PT0190" --link pos:R2:41-P-412A --user p.kulkarni
    python -m factory_to_field.pilot.review apply
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import statistics
import threading
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .approvals import Verify
from .audit import AuditLog

ROOT = Path(__file__).resolve().parents[1] / "build"
DEFAULT_DB = ROOT / "review" / "decisions.sqlite"
REVIEWER_ROLE = "data_steward"

SCHEMA = """
create table if not exists decision (
    item_id     text primary key,
    verdict     text not null check (verdict in ('link', 'dismiss')),
    canon       text,
    reason      text,
    reviewer    text not null,
    subject     text not null,
    opened_at   text,
    decided_at  text not null,
    seconds     real
);
create table if not exists opened (item_id text primary key, subject text, opened_at text not null);
"""


def _now() -> datetime:
    return datetime.now(UTC)


class ReviewStore:
    def __init__(self, path: Path | str = DEFAULT_DB) -> None:
        if str(path) != ":memory:":
            Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.con = sqlite3.connect(str(path), check_same_thread=False)
        self.con.row_factory = sqlite3.Row
        self.con.executescript(SCHEMA)
        self._lock = threading.Lock()

    def queue(self, queue_path: Path) -> list[dict[str, Any]]:
        """The KG's open queue joined with the decisions taken so far."""
        items = json.loads(Path(queue_path).read_text()) if Path(queue_path).exists() else []
        done = {r["item_id"]: dict(r) for r in self.con.execute("select * from decision")}
        out = []
        for it in items:
            d = done.get(it["id"])
            out.append({**it, "status": "decided" if d else "open", "decision": d})
        # decisions whose items already left the queue (applied) stay visible
        known = {it["id"] for it in items}
        out += [{"id": k, "status": "applied", "decision": v} for k, v in done.items() if k not in known]
        return out

    def open(self, item_id: str, token: str, verify: Verify) -> None:
        claims = verify(token)
        with self._lock:
            self.con.execute("insert or ignore into opened values (?, ?, ?)", (item_id, claims.get("sub"), _now().isoformat(timespec="seconds")))
            self.con.commit()

    def decide(self, item_id: str, token: str, verify: Verify, audit: AuditLog, *, link: str | None = None,
               dismiss: str | None = None, valid_canon: set[str] | None = None) -> dict[str, Any]:
        claims = verify(token)
        if REVIEWER_ROLE not in claims.get("roles", []):
            audit.append(claims.get("name", "unknown"), None, "review_refused", item_id, {"needs": REVIEWER_ROLE})
            raise PermissionError(f"review decisions need the {REVIEWER_ROLE} role; {claims.get('name')} holds {', '.join(claims.get('roles', [])) or 'none'}")
        if bool(link) == bool(dismiss):
            raise ValueError("decide needs exactly one of link=<canonical id> or dismiss=<reason>")
        if link and valid_canon is not None and link not in valid_canon:
            raise ValueError(f"{link} is not a node in the knowledge graph")
        now = _now()
        with self._lock:
            row = self.con.execute("select opened_at from opened where item_id = ?", (item_id,)).fetchone()
            opened = row["opened_at"] if row else None
            secs = (now - datetime.fromisoformat(opened)).total_seconds() if opened else None
            self.con.execute("insert or replace into decision values (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                             (item_id, "link" if link else "dismiss", link, dismiss, claims["name"], claims["sub"], opened,
                              now.isoformat(timespec="seconds"), secs))
            self.con.commit()
        rec = {"item": item_id, "verdict": "link" if link else "dismiss", "canon": link, "reason": dismiss, "seconds": secs}
        audit.append(claims["name"], REVIEWER_ROLE, "review_decide", item_id, rec | {"sub": claims["sub"]})
        return rec

    def decisions_for_build(self) -> dict[str, str | None]:
        """item id -> canonical id (None = dismissed), the shape kg.build expects."""
        return {r["item_id"]: (r["canon"] if r["verdict"] == "link" else None) for r in self.con.execute("select * from decision")}

    def metrics(self, queue_path: Path) -> dict[str, Any]:
        q = self.queue(queue_path)
        secs = [r["seconds"] for r in self.con.execute("select seconds from decision where seconds is not null")]
        verdicts = [r["verdict"] for r in self.con.execute("select verdict from decision")]
        return {"open": sum(1 for x in q if x["status"] == "open"), "decided": len(verdicts),
                "linked": verdicts.count("link"), "dismissed": verdicts.count("dismiss"),
                "median_seconds_per_decision": statistics.median(secs) if secs else None}


def apply(store: ReviewStore, world: Path, out: Path, skip_shacl: bool = False) -> dict[str, Any]:
    """Rebuild the knowledge graph with the reviewers' decisions."""
    from ..kg.build import build_kg
    return build_kg(world, out, skip_shacl=skip_shacl, decisions=store.decisions_for_build())


def main() -> None:
    from ..agents.core import DEFAULT_KG, DEFAULT_WORLD
    from .idp import DIRECTORY, IdentityProvider

    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list")
    d = sub.add_parser("decide")
    d.add_argument("item")
    g = d.add_mutually_exclusive_group(required=True)
    g.add_argument("--link")
    g.add_argument("--dismiss")
    d.add_argument("--user", default="p.kulkarni")
    sub.add_parser("apply")
    a = ap.parse_args()
    kg_dir = Path(DEFAULT_KG).parent
    store, queue = ReviewStore(), kg_dir / "review_queue.json"
    if a.cmd == "list":
        for it in store.queue(queue):
            print(f"{it['status']:8} {it['id']:28} candidate={it.get('candidate')} conf={it.get('confidence')}  {it.get('evidence', '')}")
        print(json.dumps(store.metrics(queue)))
    elif a.cmd == "decide":
        idp = IdentityProvider()   # local demo sign-in; a pilot uses the company identity provider
        tok = idp.login(a.user, DIRECTORY[a.user].password)
        print(store.decide(a.item, tok, idp.verify, AuditLog(), link=a.link, dismiss=a.dismiss))
    else:
        m = apply(store, Path(DEFAULT_WORLD), kg_dir)
        print(f"review queue {m['review_queue']} | dismissed {m['review_dismissed']} | recall {m['resolution']['recall']} precision {m['resolution']['precision']}")


if __name__ == "__main__":
    main()
