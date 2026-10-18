"""Generate OWL, SHACL, Pydantic, TypeScript and a JSON-LD context from the LinkML modules.

usage: python -m factory_to_field.ontology.build [--check]
  --check   fail if the committed files in ontology/generated differ from a fresh build
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "generated"
SCHEMA = HERE / "ftf.yaml"
BIN = Path(sys.executable).parent

TARGETS = {
    "ftf.owl.ttl": ["gen-owl", "--format", "ttl"],
    "ftf.shacl.ttl": ["gen-shacl", "--closed"],
    "models.py": ["gen-pydantic"],
    "types.ts": ["gen-typescript"],
    "ftf.context.jsonld": ["gen-jsonld-context"],
}


def render() -> dict[str, str]:
    out = {}
    for name, cmd in TARGETS.items():
        exe = BIN / cmd[0]
        r = subprocess.run([str(exe), *cmd[1:], str(SCHEMA)], capture_output=True, text=True)
        if r.returncode:
            raise SystemExit(f"{cmd[0]} failed:\n{r.stderr[-2000:]}")
        out[name] = r.stdout
    return out


def main() -> int:
    check = "--check" in sys.argv
    fresh = render()
    OUT.mkdir(exist_ok=True)
    stale = []
    for name, text in fresh.items():
        p = OUT / name
        if check:
            if not p.exists() or p.read_text() != text:
                stale.append(name)
        else:
            p.write_text(text)
            print(f"wrote {p.relative_to(HERE.parent)} ({len(text) / 1000:.0f} kB)")
    if stale:
        print("stale generated files:", ", ".join(stale))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
