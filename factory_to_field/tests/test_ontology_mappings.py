"""Every ontology class has an entry in ontology/mappings.yaml, and the file stays honest about its status."""
from pathlib import Path

import yaml

ONT = Path(__file__).resolve().parents[1] / "ontology"


def test_every_class_is_mapped_or_explained():
    classes = set()
    for f in ONT.glob("*.yaml"):
        if f.name == "mappings.yaml":
            continue
        classes |= set(yaml.safe_load(f.read_text()).get("classes") or {})
    m = yaml.safe_load((ONT / "mappings.yaml").read_text())
    assert m["status"] == "draft-unverified"
    assert set(m["classes"]) == classes and len(classes) == 41    # 36 pump-world classes plus 5 fixed-equipment classes
    for name, e in m["classes"].items():
        has = any(isinstance(v, dict) and "term" in v for v in e.values())
        assert has or e.get("note"), f"{name} has neither a mapping nor a stated reason it has none"
        for std, v in e.items():
            if isinstance(v, dict):
                assert v["relation"] in {"exact", "close", "broad", "narrow", "related", "none"} and v["confidence"] in {"high", "medium", "low"}
