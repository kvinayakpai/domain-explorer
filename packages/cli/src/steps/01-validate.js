// Step 1: validate inputs and resolve defaults.
// Returns {ok:true, context} on success or {ok:false, error} on failure.
//
// The "context" object is passed unchanged through every later step.

import path from "node:path";
import fs from "node:fs";
import {
  VERTICALS,
  CLOUDS,
  PERSONAS,
  findVertical,
  findCloud,
  findPersona,
} from "../registries.js";

const CUSTOMER_RE = /^[a-z][a-z0-9-]{2,29}$/i;

/** Build a friendly customer label from a slug ("acme-bank" → "Acme Bank"). */
export function customerLabelFor(slug) {
  return slug
    .split("-")
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1).toLowerCase())
    .join(" ");
}

/**
 * Validate raw CLI options and resolve defaults.
 * @param {object} opts
 * @returns {Promise<{ok:boolean, error?:string, context?:object}>}
 */
export async function validate(opts) {
  const customer = String(opts.customer ?? "").trim();
  if (!customer) {
    return { ok: false, error: "Customer name is required." };
  }
  if (!CUSTOMER_RE.test(customer)) {
    return {
      ok: false,
      error: `Invalid customer name "${customer}": must be 3-30 chars, alphanumeric + hyphens, starting with a letter.`,
    };
  }
  if (customer.length < 3 || customer.length > 30) {
    return { ok: false, error: `Customer name length must be 3-30 chars.` };
  }

  // Vertical (required): we accept either slug or canonical (BFSI, Insurance…).
  if (!opts.vertical) {
    return {
      ok: false,
      error: `Missing --vertical. Pick one of: ${VERTICALS.map((v) => v.slug).join(", ")}`,
    };
  }
  const verticalSlug = String(opts.vertical).toLowerCase();
  const vertical =
    findVertical(verticalSlug) ??
    VERTICALS.find((v) => v.canonical.toLowerCase() === verticalSlug);
  if (!vertical) {
    return {
      ok: false,
      error: `Unknown vertical "${opts.vertical}". Pick one of: ${VERTICALS.map((v) => v.slug).join(", ")}`,
    };
  }

  // Cloud (optional, defaults to duckdb).
  const cloudSlug = String(opts.cloud ?? "duckdb").toLowerCase();
  const cloud = findCloud(cloudSlug);
  if (!cloud) {
    return {
      ok: false,
      error: `Unknown cloud "${opts.cloud}". Pick one of: ${CLOUDS.map((c) => c.slug).join(", ")}`,
    };
  }

  // Persona (optional). If unrecognised we still continue, but the step that
  // writes the default-persona file will skip rather than write garbage.
  let persona = null;
  if (opts.persona) {
    persona = findPersona(String(opts.persona).toLowerCase()) ?? {
      id: String(opts.persona).toLowerCase(),
      label: customerLabelFor(String(opts.persona)),
      unknown: true,
    };
  }

  // Source repo. Accept --source-repo, $DOMAIN_EXPLORER_REPO, or default to ".".
  const sourceRepo =
    opts.sourceRepo ?? process.env.DOMAIN_EXPLORER_REPO ?? process.cwd();
  if (!fs.existsSync(sourceRepo)) {
    return { ok: false, error: `Source repo not found: ${sourceRepo}` };
  }
  // Sanity check: the source repo must look like Domain Explorer.
  const pkgPath = path.join(sourceRepo, "package.json");
  if (!fs.existsSync(pkgPath)) {
    return {
      ok: false,
      error: `Source repo at ${sourceRepo} does not contain a package.json — is this the Domain Explorer repo?`,
    };
  }
  let sourcePkg;
  try {
    sourcePkg = JSON.parse(fs.readFileSync(pkgPath, "utf8"));
  } catch (err) {
    return { ok: false, error: `Could not read source package.json: ${err.message}` };
  }

  // Output dir. Default: ./<customer>-domain-explorer at CWD.
  const outputDir =
    opts.outputDir ??
    path.resolve(process.cwd(), `${customer}-domain-explorer`);

  // Logo: must exist if provided.
  let logo = null;
  if (opts.logo) {
    if (!fs.existsSync(opts.logo)) {
      return { ok: false, error: `Logo file not found: ${opts.logo}` };
    }
    logo = path.resolve(opts.logo);
  }

  // commander stores --no-git as `git: false`; map to a positive flag.
  const skipGit = opts.git === false || opts.dryRun === true;

  const context = {
    customer,
    customerLabel: customerLabelFor(customer),
    vertical,
    cloud,
    persona,
    sourceRepo: path.resolve(sourceRepo),
    sourcePkg,
    outputDir: path.resolve(outputDir),
    logo,
    tagline: opts.tagline ?? "",
    dryRun: Boolean(opts.dryRun),
    quiet: Boolean(opts.quiet),
    skipGit,
    // Counts get filled in by later steps so the summary block can show them.
    subdomainCount: null,
  };
  return { ok: true, context };
}
