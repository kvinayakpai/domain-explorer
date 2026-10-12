#!/usr/bin/env bash
# Rebuild viewer/index.html from the YAML/JSON under data/. Needs python3 with pyyaml.
set -euo pipefail
cd "$(dirname "$0")/.."
tmp="$(mktemp)"
python3 viewer/build_dataset.py . "$tmp"
python3 viewer/assemble.py "$tmp" viewer/index.html
rm -f "$tmp"
