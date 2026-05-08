import { z } from "zod";

/** Vertical / industry buckets used across the registry. */
export const Vertical = z.enum([
  "BFSI",
  "Insurance",
  "Retail",
  "RCG",
  "CPG",
  "TTH",
  "Manufacturing",
  "LifeSciences",
  "Healthcare",
  "Telecom",
  "Media",
  "Energy",
  "Utilities",
  "PublicSector",
  "HiTech",
  "ProfessionalServices",
]);
export type Vertical = z.infer<typeof Vertical>;

export const KpiDirection = z.enum(["higher_is_better", "lower_is_better", "target_band"]);
export type KpiDirection = z.infer<typeof KpiDirection>;

export const Persona = z.object({
  name: z.string().min(1),
  title: z.string().min(1),
  level: z.enum(["C-suite", "VP", "Director", "Manager", "IC"]),
});
export type Persona = z.infer<typeof Persona>;

export const Decision = z.object({
  id: z.string().min(1),
  statement: z.string().min(1),
});
export type Decision = z.infer<typeof Decision>;

export const Kpi = z.object({
  id: z.string().min(1),
  name: z.string().min(1),
  formula: z.string().min(1),
  unit: z.string().min(1),
  direction: KpiDirection,
  decisionsSupported: z.array(z.string()).default([]),
});
export type Kpi = z.infer<typeof Kpi>;

/** Single column on an entity, used by the ERD viewer. */
export const EntityAttribute = z.object({
  name: z.string().min(1),
  type: z.string().min(1),
  description: z.string().optional(),
  isPrimaryKey: z.boolean().optional(),
  isForeignKey: z.boolean().optional(),
  references: z.string().optional(),
});
export type EntityAttribute = z.infer<typeof EntityAttribute>;

/** Cardinality between two entities. */
export const RelationshipKind = z.enum(["one_to_one", "one_to_many", "many_to_many"]);
export type RelationshipKind = z.infer<typeof RelationshipKind>;

export const EntityRelationship = z.object({
  to: z.string().min(1),
  kind: RelationshipKind,
  via: z.string().optional(),
});
export type EntityRelationship = z.infer<typeof EntityRelationship>;

export const Entity = z.object({
  name: z.string().min(1),
  description: z.string().optional(),
  keys: z.array(z.string()).default([]),
  attributes: z.array(EntityAttribute).default([]),
  relationships: z.array(EntityRelationship).default([]),
});
export type Entity = z.infer<typeof Entity>;

/** Pointers to per-style DDL files (relative paths) for a subdomain. */
export const DataModelArtifacts = z.object({
  threeNF: z.string().optional(),
  vault: z.string().optional(),
  dimensional: z.string().optional(),
});
export type DataModelArtifacts = z.infer<typeof DataModelArtifacts>;

export const DataModel = z.object({
  entities: z.array(Entity).default([]),
});
export type DataModel = z.infer<typeof DataModel>;

export const SourceSystem = z.object({
  vendor: z.string().min(1),
  product: z.string().min(1),
  category: z.string().min(1),
});
export type SourceSystem = z.infer<typeof SourceSystem>;

export const Connector = z.object({
  type: z.string().min(1),
  protocol: z.string().min(1),
  auth: z.string().min(1),
});
export type Connector = z.infer<typeof Connector>;

export const Subdomain = z.object({
  id: z.string().min(1),
  name: z.string().min(1),
  vertical: Vertical,
  oneLiner: z.string().min(1),
  personas: z.array(Persona).min(1),
  decisions: z.array(Decision).default([]),
  kpis: z.array(Kpi).default([]),
  dataModel: DataModel.default({ entities: [] }),
  dataModelArtifacts: DataModelArtifacts.optional(),
  sourceSystems: z.array(SourceSystem).default([]),
  connectors: z.array(Connector).default([]),
  ingestionChallenges: z.array(
    z.union([
      z.string(),
      z.object({}).passthrough()
    ])
  ).default([]),
  integrationChallenges: z.array(
    z.union([
      z.string(),
      z.object({}).passthrough()
    ])
  ).default([]),
});
export type Subdomain = z.infer<typeof Subdomain>;

/** Standalone KPI registry entry (KPIs that aren't tied to one subdomain). */
export const KpiRegistryEntry = Kpi.extend({
  vertical: Vertical,
});
export type KpiRegistryEntry = z.infer<typeof KpiRegistryEntry>;

/** Master KPI library entry — superset of registry with extra metadata. */
export const KpiMasterEntry = z.object({
  id: z.string().min(1),
  name: z.string().min(1),
  formula: z.string().min(1),
  unit: z.string().min(1),
  direction: KpiDirection,
  definition: z.string().optional(),
  vertical: Vertical.optional(),
  subdomains: z.array(z.string()).default([]),
  related_personas: z.array(z.string()).default([]),
  decisionsSupported: z.array(z.string()).default([]),
});
export type KpiMasterEntry = z.infer<typeof KpiMasterEntry>;

/** Per-style SQL implementations of a single KPI. */
export const KpiSqlSpec = z.object({
  kpi_id: z.string().min(1),
  threeNF: z.string().optional(),
  vault: z.string().optional(),
  dimensional: z.string().optional(),
  notes: z.string().optional(),
});
export type KpiSqlSpec = z.infer<typeof KpiSqlSpec>;

/** Source system registry entry. */
export const SourceSystemEntry = z.object({
  id: z.string().min(1),
  vendor: z.string().min(1),
  product: z.string().min(1),
  category: z.string().min(1),
  primaryConnectors: z.array(z.string()).default([]),
});
export type SourceSystemEntry = z.infer<typeof SourceSystemEntry>;

/** Connector pattern entry. */
export const ConnectorPattern = z.object({
  id: z.string().min(1),
  type: z.string().min(1),
  protocol: z.string().min(1),
  auth: z.string().min(1),
  typicalSources: z.array(z.string()).default([]),
  latency: z.enum(["realtime", "near-realtime", "batch"]),
  modes: z.array(z.enum(["push", "pull", "stream", "file"])).default([]),
});
export type ConnectorPattern = z.infer<typeof ConnectorPattern>;

/** Glossary term entry. */
export const GlossaryTerm = z.object({
  name: z.string().min(1),
  aliases: z.array(z.string()).default([]),
  definition: z.string().min(1),
  related_subdomains: z.array(z.string()).default([]),
  related_kpis: z.array(z.string()).default([]),
  steward: z.string().optional(),
});
export type GlossaryTerm = z.infer<typeof GlossaryTerm>;
