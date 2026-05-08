// Main `init()` orchestrator. Each step is small, async, and returns a
// "result" object; we wrap the call in a spinner so the demo feels alive.
//
// Step order is significant: we validate first (cheap), clone next (the only
// step that takes meaningful time), then rebrand/filter (operating on the new
// tree), then optional git init.

import path from "node:path";
import os from "node:os";
import chalk from "chalk";

import { printBanner, printSummaryHeader } from "./utils/banner.js";
import { runStep } from "./utils/spinner.js";
import { validate } from "./steps/01-validate.js";
import { clone } from "./steps/02-clone.js";
import { filterSubdomains } from "./steps/03-filter-subdomains.js";
import { rebrand } from "./steps/04-rebrand.js";
import { writeCloudConfig } from "./steps/05-cloud-config.js";
import { setDefaultPersona } from "./steps/06-persona-default.js";
import { renameApp } from "./steps/07-rename-app.js";
import { initGit } from "./steps/08-init-git.js";
import { printSummary } from "./steps/09-print-summary.js";

/**
 * Run the full Customer Accelerator flow.
 *
 * @param {object} opts
 * @param {string} opts.customer
 * @param {string} [opts.vertical]
 * @param {string} [opts.cloud]
 * @param {string} [opts.persona]
 * @param {string} [opts.outputDir]
 * @param {string} [opts.sourceRepo]
 * @param {string} [opts.logo]
 * @param {string} [opts.tagline]
 * @param {boolean} [opts.dryRun]
 * @param {boolean} [opts.git]   commander stores --no-git as `git: false`.
 * @param {boolean} [opts.quiet]
 * @returns {Promise<{exitCode:number, summary:object}>}
 */
export async function init(opts) {
  const startedAt = Date.now();
  const quiet = Boolean(opts.quiet);
  const log = quiet ? () => {} : (...a) => console.log(...a);

  if (!quiet) printBanner();

  // 1) Validate — also normalises slugs and resolves defaults.
  const validation = await runStep({
    label: "Validating configuration",
    quiet,
    fn: () => validate(opts),
  });
  if (!validation.ok) {
    console.error(chalk.red("\n  ✗ ") + validation.error);
    return { exitCode: 1, summary: null };
  }
  const ctx = validation.context;

  // Pretty header showing the resolved configuration.
  if (!quiet) printSummaryHeader(ctx);

  // 2) Clone the source repo (skipping heavy directories).
  const cloneResult = await runStep({
    label: `Cloning source files`,
    quiet,
    longRunningHint: "Copying files… (this is the only slow step)",
    fn: (sub) => clone(ctx, sub),
  });

  // 3) Filter taxonomy / KPI YAMLs to the chosen vertical.
  const filterResult = await runStep({
    label: `Filtering to ${ctx.vertical.label} subdomains`,
    quiet,
    fn: () => filterSubdomains(ctx),
  });

  // 4) Rebrand strings + optional logo/tagline.
  const rebrandResult = await runStep({
    label: `Rebranding UI for "${ctx.customerLabel}"`,
    quiet,
    fn: () => rebrand(ctx),
  });

  // 5) Cloud config (snowflake / bigquery / postgres / databricks / duckdb).
  const cloudResult = await runStep({
    label: `Generating ${ctx.cloud.label} config`,
    quiet,
    fn: () => writeCloudConfig(ctx),
  });

  // 6) Default persona on the assistant page.
  const personaResult = await runStep({
    label: ctx.persona
      ? `Setting ${ctx.persona.label} as default persona`
      : "Skipping persona default",
    quiet,
    fn: () => setDefaultPersona(ctx),
  });

  // 7) Rename Next.js app.
  const renameResult = await runStep({
    label: `Renaming package to ${ctx.customer}-explorer`,
    quiet,
    fn: () => renameApp(ctx),
  });

  // 8) Init git (unless --no-git or --dry-run).
  const gitResult = await runStep({
    label: ctx.skipGit ? "Skipping git init" : "Initialising git repository",
    quiet,
    fn: () => initGit(ctx),
  });

  // 9) Pretty summary.
  const summary = {
    customer: ctx.customer,
    customerLabel: ctx.customerLabel,
    vertical: ctx.vertical,
    cloud: ctx.cloud,
    persona: ctx.persona,
    outputDir: ctx.outputDir,
    fileCount: cloneResult?.fileCount ?? 0,
    keptSubdomains: filterResult?.kept ?? 0,
    droppedSubdomains: filterResult?.dropped ?? 0,
    rebrandedFiles: rebrandResult?.changedFiles ?? 0,
    cloudFiles: cloudResult?.files ?? [],
    gitInitialised: gitResult?.ok ?? false,
    elapsedMs: Date.now() - startedAt,
    dryRun: Boolean(opts.dryRun),
  };

  if (!quiet) printSummary(summary);

  return { exitCode: 0, summary };
}

/**
 * Convenience: programmatic entry point that callers (tests) can use without
 * having to assemble a full options object. Picks sensible defaults.
 */
export async function initWithDefaults(customer, overrides = {}) {
  const tmp = path.join(os.tmpdir(), `domain-explorer-${customer}-${Date.now()}`);
  return init({
    customer,
    vertical: "bfsi",
    cloud: "duckdb",
    outputDir: tmp,
    git: false,
    quiet: true,
    ...overrides,
  });
}
