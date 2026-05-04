# screenshots/

Captured against `next start` running `apps/explorer-web` with the populated
`domain-explorer.duckdb` at the repo root.

- `desktop/` — 1280×900, full page, DPR 1
- `mobile/` — 390×844, full page, DPR 2 (iPhone-class)

Re-capture:

```
# from the repo root, with the explorer running on http://127.0.0.1:3000
node screenshots/shoot.js                 # writes to ./screenshots/
node screenshots/shoot.js /custom/path    # write elsewhere
```

See `../NOTES.md` for the Playwright + Chromium pins that work inside the
sandboxed CI environment.
