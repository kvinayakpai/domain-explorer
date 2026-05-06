// Deprecated: this module has been split into ``lib/db.ts`` (backend-agnostic
// surface), ``lib/db-duckdb.ts`` (DuckDB driver), and ``lib/db-postgres.ts``
// (Postgres driver). It now re-exports from the new location so existing
// imports keep working until they're migrated.
export { queryRows, queryOne } from "./db";
