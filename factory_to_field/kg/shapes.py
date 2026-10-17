"""SHACL gate: validate the instance graph against the shapes generated from the LinkML schema."""
from __future__ import annotations

from pathlib import Path

from pyshacl import validate
from rdflib import Graph

GEN = Path(__file__).resolve().parents[1] / "ontology" / "generated"


def validate_graph(data: Graph) -> tuple[bool, str, Graph]:
    shapes = Graph().parse(GEN / "ftf.shacl.ttl")
    onto = Graph().parse(GEN / "ftf.owl.ttl")
    conforms, rep_graph, rep_text = validate(data, shacl_graph=shapes, ont_graph=onto, inference="rdfs", abort_on_first=False, allow_warnings=True)
    return bool(conforms), rep_text, rep_graph
