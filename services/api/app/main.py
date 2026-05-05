"""FastAPI app exposing the metadata registry plus stub KG endpoints."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from metadata import (
    ConnectorPattern,
    KpiRegistryEntry,
    Registry,
    SourceSystemEntry,
    Subdomain,
    load_registry,
)
from pydantic import BaseModel

from .dq import router as dq_router

app = FastAPI(
    title="Domain Explorer API",
    version="0.1.0",
    description="Read-only access to the Domain Explorer metadata registry.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _data_root() -> Path:
    """Walk up from this file to find the repo root, then `data/`."""
    here = Path(__file__).resolve()
    for parent in here.parents:
        candidate = parent / "data"
        if candidate.is_dir():
            return candidate
    raise RuntimeError("Could not locate `data/` directory")


@lru_cache(maxsize=1)
def registry() -> Registry:
    return load_registry(_data_root())


class HealthResponse(BaseModel):
    status: str
    subdomains: int
    kpis: int


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    r = registry()
    return HealthResponse(
        status="ok", subdomains=len(r.subdomains), kpis=len(r.kpis)
    )


@app.get("/v1/subdomains", response_model=list[Subdomain])
def list_subdomains(vertical: str | None = None) -> list[Subdomain]:
    items = registry().subdomains
    if vertical:
        items = [s for s in items if s.vertical.value == vertical]
    return items


@app.get("/v1/subdomains/{sub_id}", response_model=Subdomain)
def get_subdomain(sub_id: str) -> Subdomain:
    item = next((s for s in registry().subdomains if s.id == sub_id), None)
    if item is None:
        raise HTTPException(status_code=404, detail="subdomain not found")
    return item


@app.get("/v1/kpis", response_model=list[KpiRegistryEntry])
def list_kpis(vertical: str | None = None) -> list[KpiRegistryEntry]:
    items = registry().kpis
    if vertical:
        items = [k for k in items if k.vertical.value == vertical]
    return items


@app.get("/v1/kpis/{kpi_id}", response_model=KpiRegistryEntry)
def get_kpi(kpi_id: str) -> KpiRegistryEntry:
    item = next((k for k in registry().kpis if k.id == kpi_id), None)
    if item is None:
        raise HTTPException(status_code=404, detail="kpi not found")
    return item


@app.get("/v1/source-systems", response_model=list[SourceSystemEntry])
def list_sources() -> list[SourceSystemEntry]:
    return registry().source_systems


@app.get("/v1/source-systems/{source_id}", response_model=SourceSystemEntry)
def get_source(source_id: str) -> SourceSystemEntry:
    item = next(
        (s for s in registry().source_systems if s.id == source_id), None
    )
    if item is None:
        raise HTTPException(status_code=404, detail="source not found")
    return item


@app.get("/v1/connectors", response_model=list[ConnectorPattern])
def list_connectors() -> list[ConnectorPattern]:
    return registry().connectors


# --- Stub KG endpoints ---------------------------------------------------


class KgQueryRequest(BaseModel):
    cypher: str


class KgQueryResponse(BaseModel):
    rows: list[dict[str, str]]
    note: str


@app.post("/v1/kg/query", response_model=KgQueryResponse)
def kg_query(req: KgQueryRequest) -> KgQueryResponse:
    """Stub — returns an empty result set with a note. Wire to Neo4j later."""
    return KgQueryResponse(
        rows=[],
        note="KG backend not yet wired. Requested cypher echoed: