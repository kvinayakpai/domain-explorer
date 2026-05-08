// Step 3: keep only the taxonomy YAMLs that match the chosen vertical.
// We also rewrite the cross-vertical KPI master to drop entries from other
// verticals (so the KPI library page doesn't show 200+ irrelevant rows in a
// customer demo).
//
// We do NOT touch the synthetic-data generators or modeling/dbt models — those
// already work per-subdomain via dbt selectors. The customer can regenerate
// data with `pnpm dbt:build` once they install.

import path from "node:path";
import fs from "node:fs";
import fse from "fs-extra";

/**
 * Detect a vertical line at the top of a taxonomy YAML.
 * Files start with:
 *   id: <id>
 *   name: <name>
 *   vertical: <Canonical>
 */
function readVertical(filePath) {
  // Read just the first ~10 lines — vertical: is on line 3 in every file.
  let text;
  try {
    text = fs.readFileSync(filePath, "utf8");
  } catch {
    return null;
  }
  const head = text.split(/\r?\n/, 12).join("\n");
  const m = head.match(/^vertical:\s*(\S.*)$/m);
  if (!m) return null;
  return m[1].trim();
}

/** Rewrite kpis/kpis.yaml to keep only entries with the chosen vertical. */
function filterKpiMaster(kpiPath, canonicalVertical) {
  if (!fs.existsSync(kpiPath)) return { kept: 0, dropped: 0 };
  const text = fs.readFileSync(kpiPath, "utf8");
  const lines = text.split(/\r?\n/);
  const out = [];
  let kept = 0;
  let dropped = 0;
  for (const line of lines) {
    // Each KPI lives on a single `- { ... vertical: X ... }` line. Comments and
    // header lines we leave alone.
    if (/^\s*-\s*\{.*vertical:\s*[A-Za-z]+\b/.test(line)) {
      const vMatch = line.match(/vertical:\s*([A-Za-z]+)/);
      if (vMatch && vMatch[1] !== canonicalVertical) {
        dropped += 1;
        continue;
      }
      kept += 1;
    }
    out.push(line);
  }
  fs.writeFileSync(kpiPath, out.join("\n"), "utf8");
  return { kept, dropped };
}

export async function filterSubdomains(ctx) {
  const { outputDir, vertical, dryRun } = ctx;
  const taxonomyDir = path.join(outputDir, "data", "taxonomy");
  if (!fs.existsSync(taxonomyDir)) {
    // Nothing to do (e.g. running against a partial repo in tests).
    return { kept: 0, dropped: 0, kpisKept: 0, kpisDropped: 0 };
  }

  const entries = fs.readdirSync(taxonomyDir).filter((f) => f.endsWith(".yaml"));
  let kept = 0;
  let dropped = 0;
  for (const file of entries) {
    const full = path.join(taxonomyDir, file);
    const v = readVertical(full);
    if (v == null) {
      // Unknown vertical — leave it alone so we don't accidentally drop a
      // useful file (e.g. partials, README-style YAMLs).
      kept += 1;
      continue;
    }
    if (v === vertical.canonical) {
      kept += 1;
      continue;
    }
    if (dryRun) {
      dropped += 1;
      continue;
    }
    await fse.remove(full);
    dropped += 1;
  }

  // Filter the cross-vertical KPI master.
  const kpiMaster = path.join(outputDir, "data", "kpis", "kpis.yaml");
  let kpisKept = 0;
  let kpisDropped = 0;
  if (!dryRun) {
    const r = filterKpiMaster(kpiMaster, vertical.canonical);
    kpisKept = r.kept;
    kpisDropped = r.dropped;
  }

  // Track for the configuration header.
  ctx.subdomainCount = kept;

  return { kept, dropped, kpisKept, kpisDropped };
}
