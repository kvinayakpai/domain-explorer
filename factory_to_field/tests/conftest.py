from __future__ import annotations

import json
from pathlib import Path

import pytest
from factory_to_field.world.build import build


@pytest.fixture(scope="session")
def world_dir(tmp_path_factory) -> Path:
    out = tmp_path_factory.mktemp("world")
    build(out)
    return out


@pytest.fixture(scope="session")
def world(world_dir):
    # the in-memory world is rebuilt (cheap) so tests can compare rendered files with the truth
    from factory_to_field.world.build import make_world
    return make_world()


@pytest.fixture(scope="session")
def key(world_dir) -> dict:
    return json.loads((world_dir / "answer_key.json").read_text())


from factory_to_field.kg.build import build_kg
from factory_to_field.kg.store import KG


@pytest.fixture(scope="session")
def kg_dir(world_dir, tmp_path_factory):
    out = tmp_path_factory.mktemp("kg")
    m = build_kg(world_dir, out)
    (out / "_m.json").write_text(json.dumps(m))
    return out


@pytest.fixture(scope="session")
def kg(kg_dir) -> KG:
    return KG(kg_dir / "store")


@pytest.fixture(scope="session")
def metrics(kg_dir) -> dict:
    return json.loads((kg_dir / "metrics.json").read_text())


