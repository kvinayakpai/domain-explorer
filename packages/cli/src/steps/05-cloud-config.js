// Step 5: emit cloud-specific configuration files.
//
// We don't try to fully parameterise dbt for every cloud. We just drop a
// `profiles.yml` skeleton that the SE / customer can edit in 30 seconds, plus
// a Next.js DB-config snippet wired through `DATABASE_URL`. Sensible defaults
// + clearly-named env vars ⇒ much less brittle than auto-injecting credentials.

import path from "node:path";
import fs from "node:fs";
import fse from "fs-extra";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const TEMPLATE_DIR = path.resolve(__dirname, "..", "..", "templates");

/** Read a template file and substitute ${customer} / ${vertical} placeholders. */
function renderTemplate(name, vars) {
  const file = path.join(TEMPLATE_DIR, name);
  let text = fs.readFileSync(file, "utf8");
  for (const [k, v] of Object.entries(vars)) {
    text = text.replaceAll("${" + k + "}", String(v));
  }
  return text;
}

export async function writeCloudConfig(ctx) {
  const { outputDir, cloud, customer, dryRun } = ctx;
  if (dryRun) return { files: [] };

  const files = [];
  await fse.ensureDir(path.join(outputDir, "modeling", "dbt"));

  switch (cloud.slug) {
    case "snowflake": {
      const profile = renderTemplate("profiles-snowflake.yml", { customer });
      const profilePath = path.join(outputDir, "modeling", "dbt", "profiles-snowflake.yml");
      fs.writeFileSync(profilePath, profile, "utf8");
      files.push("modeling/dbt/profiles-snowflake.yml");

      const nextSnippet = renderTemplate("next.config.snowflake.mjs", { customer });
      const nextPath = path.join(outputDir, "next.config.snowflake.mjs");
      fs.writeFileSync(nextPath, nextSnippet, "utf8");
      files.push("next.config.snowflake.mjs");

      appendEnvExample(outputDir, [
        "",
        "# --- Snowflake (added by Customer Accelerator) ---",
        "SNOWFLAKE_ACCOUNT=",
        "SNOWFLAKE_USER=",
        "SNOWFLAKE_PRIVATE_KEY_PATH=",
        `SNOWFLAKE_WAREHOUSE=${customer.toUpperCase().replaceAll("-", "_")}_WH`,
        `SNOWFLAKE_DATABASE=${customer.toUpperCase().replaceAll("-", "_")}_DOMAIN_EXPLORER`,
        "SNOWFLAKE_SCHEMA=PUBLIC",
        "SNOWFLAKE_ROLE=DOMAIN_EXPLORER_ROLE",
        "",
      ]);
      break;
    }

    case "bigquery": {
      const profile = renderTemplate("profiles-bigquery.yml", { customer });
      fs.writeFileSync(
        path.join(outputDir, "modeling", "dbt", "profiles-bigquery.yml"),
        profile,
        "utf8",
      );
      files.push("modeling/dbt/profiles-bigquery.yml");

      appendEnvExample(outputDir, [
        "",
        "# --- BigQuery (added by Customer Accelerator) ---",
        "BIGQUERY_PROJECT=",
        `BIGQUERY_DATASET=${customer.replaceAll("-", "_")}_domain_explorer`,
        "BIGQUERY_LOCATION=US",
        "BIGQUERY_KEYFILE=",
        "",
      ]);
      break;
    }

    case "databricks": {
      const profile = renderTemplate("profiles-databricks.yml", { customer });
      fs.writeFileSync(
        path.join(outputDir, "modeling", "dbt", "profiles-databricks.yml"),
        profile,
        "utf8",
      );
      files.push("modeling/dbt/profiles-databricks.yml");

      appendEnvExample(outputDir, [
        "",
        "# --- Databricks (added by Customer Accelerator) ---",
        "DATABRICKS_HOST=",
        "DATABRICKS_HTTP_PATH=",
        "DATABRICKS_TOKEN=",
        `DATABRICKS_CATALOG=${customer.replaceAll("-", "_")}_catalog`,
        "DATABRICKS_SCHEMA=domain_explorer",
        "",
      ]);
      break;
    }

    case "postgres": {
      const profile = renderTemplate("profiles-postgres.yml", { customer });
      fs.writeFileSync(
        path.join(outputDir, "modeling", "dbt", "profiles-postgres.yml"),
        profile,
        "utf8",
      );
      files.push("modeling/dbt/profiles-postgres.yml");

      appendEnvExample(outputDir, [
        "",
        "# --- Postgres (added by Customer Accelerator) ---",
        `DATABASE_URL=postgres://user:password@localhost:5432/${customer.replaceAll("-", "_")}_domain_explorer`,
        "",
      ]);
      break;
    }

    case "duckdb":
    default: {
      // DuckDB is the source default — nothing to write. We just leave a note.
      const note = renderTemplate("README-duckdb.md", { customer });
      fs.writeFileSync(
        path.join(outputDir, "modeling", "dbt", "README-cloud.md"),
        note,
        "utf8",
      );
      files.push("modeling/dbt/README-cloud.md");
      break;
    }
  }

  return { files };
}

function appendEnvExample(outputDir, lines) {
  const envPath = path.join(outputDir, ".env.example");
  if (!fs.existsSync(envPath)) return;
  const cur = fs.readFileSync(envPath, "utf8");
  fs.writeFileSync(envPath, cur + lines.join("\n"), "utf8");
}
