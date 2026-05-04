/**
 * Re-exports the canonical types from @domain-explorer/metadata so
 * downstream apps can `import type { Subdomain } from "@domain-explorer/shared-types"`
 * without pulling in Zod runtime.
 */
export type {
  Connector,
  ConnectorPattern,
  DataModel,
  Decision,
  Entity,
  Kpi,
  KpiDirection,
  KpiRegistryEntry,
  Persona,
  SourceSystem,
  SourceSystemEntry,
  Subdomain,
  Vertical,
} from "@domain-explorer/metadata";
