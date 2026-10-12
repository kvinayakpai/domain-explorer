"""Emit one compact JSON dataset for the static viewer from the repo's data files.

Usage: python viewer/build_dataset.py <repo root> <output.json>
"""
import json
import pathlib
import subprocess
import sys

import yaml

REPO = pathlib.Path(sys.argv[1])
OUT = pathlib.Path(sys.argv[2])
D = REPO / "data"


def load(p):
    return yaml.safe_load((REPO / p).read_text(encoding="utf-8"))


TAGLINES = {
    "BFSI": "Payments, cards, lending, capital markets, AML, treasury.",
    "Insurance": "Underwriting, claims, policy admin, reinsurance, actuarial.",
    "Retail": "Stores, ecommerce, pricing & promotions, returns, last-mile, dark stores.",
    "RCG": "Pricing, supply chain, loyalty across consumer goods.",
    "CPG": "Demand planning, trade promotion management, brand marketing, retail execution.",
    "TTH": "Airlines, hotels, ride-share, rentals, ground ops.",
    "Manufacturing": "Shop floor, MES, BOM, supply chain visibility.",
    "LifeSciences": "Trials, pharmacovigilance, medical devices, supply chain.",
    "Healthcare": "EHR, revenue cycle, telehealth, imaging, engagement.",
    "Telecom": "Network ops, BSS/OSS, billing, churn, 5G slicing, QoE.",
    "Media": "Ad tech, programmatic, content metadata, SaaS metrics.",
    "Energy": "Grid, trading, EV charging, renewables, carbon accounting.",
    "Utilities": "Smart metering, outages, gas, water, asset health.",
    "PublicSector": "Benefits, court, tax, transit, emergency response.",
    "HiTech": "FinOps, telemetry, marketplaces, EDA, DevRel, yield.",
    "ProfessionalServices": "Time, billing, legal matters, audit, knowledge.",
    "CrossCutting": "Agentic commerce and other horizontal patterns spanning verticals.",
}
LABELS = {"LifeSciences": "Life Sciences", "PublicSector": "Public Sector", "HiTech": "High Tech",
          "ProfessionalServices": "Professional Services", "CrossCutting": "Cross-cutting"}

master = {k["id"]: k for k in load("data/kpis/master.yaml")["kpis"]}
sql = {s["kpi_id"]: {k: s.get(k) for k in ("threeNF", "vault", "dimensional", "notes") if s.get(k)}
       for s in load("data/kpis/sql.yaml")["kpis"]}
avail = {a["id"]: a for a in load("data/quality/data-availability.yaml")["subdomains"]}
dq_rules = load("data/quality/dq_rules.yaml")["rules"]
last = json.loads((D / "quality/last_run.json").read_text())
glossary = load("data/glossary/glossary.yaml")["terms"]
sources = load("data/source-systems/sources.yaml")
sources = sources.get("sources", sources)
connectors = load("data/connectors/connectors.yaml")
connectors = connectors.get("connectors", connectors)
synth = {p.parent.name for p in (REPO / "synthetic-data").glob("*/generate.py")}

dq_count = {}
for r in dq_rules:
    dq_count[r["subdomain"]] = dq_count.get(r["subdomain"], 0) + 1

gloss_by_sub = {}
for t in glossary:
    for s in t.get("related_subdomains") or []:
        gloss_by_sub.setdefault(s, []).append(t["name"])

subs = []
for p in sorted((D / "taxonomy").glob("*.yaml")):
    d = yaml.safe_load(p.read_text(encoding="utf-8"))
    dm = d.get("dataModel") or {}
    kpis = []
    for k in d.get("kpis") or []:
        m = master.get(k["id"], {})
        kpis.append({
            "id": k["id"], "name": k["name"], "formula": k.get("formula"), "unit": k.get("unit"),
            "dir": k.get("direction"), "def": m.get("definition"),
            "dec": k.get("decisionsSupported") or m.get("decisionsSupported") or [],
            "pers": m.get("related_personas") or [], "sql": k["id"] in sql,
        })
    ents = []
    for e in dm.get("entities") or []:
        ents.append({
            "n": e["name"], "d": e.get("description"), "keys": e.get("keys") or [],
            "a": [[a["name"], a.get("type"), 1 if a.get("isPrimaryKey") else 0, 1 if a.get("isForeignKey") else 0]
                  for a in e.get("attributes") or []],
            "r": [[r["to"], r["kind"], r.get("via")] for r in e.get("relationships") or []],
        })
    av = avail.get(d["id"], {})
    subs.append({
        "id": d["id"], "name": d["name"], "v": d["vertical"], "one": d["oneLiner"],
        "personas": d.get("personas") or [],
        "decisions": d.get("decisions") or [],
        "kpis": kpis, "ents": ents,
        "rels": [[r["from"], r["to"], r["kind"]] for r in dm.get("relationships") or []],
        "src": d.get("sourceSystems") or [],
        "con": d.get("connectors") or [],
        "ingest": [x if isinstance(x, str) else json.dumps(x) for x in d.get("ingestionChallenges") or []],
        "integ": [x if isinstance(x, str) else json.dumps(x) for x in d.get("integrationChallenges") or []],
        "std": d.get("standards") or [],
        "terms": d.get("glossaryTerms") or [],
        "gloss": gloss_by_sub.get(d["id"], []),
        "ddl": bool(d.get("dataModelArtifacts")),
        "synth": d["id"] in synth,
        "tier": av.get("tier"), "anchor": bool(av.get("anchor")),
        "cites": av.get("citations") or [],
        "dq": dq_count.get(d["id"], 0), "dqRun": last["by_subdomain"].get(d["id"]),
        "deep": bool(d.get("decisions") or d.get("ingestionChallenges")),
    })

commit = subprocess.run(["git", "-C", str(REPO), "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip()
out = {
    "commit": commit,
    "verticals": [{"id": v, "label": LABELS.get(v, v), "tag": TAGLINES[v]} for v in TAGLINES],
    "subs": subs, "kpiSql": sql,
    "glossary": [{"n": t["name"], "al": t.get("aliases") or [], "d": t.get("definition"),
                  "subs": t.get("related_subdomains") or [], "kpis": t.get("related_kpis") or [],
                  "steward": t.get("steward")} for t in glossary],
    "sources": sources, "connectors": connectors,
    "dqTotals": {k: last[k] for k in ("ran_at", "total_rules", "passed", "failed", "pending", "pass_rate")},
}
OUT.write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
print("subs", len(subs), "kpis", sum(len(s["kpis"]) for s in subs), "ents", sum(len(s["ents"]) for s in subs),
      "deep", sum(s["deep"] for s in subs), "synth", sum(s["synth"] for s in subs), "ddl", sum(s["ddl"] for s in subs),
      "glossary", len(glossary), "sources", len(sources), "connectors", len(connectors),
      "KB", OUT.stat().st_size // 1024)
