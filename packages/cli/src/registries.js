// Static registries: known verticals, clouds, and a small persona map.
// Kept in JS (not YAML) so the CLI runs without parsing the source repo's
// metadata package up-front — that keeps cold-start near-zero.

/**
 * 16 industry verticals, mirroring the slugs used inside data/taxonomy/*.yaml's
 * `vertical:` field. Slug is what the CLI accepts on the command line; label is
 * what we show in the spinner output.
 */
export const VERTICALS = [
  { slug: "bfsi", label: "BFSI", canonical: "BFSI" },
  { slug: "insurance", label: "Insurance", canonical: "Insurance" },
  { slug: "retail", label: "Retail", canonical: "Retail" },
  { slug: "rcg", label: "RCG", canonical: "RCG" },
  { slug: "cpg", label: "CPG", canonical: "CPG" },
  { slug: "tth", label: "Travel, Transport & Hospitality", canonical: "TTH" },
  { slug: "manufacturing", label: "Manufacturing", canonical: "Manufacturing" },
  { slug: "lifesciences", label: "Life Sciences", canonical: "LifeSciences" },
  { slug: "healthcare", label: "Healthcare", canonical: "Healthcare" },
  { slug: "telecom", label: "Telecom", canonical: "Telecom" },
  { slug: "media", label: "Media", canonical: "Media" },
  { slug: "energy", label: "Energy", canonical: "Energy" },
  { slug: "utilities", label: "Utilities", canonical: "Utilities" },
  { slug: "publicsector", label: "Public Sector", canonical: "PublicSector" },
  { slug: "hitech", label: "HiTech", canonical: "HiTech" },
  {
    slug: "professionalservices",
    label: "Professional Services",
    canonical: "ProfessionalServices",
  },
];

export const CLOUDS = [
  { slug: "duckdb", label: "DuckDB (default)" },
  { slug: "snowflake", label: "Snowflake" },
  { slug: "databricks", label: "Databricks" },
  { slug: "bigquery", label: "BigQuery" },
  { slug: "postgres", label: "Postgres" },
];

/**
 * A small map of persona shorthand ids that prospects often ask for. The CLI
 * stamps these as the default in the assistant landing page. The full persona
 * list is the union of every subdomain's `personas:` block — when the user
 * passes an id we don't recognise here we fall through gracefully and write
 * the raw id as the default (the UI will fall back to "first persona").
 */
export const PERSONAS = [
  { id: "cdo", label: "Chief Data Officer" },
  { id: "cto", label: "Chief Technology Officer" },
  { id: "ciso", label: "Chief Information Security Officer" },
  { id: "head-of-payments", label: "Head of Payments" },
  { id: "head-of-cards", label: "Head of Cards" },
  { id: "head-of-claims", label: "Head of Claims" },
  { id: "head-of-underwriting", label: "Head of Underwriting" },
  { id: "head-of-merchandising", label: "Head of Merchandising" },
  { id: "head-of-pricing", label: "Head of Pricing" },
  { id: "demand-planner", label: "Demand Planner" },
  { id: "vp-analytics", label: "VP, Analytics" },
  { id: "vp-data-engineering", label: "VP, Data Engineering" },
  { id: "head-of-fraud", label: "Head of Fraud" },
  { id: "head-of-aml", label: "Head of AML" },
  { id: "treasurer", label: "Treasurer" },
];

/** Lookup helpers — case-insensitive. */
export function findVertical(slug) {
  if (!slug) return undefined;
  const norm = String(slug).toLowerCase();
  return VERTICALS.find((v) => v.slug === norm);
}

export function findCloud(slug) {
  if (!slug) return undefined;
  const norm = String(slug).toLowerCase();
  return CLOUDS.find((c) => c.slug === norm);
}

export function findPersona(id) {
  if (!id) return undefined;
  const norm = String(id).toLowerCase();
  return PERSONAS.find((p) => p.id === norm);
}
