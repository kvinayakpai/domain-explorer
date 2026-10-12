# Static viewer

`index.html` is a single self-contained page (data embedded, no server, no build step to open it).
Open it in a browser, or serve the repo with GitHub Pages and point at `viewer/`.

It reads from `data/` at build time: the taxonomy (one file per subdomain), KPI master and SQL specs,
glossary, source systems, connectors and data-quality results.

Rebuild after changing any data file:

```
bash viewer/build.sh
```

Layout: `src/head.html` (styles), `src/body.html` (markup and logic), `build_dataset.py` (data to JSON),
`assemble.py` (inline the JSON into one page).
