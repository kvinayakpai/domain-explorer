// Step 9: print a final summary box — the closing demo moment.

import chalk from "chalk";
import path from "node:path";
import { formatDuration } from "../utils/spinner.js";

const BOX_W = 56;

function line(s) {
  const inner = s.length > BOX_W ? s.slice(0, BOX_W) : s + " ".repeat(BOX_W - s.length);
  return chalk.bold.cyan("  ║") + " " + inner + " " + chalk.bold.cyan("║");
}

export function printSummary(summary) {
  const {
    customer,
    customerLabel,
    vertical,
    cloud,
    persona,
    outputDir,
    fileCount,
    keptSubdomains,
    rebrandedFiles,
    cloudFiles,
    gitInitialised,
    elapsedMs,
    dryRun,
  } = summary;

  const top = chalk.bold.cyan("  ╔" + "═".repeat(BOX_W + 2) + "╗");
  const bottom = chalk.bold.cyan("  ╚" + "═".repeat(BOX_W + 2) + "╝");
  const sep = chalk.bold.cyan("  ╠" + "─".repeat(BOX_W + 2) + "╣");

  console.log("");
  console.log(top);
  console.log(line(chalk.bold.green(`✓ Done in ${formatDuration(elapsedMs)}.`)));
  console.log(sep);
  console.log(line(`Customer:   ${customerLabel}`));
  console.log(line(`Vertical:   ${vertical.label}  (kept ${keptSubdomains} subdomains)`));
  console.log(line(`Cloud:      ${cloud.label}`));
  if (persona) {
    console.log(line(`Persona:    ${persona.label}`));
  }
  console.log(line(`Files:      ${fileCount} copied · ${rebrandedFiles} rebranded`));
  if (cloudFiles?.length) {
    console.log(line(`Cloud cfg:  ${cloudFiles.length} file${cloudFiles.length === 1 ? "" : "s"} written`));
  }
  console.log(line(`Git:        ${gitInitialised ? "initialised + first commit" : "skipped"}`));
  console.log(sep);
  console.log(line(chalk.bold("Next:")));
  console.log(line(`  cd ${path.basename(outputDir)}`));
  console.log(line(`  pnpm install`));
  console.log(line(`  pnpm --filter ${customer}-explorer-web dev`));
  console.log(bottom);
  console.log("");

  if (dryRun) {
    console.log(chalk.yellow("  (dry run — nothing was written)"));
    console.log("");
  }
}
