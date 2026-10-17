"""End-to-end demo without any real system.

    python -m factory_to_field.demo            # builds the world and KG if missing, starts the simulators, runs CASE-1042 through them,
                                               # approves its drafts as the right named people and releases them to the simulated SAP and QMS

Prints each step, then what the simulated systems received.
"""
from __future__ import annotations

import json

from .agents import tools
from .agents.agent import Agent, Case
from .agents.core import DEFAULT_KG, DEFAULT_WORLD
from .agents.release import release
from .agents.sources import HttpSource
from .agents.verifier import verify
from .kg.store import KG
from .sim.server import serve_in_thread


def ensure_built() -> None:
    if not (DEFAULT_WORLD / "MANIFEST.json").exists():
        from .world.build import build as build_world
        build_world()
    if not DEFAULT_KG.exists():
        from .kg.build import build_kg
        build_kg(DEFAULT_WORLD, DEFAULT_KG.parent, skip_shacl=True)


def main() -> None:
    ensure_built()
    srv, url = serve_in_thread()
    print(f"simulated systems up at {url}: {json.dumps(HttpSource(url).get('/sim/health')['systems'])}")
    src = HttpSource(url)  # read-only credential
    agent = Agent(kg=KG(DEFAULT_KG, read_only=True), src=src)
    rep, s = agent.run(Case("CASE-1042", "Why is P-101A vibrating and what do we do?", "2026-10-16T07:30:00Z", trigger_tag="10P101A.VIB_DE"))
    print("\n" + rep.markdown() + f"\n\n({rep.tool_calls} tool calls through the simulated PI, SAP, PLM, MES, QMS; verifier problems: {verify(rep, s) or 'none'})")
    people = {"maintenance_planner": "A. Rao", "materials_planner": "S. Iyer", "quality_engineer": "M. Das"}
    admin = HttpSource(url, token="release")
    for did in rep.drafts:
        d = tools.STORE.items[did]
        tools.STORE.approve(did, people[d.approver_role], d.approver_role)
        rec = release(tools.STORE, did, admin)
        print(f"  {did} {d.kind}: approved by {d.decided_by} ({d.decided_role}) -> {rec['system']} {rec['id']}")
    try:
        src.post("/sap/opu/odata/sap/API_MAINTNOTIFICATION/MaintenanceNotification", {"x": 1})
    except Exception as e:  # the agent's own credential cannot write
        print("agent credential writing to SAP:", str(e)[:90])
    print("\nsimulated systems now hold", len(HttpSource(url).get("/sim/writes")["writes"]), "released records")
    srv.shutdown()


if __name__ == "__main__":
    main()
