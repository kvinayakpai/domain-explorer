# Static viewer

`viewer.html` (repo root) is a single self-contained page: data embedded, no server, no build step to open it.
Open it in a browser, or serve the repo with GitHub Pages. The root `index.html` redirects to it.

Views: Atlas (treemap, verticals, subdomain dossiers with KPI SQL and entity diagrams), Map (force graph of shared
systems, personas and terms), Ask (answers assembled only from the data files and `data/canned-answers.json`),
Lineage (KPI to personas, decisions, SQL tables and systems), and KPI, People, Systems and Glossary lenses.

It reads from `data/` at build time: the taxonomy (one file per subdomain), KPI master and SQL specs, glossary,
source systems, connectors, data-quality results and the prepared answers.

Rebuild after changing any data file:

```
bash viewer/build.sh
```

Layout: `src/head.html` (styles), `src/body.html` (markup and logic), `build_dataset.py` (data to JSON),
`assemble.py` (inline the JSON into one page).
