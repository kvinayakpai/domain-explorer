#!/usr/bin/env node
// Validate the pricing_and_promotions anchor YAML against the Zod schema,
// then run a wider sanity check on shape (persona/KPI/source counts).
// Prints a one-line PASS/FAIL token per check.

import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { createRequire } from "node:module";

const require = createRequire(import.meta.url);

// Resolve YAML + Zod from pnpm's hoisted store.
const YAML = require("yaml");
const { z } = require("zod");

const Vertical = z.enum([
  "BFSI", "Insurance", "Retail", "RCG", "CPG", "TTH", "Manufacturing",
  "LifeSciences", "Healthcare", "Telecom", "Media", "Energy", "Utilities",
  "PublicSector", "HiTech", "ProfessionalServices", "CrossCutting",
]);
const KpiDirection = z.enum(["higher_is_better", "lower_is_better", "target_band"]);
const Persona = z.object({
  name: z.string().min(1),
  title: z.string().min(1),
  level: z.enum(["C-suite", "VP", "Director", "Manager", "IC"]),
});
const Decision = z.object({
  id: z.string().min(1),
  statement: z.string().min(1),
});
const Kpi = z.object({
  id: z.string().min(1),
  name: z.string().min(1),
  formula: z.string().min(1),
  unit: z.string().min(1),
  direction: KpiDirection,
  decisionsSupported: z.array(z.string()).default([]),
});
const EntityAttribute = z.object({
  name: z.string().min(1),
  type: z.string().min(1),
  description: z.string().optional(),
  isPrimaryKey: z.boolean().optional(),
  isForeignKey: z.boolean().optional(),
  references: z.string().optional(),
});
const RelationshipKind = z.enum(["one_to_one", "one_to_many", "many_to_many", "many_to_one"]);
const EntityRelationship = z.object({
  to: z.string().min(1),
  kind: RelationshipKind,
  via: z.string().optional(),
  from: z.string().optional(),
});
const Entity = z.object({
  name: z.string().min(1),
  description: z.string().optional(),
  keys: z.array(z.string()).default([]),
  attributes: z.array(EntityAttribute).default([]),
  relationships: z.array(EntityRelationship).default([]),
});
const DataModel = z.object({
  entities: z.array(Entity).default([]),
  relationships: z.array(z.any()).optional(),
});
const SourceSystem = z.object({
  vendor: z.string().min(1),
  product: z.string().min(1),
  category: z.string().min(1),
});
const Connector = z.object({
  type: z.string().min(1),
  protocol: z.string().min(1),
  auth: z.string().min(1),
});

const Subdomain = z.object({
  id: z.string().min(1),
  name: z.string().min(1),
  vertical: Vertical,
  oneLiner: z.string().optional(),
  summary: z.string().optional(),
  personas: z.array(Persona).min(1),
  decisions: z.array(Decision).default([]),
  kpis: z.array(Kpi).default([]),
  dataModel: DataModel.default({ entities: [] }),
  dataModelArtifacts: z.object({
    threeNF: z.string().optional(),
    vault: z.string().optional(),
    dimensional: z.string().optional(),
  }).optional(),
  sourceSystems: z.array(SourceSystem).default([]),
  connectors: z.array(Connector).default([]),
  ingestionChallenges: z.array(z.union([z.string(), z.object({}).passthrough()])).default([]),
  integrationChallenges: z.array(z.union([z.string(), z.object({}).passthrough()])).default([]),
  glossaryTerms: z.array(z.string()).optional(),
  standards: z.array(z.any()).optional(),
}).passthrough();

function fail(msg) {
  console.error("pricing_and_promotions: FAIL — " + msg);
  process.exit(1);
}

const repoRoot = resolve(process.argv[2] ?? ".");
const yamlPath = resolve(repoRoot, "data/taxonomy/pricing_and_promotions.yaml");
const txt = readFileSync(yamlPath, "utf8");
const raw = YAML.parse(txt);

const parsed = Subdomain.safeParse(raw);
if (!parsed.success) {
  fail("Zod validation: " + JSON.stringify(parsed.error.issues, null, 2));
}

const sd = parsed.data;
if (sd.id !== "pricing_and_promotions") fail(`id mismatch: ${sd.id}`);
if (sd.vertical !== "Retail") fail(`vertical mismatch: ${sd.vertical}`);
if (sd.personas.length < 5) fail(`expected >=5 personas, got ${sd.personas.length}`);
if (sd.decisions.length < 8) fail(`expected >=8 decisions, got ${sd.decisions.length}`);
if (sd.kpis.length < 12) fail(`expected >=12 KPIs, got ${sd.kpis.length}`);
if (sd.sourceSystems.length < 10) fail(`expected >=10 source systems, got ${sd.sourceSystems.length}`);
if (sd.integrationChallenges.length < 8) fail(`expected >=8 integration challenges, got ${sd.integrationChallenges.length}`);
if (sd.ingestionChallenges.length < 6) fail(`expected >=6 ingestion challenges, got ${sd.ingestionChallenges.length}`);
const entities = sd.dataModel?.entities ?? [];
if (entities.length < 9) fail(`expected >=9 entities, got ${entities.length}`);

console.log("pricing_and_promotions: OK");
console.log(`  personas:               ${sd.personas.length}`);
console.log(`  decisions:              ${sd.decisions.length}`);
console.log(`  kpis:                   ${sd.kpis.length}`);
console.log(`  sourceSystems:          ${sd.sourceSystems.length}`);
console.log(`  integrationChallenges:  ${sd.integrationChallenges.length}`);
console.log(`  ingestionChallenges:    ${sd.ingestionChallenges.length}`);
console.log(`  entities:               ${entities.length}`);
console.log(`  glossaryTerms:          ${(sd.glossaryTerms ?? []).length}`);
console.log(`  standards:              ${(sd.standards ?? []).length}`);
