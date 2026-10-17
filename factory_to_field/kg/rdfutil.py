from __future__ import annotations

from datetime import date, datetime
from urllib.parse import quote

from rdflib import BNode, Graph, Literal, Namespace, URIRef
from rdflib.namespace import RDF, XSD

FTF = Namespace("https://domain-explorer.dev/ftf#")
BASE = "https://domain-explorer.dev/ftf/id/"
PROV_GRAPH = URIRef("https://domain-explorer.dev/ftf/graph/provenance")
DATA_GRAPH = URIRef("https://domain-explorer.dev/ftf/graph/data")


def iri(canon: str) -> URIRef:
    return URIRef(BASE + quote(canon.replace(":", "/"), safe="/-_.~"))


def lit(v):
    if isinstance(v, bool):
        return Literal(v, datatype=XSD.boolean)
    if isinstance(v, datetime):
        return Literal(v.isoformat(), datatype=XSD.dateTime)
    if isinstance(v, date):
        return Literal(v.isoformat(), datatype=XSD.date)
    if isinstance(v, int):
        return Literal(v, datatype=XSD.integer)
    if isinstance(v, float):
        return Literal(v, datatype=XSD.float)
    return Literal(str(v))


class Builder:
    """Adds typed nodes that follow the generated LinkML shapes (id and label always present)."""

    def __init__(self) -> None:
        self.g = Graph()
        self.prov = Graph()
        self.g.bind("ftf", FTF)
        self.prov.bind("ftf", FTF)
        self.nodes: dict[str, str] = {}

    def node(self, canon: str, cls: str, label: str, **props) -> URIRef:
        u = iri(canon)
        if canon in self.nodes:
            # merging a second source record into the same node
            if self.nodes[canon] != cls and not (cls in ("PhysicalEquipment",) and self.nodes[canon] in ("ESPString", "ESPComponent")):
                pass
        else:
            self.nodes[canon] = cls
            self.g.add((u, RDF.type, FTF[cls]))
            self.g.add((u, FTF["id"], Literal(canon)))
            self.g.add((u, FTF["label"], Literal(label)))
        for k, v in props.items():
            self.set(u, k, v)
        return u

    def set(self, u: URIRef, k: str, v) -> None:
        if v is None or v == "" or v == []:
            return
        vals = v if isinstance(v, (list, tuple, set)) else [v]
        for x in vals:
            if x is None or x == "":
                continue
            self.g.add((u, FTF[k], x if isinstance(x, (URIRef, BNode, Literal)) else lit(x)))

    def ident(self, u: URIRef, system: str, world: str, kind: str, value: str) -> None:
        b = BNode()
        self.g.add((u, FTF["identifiers"], b))
        self.g.add((b, RDF.type, FTF["SourceIdentifier"]))
        for k, v in (("system", system), ("world", world), ("kind", kind), ("value", value)):
            self.g.add((b, FTF[k], Literal(v)))

    def assertion(self, subject: URIRef, predicate: str, obj: URIRef, method: str, conf: float, evidence: str) -> None:
        b = BNode()
        self.prov.add((b, RDF.type, FTF["LinkAssertion"]))
        for k, v in (("subject", str(subject)), ("predicate", predicate), ("object", str(obj)), ("method", method), ("evidence", evidence)):
            self.prov.add((b, FTF[k], Literal(v)))
        self.prov.add((b, FTF["confidence"], Literal(round(conf, 3), datatype=XSD.float)))
