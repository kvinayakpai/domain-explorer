import "server-only";
import { existsSync, readFileSync } from "node:fs";
import { resolve } from "node:path";

export interface DqResult {
  id: string;
  subdomain: string;
  table: string;
  column?: string | null;
  rule_type: string;
  severity: "critical" | "high" | "medium" | "low";
  expectation: string;
  failing_rows: number;
  passed: boolean;
  duration_ms: number;
  error?: string | null;
}

export interface DqReport {
  ran_at: string;
  duckdb_available: boolean;
  total_rules: number;
  passed: number;
  failed: number;
  errored: number;
  pass_rate: number;
  by_severity: Record<string, { passed: number; failed: number; errored: number }>;
  by_subdomain: Record<string, { passed: number; failed: number; errored: number }>;
  results: DqResult[];
}

function findRepoRoot(): string {
  let dir = process.cwd();
  for (let i = 0; i < 8; i++) {
    if (existsSync(resolve(dir, "data", "quality"))) return dir;
    const parent = resolve(dir, "..");
    if (parent === dir) break;
    dir = parent;
  }
  return process.cwd();
}

const API_BASE = process.env.DOMAIN_EXPLORER_API ?? "http://localhost:8000";

/** Try the live FastAPI service first; fall back to the committed snapshot. */
export async function loadDqReport(): Promise<{ report: DqReport | null; source: "live" | "snapshot" | "none" }> {
  // Live path — useful when the API service is up.
  try {
    const res = await fetch(`${API_BASE}/dq/run`, {
      cache: "no-store",
      // Give up quickly so the page stays responsive in offline demos.
      signal: AbortSignal.timeout(1500),
    });
    if (res.ok) {
      return { report: (await res.json()) as DqReport, source: "live" };
    }
  } catch {
    // ignore; fall through to snapshot
  }

  const snap = resolve(findRepoRoot(), "data", "quality", "last_run.json");
  if (existsSync(snap)) {
    return { report: JSON.parse(readFileSync(snap, "utf-8")) as DqReport, source: "snapshot" };
  }
  return { report: null, source: "none" };
}
