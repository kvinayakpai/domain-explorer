# `@domain-explorer/init` — Customer Accelerator CLI

Produce a branded, vertical-filtered clone of [Domain Explorer](../../README.md)
in **~30 seconds**. Built for the closing demo moment in a sales motion: enter
a customer name, watch the spinner, hand them a working repo.

## Quick start

```bash
npx @domain-explorer/init acme-bank \
    --vertical=bfsi \
    --cloud=snowflake \
    --persona=cdo
```

That generates `./acme-bank-domain-explorer/` containing:

- only the BFSI taxonomy YAMLs (the others are deleted),
- root + `apps/explorer-web` `package.json` renamed to `acme-bank-*`,
- README, hero band, layout title, and `.env.example` rebranded to "Acme Bank",
- `modeling/dbt/profiles-snowflake.yml` ready for credentials,
- `apps/explorer-web/lib/customer-defaults.json` pinning CDO as the assistant's default persona,
- a fresh `git init -b main` with one bootstrap commit.

## Flags

| Flag | Default | Notes |
| ---- | ------- | ----- |
| `<customer>` (positional, required) | — | Slug, 3-30 chars, alphanumeric + hyphens. The CLI derives a friendly label automatically (`acme-bank` → "Acme Bank"). |
| `--vertical=<slug>` (required) | — | One of: `bfsi`, `insurance`, `retail`, `rcg`, `cpg`, `tth`, `manufacturing`, `lifesciences`, `healthcare`, `telecom`, `media`, `energy`, `utilities`, `publicsector`, `hitech`, `professionalservices`. |
| `--cloud=<slug>` | `duckdb` | One of `duckdb`, `snowflake`, `databricks`, `bigquery`, `postgres`. |
| `--persona=<id>` | — | Optional. Common ids: `cdo`, `cto`, `head-of-payments`, `head-of-claims`, `vp-analytics`. Unknown ids are accepted but won't pre-populate the assistant. |
| `--output-dir=<path>` | `./<customer>-domain-explorer` | Where to write the clone. Must be empty or non-existent. |
| `--source-repo=<path>` | `$DOMAIN_EXPLORER_REPO` or `.` | Path to the source Domain Explorer checkout. |
| `--logo=<path>` | — | Optional `.png`/`.svg` to copy into `apps/explorer-web/public/customer-logo.*`. |
| `--tagline="…"` | — | Replaces the hero subtitle. |
| `--dry-run` | off | Walk the tree and print the plan without writing anything. |
| `--no-git` | off | Skip the `git init` + first commit at the end. |
| `--quiet` | off | Suppress the banner, animation, and summary box. |

## How it works

The flow is nine independent steps in `src/steps/`:

1. **`01-validate.js`** — checks the customer slug, vertical, cloud, persona; resolves defaults; reads the source `package.json` to confirm we're pointed at a Domain Explorer checkout.
2. **`02-clone.js`** — copies the source tree using `fs-extra`, skipping `node_modules`, `.git`, `.next`, `*.duckdb`, and `synthetic-data/output`. Reports a running file count to the spinner.
3. **`03-filter-subdomains.js`** — deletes every `data/taxonomy/*.yaml` whose `vertical:` field doesn't match the chosen vertical. Filters `data/kpis/kpis.yaml` to the same vertical.
4. **`04-rebrand.js`** — string-replaces the customer name into root + app `package.json`, README, hero badge, layout metadata, footer, and `.env.example`. Drops a `customer.json` marker. Optionally copies the logo.
5. **`05-cloud-config.js`** — writes a cloud-specific `profiles-*.yml` for dbt, plus a `next.config.<cloud>.mjs` snippet for Snowflake. Appends env-var stubs to `.env.example`.
6. **`06-persona-default.js`** — writes `apps/explorer-web/lib/customer-defaults.json` (and a small `.ts` re-export) that the assistant page can read at render time.
7. **`07-rename-app.js`** — patches root `package.json` `scripts` so that `pnpm --filter explorer-web …` is rewritten to the new package name.
8. **`08-init-git.js`** — `git init -b main && git add -A && git commit`. Sets a local `user.name`/`user.email` so the commit doesn't fail on machines without a global git identity. Falls back gracefully if git isn't on PATH.
9. **`09-print-summary.js`** — the closing box: where the clone landed, how to start it.

Each step is wrapped by `runStep()` (see `src/utils/spinner.js`) which:

- shows an `ora` spinner during the work,
- flips to a green `✓` on success or red `✗` on failure,
- emits a per-second heartbeat once a step exceeds 5 seconds, so the demo audience never thinks the CLI hung.

## Demo path

For prospect demos the SE shouldn't have to type. The repo root ships
[`demo-init.bat`](../../demo-init.bat) which runs the CLI with sensible
defaults and writes to `C:\Claude\demo-output`.

## Programmatic usage

```js
import { init } from "@domain-explorer/init";

const result = await init({
  customer: "acme-bank",
  vertical: "bfsi",
  cloud: "snowflake",
  persona: "cdo",
  sourceRepo: "/path/to/domain-explorer",
  outputDir: "/tmp/acme-bank-clone",
  quiet: true,
});

if (result.exitCode === 0) {
  console.log(`Cloned ${result.summary.fileCount} files in ${result.summary.elapsedMs}ms.`);
}
```

The `summary` object includes file count, kept/dropped subdomain counts,
rebranded file count, cloud config files written, and total elapsed time.

## Tests

```bash
pnpm --filter @domain-explorer/init test
```

The suite covers validation (good + bad inputs), the subdomain filter, the
rebrand string-replace logic, and one end-to-end smoke that runs `init()`
against a tiny synthetic source tree. Total: 10 tests.

## Troubleshooting

| Symptom | Fix |
| ------- | --- |
| `Source repo not found` | Pass `--source-repo=/path/to/domain-explorer` or set `DOMAIN_EXPLORER_REPO`. |
| `Output directory is not empty` | Choose a fresh `--output-dir` or remove the existing one. |
| `Unknown vertical` | Use one of the slugs in the table above (case-insensitive). |
| Git commit didn't happen | The CLI reports `Skipping git init` if git isn't on PATH or you passed `--no-git`. The clone is still complete. |
| Step exceeds 30s | Source tree is unusually large (e.g. cached `synthetic-data/output`). Add the offender to `IGNORE_DIRS` in `src/steps/02-clone.js`. |

## Contributing

The CLI lives in this workspace package and is invoked via `pnpm --filter
@domain-explorer/init …`. The flow is intentionally simple: each step is a
pure async function on a shared `context` object — no class hierarchy, no
hidden state. To add a step, drop a new file in `src/steps/` and wire it
into `src/index.js`.

## Constraints

- We do **not** copy `domain-explorer.duckdb` or `synthetic-data/output/` —
  the customer regenerates those with `pnpm dbt:build`.
- We do **not** modify the source repo at all. Clones are write-only.
- We do **not** push the new clone to a remote — that's a deliberate manual
  step the SE takes after their demo.
