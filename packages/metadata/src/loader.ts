import { existsSync, readFileSync, readdirSync } from "node:fs";
import { join, resolve } from "node:path";
import { parse as parseYaml } from "yaml";
import {
  ConnectorPattern,
  GlossaryTerm,
  KpiMasterEntry,
  KpiRegistryEntry,
  KpiSqlSpec,
  SourceSystemEntry,
  Subdomain,
} from "./schema";
import type {
  ConnectorPattern as ConnectorPatternT,
  GlossaryTerm as GlossaryTermT,
  KpiMasterEntry as KpiMasterEntryT,
  KpiRegistryEntry as KpiRegistryEntryT,
  KpiSqlSpec as KpiSqlSpecT,
  SourceSystemEntry as SourceSystemEntryT,
  Subdomain as SubdomainT,
} from "./schema";

const DATA_ROOT = resolve(process.cwd(), "data");

function readYamlDir(dir: string, exclude: string[] = []): unknown[] {
  let entries: string[];
  try {
    entries = readdirSync(dir);
  } catch {
    return [];
  }
  return entries
    .filter((f) => f.endsWith(".yaml") || f.endsWith(".yml"))
    .filter((f) => !exclude.includes(f))
    .map((f) => parseYaml(readFileSync(join(dir, f), "utf8")));
}

function readYamlFile(file: string): unknown {
  if (!existsSync(file)) return null;
  return parseYaml(readFileSync(file, "utf8"));
}

export interface Registry {
  subdomains: SubdomainT[];
  kpis: KpiRegistryEntryT[];
  sourceSystems: SourceSystemEntryT[];
  connectors: ConnectorPatternT[];
  glossary: GlossaryTermT[];
  kpiMaster: KpiMasterEntryT[];
  kpiSql: KpiSqlSpecT[];
}

export function loadRegistry(dataRoot: string = DATA_ROOT): Registry {
  const subdomains = readYamlDir(join(dataRoot, "taxonomy")).map((raw) =>
    Subdomain.parse(raw),
  );
  // Skip master.yaml + sql.yaml here; they're loaded via dedicated helpers
  // because they carry richer (forbidden-extra) fields and may not have
  // `vertical` populated for every entry.
  const kpis = readYamlDir(join(dataRoot, "kpis"), ["master.yaml", "sql.yaml"])
    .flatMap((raw) => {
      const list = (raw as { kpis?: unknown[] } | null)?.kpis ?? [];
      return list;
    })
    .map((k) => {
      try {
        return KpiRegistryEntry.parse(k);
      } catch {
        return null;
      }
    })
    .filter((k): k is KpiRegistryEntryT => k !== null);
  const sourceSystems = readYamlDir(join(dataRoot, "source-systems")).flatMap(
    (raw) => {
      const list = (raw as { sources?: unknown[] } | null)?.sources ?? [];
      return list.map((s) => SourceSystemEntry.parse(s));
    },
  );
  const connectors = readYamlDir(join(dataRoot, "connectors")).flatMap(
    (raw) => {
      const list = (raw as { connectors?: unknown[] } | null)?.connectors ?? [];
      return list.map((c) => ConnectorPattern.parse(c));
    },
  );
  const glossary = readYamlDir(join(dataRoot, "glossary")).flatMap((raw) => {
    const list = (raw as { terms?: unknown[] } | null)?.terms ?? [];
    return list.map((t) => GlossaryTerm.parse(t));
  });
  const masterRaw = readYamlFile(join(dataRoot, "kpis", "master.yaml")) as
    | { kpis?: unknown[] }
    | null;
  const kpiMaster = (masterRaw?.kpis ?? []).map((k) => KpiMasterEntry.parse(k));
  const sqlRaw = readYamlFile(join(dataRoot, "kpis", "sql.yaml")) as
    | { kpis?: unknown[] }
    | null;
  const kpiSql = (sqlRaw?.kpis ?? []).map((k) => KpiSqlSpec.parse(k));
  return {
    subdomains,
    kpis,
    sourceSystems,
    connectors,
    glossary,
    kpiMaster,
    kpiSql,
  };
}

export function getSubdomain(
  registry: Registry,
  id: string,
): SubdomainT | undefined {
  return registry.subdomains.find((s) => s.id === id);
}

export function getSubdomainsByVertical(
  registry: Registry,
  vertical: string,
): SubdomainT[] {
  return registry.subdomains.filter((s) => s.vertical === vertical);
}

export function getKpi(
  registry: Registry,
  id: string,
): KpiRegistryEntryT | undefined {
  return registry.kpis.find((k) => k.id === id);
}

export function getSourceSystem(
  registry: Registry,
  id: string,
): SourceSystemEntryT | undefined {
  return registry.sourceSystems.find((s) => s.id === id);
}

export function getKpiMaster(
  registry: Registry,
  id: string,
): KpiMasterEntryT | undefined {
  return registry.kpiMaster.find((k) => k.id === id);
}

export function getKpiSql(
  registry: Registry,
  id: string,
): KpiSqlSpecT | undefined {
  return registry.kpiSql.find((k) => k.kpi_id === id);
}
