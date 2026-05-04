# ADR 0001 — Stack choices for Domain Explorer

Status: Accepted
Date: 2026-05-04

## Context

We need a monorepo that hosts (a) a metadata-driven web UI that humans can
browse and (b) a data layer that downstream pipelines can plug into. The data
in scope spans 14 verticals and ~100+ subdomains, and we want adding a new
subdomain to be a YAML PR — no per-page code.

## Decision

- **Monorepo layout** — pnpm workspaces for JS, uv workspace for Python.
  Both ecosystems import from `packages/metadata` so the schema lives once.
- **UI** — Next.js 14 App Router with TS strict and shadcn/ui. App Router
  lets every subdomain page be a server component reading from the typed
  registry, which keeps the bundle small and the UX fast on mobile.
- **API** — FastAPI service exposing the same registry over HTTP. Same
  Pydantic v2 models that power validation power the response shapes.
- **Schema** — Zod (TS) + Pydantic v2 (Py) duplicated by hand (mirrored
  shapes). We considered codegen from a single source (e.g. JSON Schema)
  but the duplication cost is small and the dev ergonomics of native
  types in each language outweigh the maintenance overhead at this scale.
- **Modeling** — dbt-core with a DuckDB profile so contributors don't need
  cloud warehouse access to run the modeling layer locally. DDL for 3NF /
  Vault / dim is hand-authored alongside dbt models for documentation.
- **KG** — start with OWL/Turtle for the ontology, openCypher for queries.
  Defer choice of triplestore vs labeled property graph until we know what
  reasoning we actually need.
- **Synthetic data** — Python generators with a layered strategy
  (dimensions → entities → events → drift), emitting Parquet so DuckDB +
  dbt can read it directly.

## Consequences

- Two schema languages to keep in sync — tested via fixture YAMLs that
  must round-trip cleanly through both validators.
- The UI does no client-side data fetching for the registry — pages are
  built from server-side YAML reads. Adding a subdomain is a single PR
  that touches `data/taxonomy/`.
- Operating in a monorepo with two package managers (pnpm + uv) requires
  some onboarding documentation. CI runs both lanes in parallel.

## Alternatives considered

- **Single language stack** — Pure TS or pure Python would simplify the
  schema story but block one of the two consumer types we expect (web vs
  data pipelines). Not worth it.
- **Headless CMS for the registry** — Adds operational surface area for a
  feature whose reads are static. The YAML-in-git approach gives us
  versioning and code review for free.
