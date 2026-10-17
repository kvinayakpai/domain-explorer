"""Builds ui/case_viewer.html: one self-contained page with the ten gold cases, their reports, audit trails and drafts.

    python -m factory_to_field.ui.build_ui
"""
from __future__ import annotations

import json
from pathlib import Path

from ..agents.gold import score

HERE = Path(__file__).resolve().parent


def main() -> None:
    r = score()
    data = {"checks": r["checks"], "passed": r["passed"], "cases": [{"id": c["case"], "title": c["title"], "ok": c["ok"], "checks": c["checks"], "problems": c["problems"], **c["detail"]} for c in r["cases"]]}
    html = (HERE / "case_viewer.template.html").read_text().replace("/*DATA*/null", json.dumps(data, default=str))
    (HERE / "case_viewer.html").write_text(html)
    print(f"wrote {HERE / 'case_viewer.html'} ({len(html) // 1024} KB), {r['passed']}/{r['checks']} checks")


if __name__ == "__main__":
    main()
