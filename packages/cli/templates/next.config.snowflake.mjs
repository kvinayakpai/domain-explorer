/**
 * Next.js config snippet for ${customer} — Snowflake target.
 *
 * Replace `apps/explorer-web/next.config.mjs` with this file (or merge the
 * `env` block) when you switch the data source from DuckDB to Snowflake.
 *
 * The Domain Explorer app reads `process.env.DATA_SOURCE` to choose its
 * adapter. Setting it to "snowflake" routes registry & DQ queries through
 * the Snowflake driver (you'll need to `pnpm add snowflake-sdk` in the
 * `apps/explorer-web` workspace first).
 */
export default {
  reactStrictMode: true,
  env: {
    DATA_SOURCE: "snowflake",
    SNOWFLAKE_DATABASE: process.env.SNOWFLAKE_DATABASE,
    SNOWFLAKE_SCHEMA: process.env.SNOWFLAKE_SCHEMA ?? "PUBLIC",
    SNOWFLAKE_WAREHOUSE: process.env.SNOWFLAKE_WAREHOUSE,
    SNOWFLAKE_ROLE: process.env.SNOWFLAKE_ROLE ?? "DOMAIN_EXPLORER_ROLE",
  },
};
