import { readFileSync, readdirSync } from "node:fs";
import { join, resolve } from "node:path";
import { parse as parseYaml } from "yaml";
import {
  ConnectorPattern,
  GlossaryTerm,
  KpiRegistryEntry,
  SourceSystemEntry,
  Subdomain,
} from "./schema";
import type {
  ConnectorPattern as ConnectorPatternT,
  GlossaryTerm as GlossaryTermT,
  KpiRegistryEntry as KpiRegistryEntryT,
  SourceSystemEntry as SourceSystemEntryT,
  Subdomain as SubdomainT,
} from "./schema";

const DATA_ROOT = resolve(process.cwd(), "data");

function readYamlDir(dir: string): unknown[] {
  let entries: string[];
  try {
    entries = readdirSync(dir);
  } catch {
    return [];
  }
  return entries
    .filter((f) => f.endsWith(".yaml") || f.endsWith(".yml"))
    .map((f) => parseYaml(readFileSync(join(dir, f), "utf8")));
}

export interface Registry {
  subdomains: SubdomainT[];
  kpis: KpiRegistryEntryT[];
  sourceSystems: SourceSystemEntryT[];
  connectors: ConnectorPatternT[];
  glossary: GlossaryTermT[];
}

export function loadRegistry(dataRoot: string = DATA_ROOT): Registry {
  const subdomains = readYamlDir(join(dataRoot, "taxonomy")).map((raw) =>
    Subdomain.parse(raw),
  );
  const kpis = readYamlDir(join(dataRoot, "kpis")).flatMap((raw) => {
    const list = (raw as { kpis?: unknown[] } | null)?.kpis ?? [];
    return list.map((k) => KpiRegistryEntry.parse(k));
  });
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
  return { subdomains, kpis, sourceSystems, connectors, glossary };
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
