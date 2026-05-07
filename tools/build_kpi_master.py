#!/usr/bin/env python3
"""Build data/kpis/master.yaml + data/kpis/sql.yaml from data/taxonomy/*.yaml.

Aggregates every KPI mentioned across all 116 subdomains, dedupes by id, and
adds enrichment metadata (definition, subdomains[], related_personas[]).

Usage:
    python tools/build_kpi_master.py [--out data/kpis]
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import OrderedDict
from pathlib import Path
from typing import Any

import yaml


REPO = Path(__file__).resolve().parent.parent
TAXO_DIR = REPO / "data" / "taxonomy"
KPI_DIR = REPO / "data" / "kpis"


def _read_yaml(p: Path) -> dict[str, Any]:
    with p.open("r", encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


def _normalise(s: str) -> str:
    return (s or "").strip()


def _id_to_default_definition(name: str, formula: str, unit: str, sub: str) -> str:
    return f"{name} — used in {sub}. Computed as {formula}. Reported in {unit}."


def build_master(taxo_dir: Path) -> list[dict[str, Any]]:
    by_id: "OrderedDict[str, dict[str, Any]]" = OrderedDict()
    for f in sorted(taxo_dir.glob("*.yaml")):
        sub = _read_yaml(f)
        sub_id = sub.get("id", f.stem)
        sub_name = sub.get("name", sub_id)
        vert = sub.get("vertical")
        personas = [p.get("title") or p.get("name") for p in sub.get("personas", [])]
        for k in sub.get("kpis", []) or []:
            kid = _normalise(k.get("id", ""))
            if not kid:
                continue
            entry = by_id.get(kid)
            if entry is None:
                entry = {
                    "id": kid,
                    "name": _normalise(k.get("name", kid)),
                    "formula": _normalise(k.get("formula", "")),
                    "unit": _normalise(k.get("unit", "count")),
                    "direction": _normalise(k.get("direction", "higher_is_better")),
                    "definition": _id_to_default_definition(
                        k.get("name", kid),
                        k.get("formula", ""),
                        k.get("unit", "count"),
                        sub_name,
                    ),
                    "vertical": vert,
                    "subdomains": [],
                    "related_personas": [],
                    "decisionsSupported": list(k.get("decisionsSupported", []) or []),
                }
                by_id[kid] = entry
            if sub_id not in entry["subdomains"]:
                entry["subdomains"].append(sub_id)
            for p in personas:
                if p and p not in entry["related_personas"]:
                    entry["related_personas"].append(p)
            for d in k.get("decisionsSupported", []) or []:
                if d not in entry["decisionsSupported"]:
                    entry["decisionsSupported"].append(d)
    return list(by_id.values())


def build_sql_skeletons(master: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for k in master:
        out.append(
            {
                "kpi_id": k["id"],
                "threeNF": f"-- TODO: implement {k['id']} against operational schema\nSELECT NULL AS {k['id'].split('.')[-1]};",
                "vault":   f"-- TODO: implement {k['id']} against vault schema\nSELECT NULL AS {k['id'].split('.')[-1]};",
                "dimensional": f"-- TODO: implement {k['id']} against dimensional schema\nSELECT NULL AS {k['id'].split('.')[-1]};",
                "notes": "Auto-generated stub; replace with subdomain-specific SQL.",
            }
        )
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(KPI_DIR), help="Output directory (default: data/kpis)")
    ap.add_argument("--force-overwrite-sql", action="store_true",
                    help="Overwrite an existing sql.yaml even if it exists")
    args = ap.parse_args()
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    master = build_master(TAXO_DIR)
    print(f"Aggregated {len(master)} unique KPIs from {len(list(TAXO_DIR.glob('*.yaml')))} subdomains")
    master_path = out_dir / "master.yaml"
    with master_path.open("w", encoding="utf-8") as fh:
        yaml.safe_dump({"kpis": master}, fh, sort_keys=False, allow_unicode=True)
    print(f"Wrote {master_path}")

    sql_path = out_dir / "sql.yaml"
    if sql_path.exists() and not args.force_overwrite_sql:
        print(f"Skipping {sql_path} (already exists; pass --force-overwrite-sql to regenerate stubs)")
    else:
        with sql_path.open("w", encoding="utf-8") as fh:
            yaml.safe_dump({"kpis": build_sql_skeletons(master)}, fh, sort_keys=False, allow_unicode=True)
        print(f"Wrote {sql_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
