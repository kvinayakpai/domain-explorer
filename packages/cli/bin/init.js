#!/usr/bin/env node
// Domain Explorer Customer Accelerator CLI — entry point.
//
// Usage:
//   npx @domain-explorer/init <customer> --vertical=bfsi --cloud=snowflake --persona=cdo
//
// Run `--help` for the full flag list. The implementation lives in `../src/index.js`;
// keeping the bin file thin makes it trivial to test the flow programmatically.

import { Command } from "commander";
import { init } from "../src/index.js";
import { VERTICALS, CLOUDS } from "../src/registries.js";

const program = new Command();

program
  .name("domain-explorer-init")
  .description(
    "Customer Accelerator: produce a branded Domain Explorer clone for a prospect in ~30s.",
  )
  .argument("<customer>", "Customer slug (alphanumeric + hyphens, 3-30 chars)")
  .option(
    "--vertical <slug>",
    `Industry vertical. One of: ${VERTICALS.map((v) => v.slug).join(", ")}`,
  )
  .option(
    "--cloud <slug>",
    `Cloud target. One of: ${CLOUDS.map((c) => c.slug).join(", ")}`,
    "duckdb",
  )
  .option("--persona <id>", "Default persona id (e.g. cdo, head-of-payments)")
  .option(
    "--output-dir <path>",
    "Output directory (default: ./<customer>-domain-explorer)",
  )
  .option(
    "--source-repo <path>",
    "Path to the source Domain Explorer repo. Defaults to $DOMAIN_EXPLORER_REPO or `..`.",
  )
  .option("--logo <path>", "Path to a customer logo image (.png/.svg)")
  .option("--tagline <string>", "Customer tagline used as hero subtitle")
  .option("--dry-run", "Print the plan without making changes", false)
  .option("--no-git", "Skip git init/commit at the end", false)
  .option("--quiet", "Suppress banner and minimise output", false)
  .action(async (customer, opts) => {
    try {
      const result = await init({ customer, ...opts });
      // Success exit — non-zero on validation/runtime errors.
      process.exit(result.exitCode ?? 0);
    } catch (err) {
      // The init() flow handles its own pretty-printing for known errors.
      // Anything that bubbles here is unexpected.
      console.error("\n  ✗ Unexpected error:", err?.message ?? err);
      if (process.env.DEBUG) console.error(err?.stack ?? "");
      process.exit(1);
    }
  });

program.parseAsync(process.argv);
