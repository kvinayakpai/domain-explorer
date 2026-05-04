# synthetic-data

Stub package. Real generators land in `synthetic_data/` per subdomain.

## Strategy

We use a **layered** approach:

1. **Reference dimensions** — small, hand-curated CSVs for things like MCC
   codes, ICD-10 fragments, GICS classifications, IATA codes. These are
   committed to the repo so the generators are deterministic.
2. **Entity generators** — Faker-based or domain-aware generators (e.g.
   merchants, taxpayers, hotels, plants) that produce dimension rows with
   stable surrogate keys.
3. **Event simulators** — stochastic processes (Poisson arrivals,
   AR(1)-with-seasonality demand, hawkes for fraud bursts) that emit fact
   rows tied to the dimensions.
4. **Drift hooks** — explicit knobs (`--scenario growth | recession | fraud_spike`)
   that bend the signals so users can see the explorer light up.

## Output formats

Generators write Parquet to `synthetic_data/output/<subdomain>/` so dbt + DuckDB
can pick them up directly via `read_parquet`.

## Phasing

- Phase 1 (now): no generators yet — registry-driven UI is the priority.
- Phase 2: Payments + Merchandising generators (the easiest schemas).
- Phase 3: telemetry-heavy subdomains (MES/Quality, Smart Metering, Network
  Operations) which need a streaming-style emitter.
