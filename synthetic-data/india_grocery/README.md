# India grocery world

One fictional supermarket in Bengaluru (Store 014, Jayanagar), the warehouse that supplies it (Hoskote) and the dairy route that delivers its milk, simulated hourly from 4 May to 28 June 2026 at seed 42. The last four weeks are the story month used by the "Why Domain Matters" blog series.

The store runs the way many stores do: a min/max reorder rule on its own book stock, two shelf-refill rounds a day, pallets received by scanning the pallet label against the shipping notice, and a full count at the start and end of the month. The book drifts from the shelf through wrong-size scans, unrecorded damage and theft, misplaced cases and notice-based receiving.

The warehouse picks each night's store order before 04:00, confirming each line by scanning the slot's label, and sends one truck a morning for a 06:00-06:30 delivery slot. Its records (pick confirmations, shipping notice lines, pallet labels with the weight each notice implies, and its own stock corrections for the store's lines) are written alongside the store's.

## What is scripted and what is random

Background behaviour is random but seeded: customers, refill rounds that get skipped, damage, truck lateness, short shipments, misplaced cases. Six story incidents are scripted on top, the same approach as Factory to Field, and every one is listed in `answer_key.json` under `planted_events`:

| When | What | Domain |
|---|---|---|
| 9 June, first 5 kg delivery | The cases are put away behind the rice stack, in the wrong bay | Retail |
| 13 June, 10:00 | Staff restacking rice find them (unless found earlier) | Retail |
| 22 June, first 5 kg line | The DC picks it from the adjacent 1 kg slot; the label and shipping notice still say 5 kg | Logistics |
| 23 June, 14:20 | A DC picker finds the 1 kg slot 16 cases short; it is counted and adjusted down (only if nobody reported the wrong pallet) | Logistics |
| 25 June, 10:00 | The DC's weekly cycle count finds 16 extra cases of 5 kg and adjusts up (same condition) | Logistics |
| 26 June, 09:00 | The manager orders a count after complaints (only if the shelf is still frozen) | Retail |

## Interventions

`world.Scenario` changes only what the store and the warehouse do, never the customers: every random number is drawn up front, so all scenarios face the same shoppers, trucks and accidents, and May is identical in every scenario. Interventions start with the month-start count on 1 June.

- `alert_days`: flag an item whose sales fall under 25% of forecast for N days while the books show stock, and count it next morning.
- `backroom_discipline`: scan every case into a backroom bin at put-away (which also catches a wrong pallet) and keep fixed refill rounds.
- `milk_order_factor`: scale the toned-milk standing order.
- `dc_check`: `"pick_scan"` scans every case's barcode at pick, so the wrong-slot pick never happens; `"check_weigh"` weighs each pallet against the weight its shipping notice implies (2% tolerance), re-picks a flagged line and sends the truck 30 minutes late.
- `receiving`: `"case_scan"` scans every case at the store, books what arrived and raises a claim; the DC then corrects both slots the same morning.

`answer_key.otif` measures June's on-time-in-full four ways: the DC's own report (dispatch and pick confirmations), the scorecard per order line and per delivery (slot and goods receipt), and what was physically on the pallets.

## Realism checks

`realism.py` compares the world with published figures where they exist and labels the rest as assumptions. All 15 must pass; `realism_report.txt` is written next to the tables.

| Check | Benchmark |
|---|---|
| Warehouse items off the shelf 3-14% of open hours (world: 5.0%) | FMI, GMA and CIES (2002): 8.3% average |
| Most out-of-stock hours start in the store (world: 74%) | Same study: about 47% store ordering, 25% shelf management |
| Most item records wrong at the month-end count (world: 8 of 11) | DeHoratius and Raman (2008): 65% |
| Shopper responses to an empty shelf | Gruen, Corsten and Bharadwaj (2002), via Penn (SAEA) |
| Pouch milk sellable for the delivery day and the next | Amul Taaza: 48 hours from packing below 8 degC |
| Valid GTIN, GLN and SSCC check digits under prefix 29 | GS1 GSCN 23-006: 02 and 20-29 are for restricted circulation within a company or region |
| Every shipping-notice line has a matching pick confirmation and pallet record | Logic: the warehouse's documents agree with each other, whatever was on the pallet |

Prices are illustrative and not quotes for any real brand. Every parameter and its provenance is in `spec.PARAMS`.

## Run

    python synthetic-data/india_grocery/generate.py --seed 42                     # tables, answer key, realism report
    python synthetic-data/india_grocery/export_blog.py --out ../domain-series     # blog demo data and downloads
    pytest synthetic-data/tests/test_india_grocery.py

`generate_all.py` includes this world, so it also loads into DuckDB or Postgres with the other subdomains.
