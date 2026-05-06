import "server-only";

/**
 * Backend-agnostic database layer.
 *
 * Selection
 * ---------
 * The runtime backend is chosen via the ``DB_BACKEND`` env var:
 *   * ``DB_BACKEND=duckdb`` (default) — uses the populated
 *     ``domain-explorer.duckdb`` file at the repo root.
 *   * ``DB_BACKEND=postgres`` — uses ``DATABASE_URL`` to connect via ``pg``.
 *
 * Both backends expose the same ``queryRows`` / ``queryOne`` surface so
 * ``lib/snapshots.ts``, ``lib/dq.ts``, etc. don't have to know which one is
 * active.
 *
 * Translation
 * -----------
 * The default driver is DuckDB; a small ``translateForBackend`` helper
 * rewrites the handful of DuckDB-specific bits that show up in our SQL
 * (currently just ``date_diff``) into the equivalent Postgres expression.
 */

export type Backend = "duckdb" | "postgres";

export function selectedBackend(): Backend {
  const raw = (process.env.DB_BACKEND || "duckdb").toLowerCase();
  return raw === "postgres" ? "postgres" : "duckdb";
}

/**
 * Translate DuckDB-specific SQL into the dialect of the active backend.
 *
 * We hand-write SQL in the snapshot/dq helpers in *DuckDB* dialect because
 * that's the default. When the active backend is Postgres we apply a tiny
 * pre-flight rewrite — currently:
 *
 *   ``date_diff('minute', a, b)`` -> ``EXTRACT(EPOCH FROM (b - a)) / 60``
 *   ``date_diff('hour',   a, b)`` -> ``EXTRACT(EPOCH FROM (b - a)) / 3600``
 *   ``date_diff('day',    a, b)`` -> ``EXTRACT(EPOCH FROM (b - a)) / 86400``
 *   ``quantile_cont(expr, p)``     -> ``percentile_cont(p) WITHIN GROUP (ORDER BY expr)``
 *
 * Add more rewrites here as the snapshot SQL grows. The translation is
 * intentionally regex-based and small — the queries we run against the
 * dual backends are simple aggregate scans.
 */
export function translateForBackend(sql: string, backend: Backend): string {
  if (backend !== "postgres") return sql;
  let out = sql;

  // date_diff('unit', a, b) -> EXTRACT(EPOCH FROM (b - a)) / divisor
  out = out.replace(
    /date_diff\(\s*'(minute|hour|day|second)'\s*,\s*([^,]+?)\s*,\s*([^)]+?)\)/gi,
    (_m, unit: string, a: string, b: string) => {
      const divisor =
        unit.toLowerCase() === "minute"
          ? 60
          : unit.toLowerCase() === "hour"
          ? 3600
          : unit.toLowerCase() === "day"
          ? 86400
          : 1;
      return `(EXTRACT(EPOCH FROM (${b.trim()} - ${a.trim()})) / ${divisor})`;
    },
  );

  // quantile_cont(expr, p) -> percentile_cont(p) WITHIN GROUP (ORDER BY expr)
  // Note: we look for the "expr , number)" shape — sufficient for our needs.
  out = out.replace(
    /quantile_cont\(\s*([\s\S]+?)\s*,\s*([0-9.]+)\s*\)/gi,
    (_m, expr: string, p: string) =>
      `percentile_cont(${p}) WITHIN GROUP (ORDER BY ${expr})`,
  );

  return out;
}

async function getDriver() {
  const backend = selectedBackend();
  if (backend === "postgres") {
    const { runQuery } = await import("./db-postgres");
    return { backend, runQuery } as const;
  }
  const { runQuery } = await import("./db-duckdb");
  return { backend, runQuery } as const;
}

/**
 * Run a query against the active backend and return rows as JSON-safe objects.
 *
 * For DuckDB, ``getRowObjectsJson()`` stringifies bigints / decimals so they
 * survive serialization across Server Components — we coerce numeric strings
 * back where needed in the snapshot helpers. The Postgres impl mirrors that
 * behaviour: bigints / numerics arrive as strings, callers ``Number(...)``
 * them when they need a number.
 */
export async function queryRows<T = Record<string, any>>(sql: string): Promise<T[]> {
  const { backend, runQuery } = await getDriver();
  const translated = translateForBackend(sql, backend);
  return (await runQuery(translated)) as T[];
}

export async function queryOne<T = Record<string, any>>(sql: string): Promise<T | null> {
  const rows = await queryRows<T>(sql);
  return (rows.length === 0 ? null : rows[0]) as T | null;
}
