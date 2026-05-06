import "server-only";
import { existsSync } from "node:fs";
import { dirname, resolve } from "node:path";

let _instance: any = null;

function findRepoRoot(): string {
  let dir = resolve(process.cwd());
  for (let i = 0; i < 10; i++) {
    if (existsSync(resolve(dir, "domain-explorer.duckdb"))) return dir;
    if (existsSync(resolve(dir, "data", "taxonomy")) && existsSync(resolve(dir, "synthetic-data"))) {
      return dir;
    }
    const parent = dirname(dir);
    if (parent === dir) break;
    dir = parent;
  }
  return process.cwd();
}

async function getInstance(): Promise<any> {
  if (_instance) return _instance;
  const dbPath = resolve(findRepoRoot(), "domain-explorer.duckdb");
  if (!existsSync(dbPath)) {
    throw new Error(
      `domain-explorer.duckdb not found at ${dbPath}. Run synthetic-data/generate_all.py first.`,
    );
  }
  const mod: any = await import("@duckdb/node-api");
  _instance = await mod.DuckDBInstance.create(dbPath);
  return _instance;
}

/**
 * Run a query against the prebuilt DuckDB and return rows as JSON-safe objects.
 *
 * ``getRowObjectsJson`` stringifies bigints / decimals so they survive
 * serialization across Server Components — we coerce numeric strings back
 * where needed in the snapshot helpers.
 */
export async function runQuery<T = Record<string, any>>(sql: string): Promise<T[]> {
  const instance = await getInstance();
  const con = await instance.connect();
  try {
    const reader = await con.runAndReadAll(sql);
    const rows: any[] = reader.getRowObjectsJson();
    return rows as T[];
  } finally {
    await con.close();
  }
}
