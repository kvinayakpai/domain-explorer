"""Query layer over the instance graph (pyoxigraph). All methods answer through SPARQL files in queries/."""
from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any

import pyoxigraph as ox

from .rdfutil import BASE, iri

Q = Path(__file__).resolve().parents[1] / "queries"
XSD = "http://www.w3.org/2001/XMLSchema#"


def term(v: Any) -> ox.Term:
    if isinstance(v, ox.NamedNode):
        return v
    if isinstance(v, date):
        return ox.Literal(v.isoformat(), datatype=ox.NamedNode(XSD + "date"))
    if isinstance(v, bool):
        return ox.Literal("true" if v else "false", datatype=ox.NamedNode(XSD + "boolean"))
    return ox.Literal(str(v))


def val(t: ox.Term | None) -> Any:
    if t is None:
        return None
    if isinstance(t, ox.NamedNode):
        s = t.value
        if not s.startswith(BASE):
            return s
        kind, _, rest = s[len(BASE):].partition("/")
        # position ids are kind:site:tag; every other id keeps any slash that is part of the serial (e.g. TF/21/56593)
        return f"{kind}:{rest.replace('/', ':')}" if kind == "pos" else f"{kind}:{rest}"
    if isinstance(t, ox.Literal):
        dt = t.datatype.value if t.datatype else ""
        if dt.endswith("#date"):
            return date.fromisoformat(t.value)
        if dt.endswith("#integer"):
            return int(t.value)
        if dt.endswith("#float") or dt.endswith("#double"):
            return float(t.value)
        if dt.endswith("#boolean"):
            return t.value == "true"
        return t.value
    return str(t)


class KG:
    def __init__(self, store_dir: Path | None = None, read_only: bool = False) -> None:
        self.store = ox.Store.read_only(str(store_dir)) if (store_dir and read_only) else ox.Store(str(store_dir) if store_dir else None)

    @classmethod
    def from_nquads(cls, path: Path, store_dir: Path | None = None) -> "KG":
        kg = cls(store_dir)
        kg.store.bulk_load(path=str(path), format=ox.RdfFormat.N_QUADS)
        return kg

    def sparql(self, text: str, **bindings) -> list[dict[str, Any]]:
        if bindings:
            # bind parameters with a VALUES block; terms are serialised (and escaped) by oxigraph itself
            names = " ".join(f"?{k}" for k in bindings)
            vals = " ".join(str(term(v)) for v in bindings.values())
            i = text.index("WHERE {") + len("WHERE {")
            text = text[:i] + f" VALUES ({names}) {{ ({vals}) }} " + text[i:]
        res = self.store.query(text, use_default_graph_as_union=True)
        vars_ = [v.value for v in res.variables]
        return [{v: val(sol[v]) if sol[v] is not None else None for v in vars_} for sol in res]

    def cq(self, name: str, **bindings) -> list[dict[str, Any]]:
        path = next(Q.glob(f"{name}*.rq"))
        return self.sparql(path.read_text(), **bindings)

    # ---- helpers the agents use -------------------------------------------------------------------
    def node(self, canon: str) -> ox.NamedNode:
        return ox.NamedNode(str(iri(canon)))

    def props(self, canon: str) -> dict[str, list[Any]]:
        out: dict[str, list[Any]] = {}
        for q in self.store.quads_for_pattern(self.node(canon), None, None, None):
            k = q.predicate.value.split("#")[-1]
            out.setdefault(k, []).append(val(q.object))
        return out

    def exists(self, canon: str) -> bool:
        return any(True for _ in self.store.quads_for_pattern(self.node(canon), None, None, None))

    def unit_at(self, position: str, on: date) -> dict | None:
        r = self.cq("cq01", pos=self.node(position), on=on)
        return r[0] if r else None

    def failures_at(self, position: str) -> list[dict]:
        return self.cq("cq02", pos=self.node(position))

    def unit_trace(self, unit: str) -> list[dict]:
        return self.cq("cq03", unit=self.node(unit))

    def position_history(self, position: str) -> list[dict]:
        rows = self.sparql("""PREFIX ftf: <https://domain-explorer.dev/ftf#>
            SELECT ?i ?unit ?serial ?from ?to WHERE { ?i a ftf:Installation ; ftf:position ?pos ; ftf:unit ?unit ; ftf:from_date ?from .
              OPTIONAL { ?i ftf:to_date ?to } ?unit ftf:serial ?serial } ORDER BY ?from""", pos=self.node(position))
        return rows

    def units_by_build(self, model_prefix: str, built_from: date, built_to: date, customer_label: str) -> list[dict]:
        return self.sparql("""PREFIX ftf: <https://domain-explorer.dev/ftf#>
            SELECT DISTINCT ?unit ?serial ?model ?built ?pos ?postag WHERE {
              ?unit a ftf:PhysicalEquipment ; ftf:serial ?serial ; ftf:model ?model ; ftf:built_on ?built .
              ?s a ftf:Shipment ; ftf:unit ?unit ; ftf:customer ?c . ?c ftf:label ?cl .
              FILTER (STRSTARTS(?model, ?prefix) && ?built >= ?from && ?built <= ?to && ?cl = ?cust)
              OPTIONAL { ?i a ftf:Installation ; ftf:unit ?unit ; ftf:position ?pos . FILTER NOT EXISTS { ?i ftf:to_date ?t } ?pos ftf:label ?postag }
            } ORDER BY ?built""", prefix=model_prefix, **{"from": built_from, "to": built_to}, cust=customer_label)


def run_life_groups(kg: "KG", cutoff: date) -> dict:
    """Run lives of ESP strings split by whether their seal section was built before or on/after the cutoff."""
    from ..analytics import km_median
    rows = kg.cq("cq07")
    groups: dict[str, list[tuple[int, bool]]] = {"before": [], "since": []}
    members: dict[str, list[dict]] = {"before": [], "since": []}
    for r in rows:
        g = "since" if r["sealbuilt"] >= cutoff else "before"
        groups[g].append((r["days"], r["state"] == "failed"))
        members[g].append(r)
    out = {}
    for g, runs in groups.items():
        out[g] = {"n": len(runs), "failed": sum(f for _, f in runs), "running": sum(not f for _, f in runs), "km_median_days": km_median(runs)}
    out["members"] = members
    return out
