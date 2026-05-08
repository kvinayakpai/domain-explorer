// ASCII banner + the "configuration block" shown at the top of a run.
// Kept in its own module because we want to be able to skip it cleanly
// when --quiet is set and to test it.

import chalk from "chalk";

const BOX_W = 56;
const BANNER_LINES = [
  "",
  chalk.bold.cyan("  ╔" + "═".repeat(BOX_W) + "╗"),
  chalk.bold.cyan("  ║") +
    chalk.bold.white(centre("DOMAIN EXPLORER — Customer Accelerator", BOX_W)) +
    chalk.bold.cyan("║"),
  chalk.bold.cyan("  ║") +
    chalk.dim(centre("npx @domain-explorer/init <customer>", BOX_W)) +
    chalk.bold.cyan("║"),
  chalk.bold.cyan("  ╚" + "═".repeat(BOX_W) + "╝"),
  "",
];

function centre(s, width) {
  if (s.length >= width) return s.slice(0, width);
  const total = width - s.length;
  const left = Math.floor(total / 2);
  const right = total - left;
  return " ".repeat(left) + s + " ".repeat(right);
}

export function printBanner() {
  for (const line of BANNER_LINES) console.log(line);
}

/**
 * Pretty configuration block. Shown right after the banner so prospects can
 * confirm the run before any work happens.
 */
export function printSummaryHeader(ctx) {
  const subdomainsHint = ctx.subdomainCount
    ? `${ctx.subdomainCount} subdomain${ctx.subdomainCount === 1 ? "" : "s"}`
    : "subdomains TBD";

  console.log("  " + chalk.bold("Customer:") + "  " + chalk.cyan(ctx.customerLabel));
  console.log(
    "  " +
      chalk.bold("Vertical:") +
      "  " +
      chalk.cyan(ctx.vertical.label) +
      chalk.dim(`  (${subdomainsHint})`),
  );
  console.log("  " + chalk.bold("Cloud:") + "     " + chalk.cyan(ctx.cloud.label));
  if (ctx.persona) {
    console.log("  " + chalk.bold("Persona:") + "   " + chalk.cyan(ctx.persona.label));
  } else {
    console.log("  " + chalk.bold("Persona:") + "   " + chalk.dim("(none)"));
  }
  if (ctx.tagline) {
    console.log("  " + chalk.bold("Tagline:") + "   " + chalk.dim(`"${ctx.tagline}"`));
  }
  console.log("");
}
