# synthetic-data

Per-subdomain generators that produce the populated DuckDB the explorer reads
from. All generators are deterministic at a fixed seed.

## Wired generators

7 anchor subdomains have full generators:

- `payments/`              (BFSI)         — customers, accounts, payments,
                                            settlements, chargebacks, disputes,
                                            fraud_alerts, mcc_codes, +.
- `p_and_c_claims/`        (Insurance)    — policies, claims, coverages,
                                            adjusters, payouts.
- `merchandising/`         (Retail)       — stores, skus, orders, lineitems.
- `demand_planning/`       (CPG)          — products, plants, forecasts, sell-in.
- `hotel_revenue_management/` (TTH)       — properties, rates, reservations,
                                            cancellations.
- `mes_quality/`           (Manufacturing) — plants, lines, equipment, work
                                            orders, sensor readings, defects.
- `pharmacovigilance/`     (LifeSciences) — patients, drugs, cases, reactions,
                                            outcomes.

The remaining subdomains under `data/taxonomy/` ship as registry-only and pick
up generators incrementally.

## Strategy

1. **Reference dimensions** — small, hand-curated CSVs for things like MCC
   codes, ICD-10 fragments, GICS classifications, IATA codes. Committed for
   determinism.
2. **Entity generators** — Faker-based or domain-aware generators (e.g.
   merchants, taxpayers, hotels, plants) that produce dimension rows with
   stable surrogate keys.
3. **Event simulators** — stochastic processes (Poisson arrivals,
   AR(1)-with-seasonality demand, Hawkes for fraud bursts) that emit fact
   rows tied to the dimensions.
4. **Drift hooks** — explicit knobs (`--scenario growth | recession | fraud_spike`)
   that bend the signals so users can see the explorer light up.

## Output

Generators write CSV + Parquet sidecars to `synthetic-data/output/<subdomain>/`
and `generate_all.py` materialises everything into one DuckDB at the repo root
(`domain-explorer.duckdb`, one schema per subdomain).

## Tests

```bash
# Fast subset (`mes_quality`, `pharmacovigilance` smoke + common helpers + FK).
python -m pytest synthetic-data/tests/

# Full re-runs against all 7 generators (slow — ~2 min).
python -m pytest synthetic-data/tests/ -m slow
```

The fixture `_stub_write_table` autouse-monkeypatches the parquet/CSV writer
out so tests stay in-memory.
