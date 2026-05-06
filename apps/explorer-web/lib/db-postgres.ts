import "server-only";

/**
 * Postgres backend driver.
 *
 * Activated when ``DB_BACKEND=postgres``. Uses ``DATABASE_URL`` for the
 * connection string. We keep a single shared ``Pool`` per Node process —
 * Next.js dev mode HMR can re-evaluate this module, so we stash the pool
 * on ``globalThis`` to survive reloads.
 */

type PgPool = {
  query: (sql: string) => Promise<{ rows: any[] }>;
  end: () => Promise<void>;
};

declare global {
  // eslint-disable-next-line no-var
  var __explorerPgPool: PgPool | undefined;
}

async function getPool(): Promise<PgPool> {
  if (globalThis.__explorerPgPool) return globalThis.__explorerPgPool;
  const databaseUrl = process.env.DATABASE_URL;
  if (!databaseUrl) {
    throw new Error(
      "DB_BACKEND=postgres but DATABASE_URL is not set. " +
        "Provide a Postgres URL like postgresql://user:pass@host:5432/db",
    );
  }
  // Dynamic import keeps ``pg`` out of the bundle for DuckDB users.
  const pg: any = await import("pg");
  const PoolCtor = pg.Pool ?? pg.default?.Pool;
  if (!PoolCtor) {
    throw new Error("pg module did not expose Pool — install the 'pg' package");
  }
  // Bigints/numerics arrive as strings (default ``pg`` behaviour). Snapshot
  // helpers already cope with strings, so we don't fiddle with type parsers.
  const pool: PgPool = new PoolCtor({ connectionString: databaseUrl });
  globalThis.__explorerPgPool = pool;
  return pool;
}

/**
 * Run a query against Postgres and return JSON-safe row objects.
 *
 * Numeric / bigint columns come back as strings so they round-trip through
 * the React Server Component boundary unchanged — matching the DuckDB
 * driver. Snapshot helpers wrap raw values with ``Number(...)`` when a
 * number is actually needed.
 */
export async function runQuery<T = Record<string, any>>(sql: string): Promise<T[]> {
  const pool = await getPool();
  const result = await pool.query(sql);
  return (result.rows ?? []) as T[];
}
