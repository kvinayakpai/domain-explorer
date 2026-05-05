import "server-only";
import { registry, VERTICALS } from "@/lib/registry";
import type { Subdomain } from "@domain-explorer/metadata";

/**
 * Vertical-anchored demo flows.
 *
 * Each vertical maps to a "hero subdomain" — preferring one we have full DDL
 * + populated data for, falling back to the highest-leverage subdomain in the
 * vertical otherwise. The /demo/[vertical] route uses this mapping.
 */

/** Subdomains we have fully wired (DDL + populated DuckDB schema). */
export const ANCHORED_SUBDOMAINS = new Set<string>([
  "payments",
  "p_and_c_claims",
  "merchandising",
  "demand_planning",
  "hotel_revenue_management",
  "mes_quality",
  "pharmacovigilance",
]);

/**
 * Hero subdomain per vertical. The first matching id (against the loaded
 * registry) wins — we keep multiple candidates per vertical in case a
 * subdomain hasn't been seeded yet.
 */
const HERO_BY_VERTICAL: Record<string, string[]> = {
  BFSI: ["payments", "cards", "lending", "capital_markets"],
  Insurance: ["p_and_c_claims", "underwriting", "policy_admin"],
  Retail: ["merchandising", "ecommerce", "store_ops"],
  RCG: ["pricing", "supply_chain"],
  CPG: ["demand_planning", "trade_promotion", "retail_execution"],
  TTH: [
    "hotel_revenue_management",
    "airline_revenue_management",
    "ride_share_dispatch",
  ],
  Manufacturing: ["mes_quality", "predictive_maintenance", "bill_of_materials"],
  LifeSciences: ["pharmacovigilance", "clinical_trials", "pharma_supply_chain"],
  Healthcare: ["revenue_cycle", "ehr_integrations", "clinical_decision_support"],
  Telecom: ["subscriber_billing", "network_operations", "churn_management"],
  Media: ["programmatic_advertising", "content_metadata", "video_streaming_qoe"],
  Energy: ["energy_trading", "grid_ops", "renewable_generation"],
  Utilities: ["smart_metering", "outage_management", "water_utilities"],
  PublicSector: ["benefits_administration", "tax_administration", "court_records"],
  HiTech: ["cloud_finops", "device_telemetry", "saas_metrics"],
  ProfessionalServices: ["time_and_billing", "legal_case_management", "audit_workflow"],
};

export interface DemoFlowMeta {
  verticalSlug: string;
  verticalLabel: string;
  hero: Subdomain;
  hasFullStack: boolean;
  fallbackChain: string[];
}

export function listDemoFlows(): DemoFlowMeta[] {
  const reg = registry();
  const out: DemoFlowMeta[] = [];
  for (const v of VERTICALS) {
    const candidates = HERO_BY_VERTICAL[v.slug] ?? [];
    let hero: Subdomain | undefined;
    for (const id of candidates) {
      const sd = reg.subdomains.find((s) => s.id === id && s.vertical === v.slug);
      if (sd) {
        hero = sd;
        break;
      }
    }
    if (!hero) {
      // Pick the first subdomain in the vertical with the most KPIs as a tiebreaker.
      const inV = reg.subdomains.filter((s) => s.vertical === v.slug);
      inV.sort((a, b) => (b.kpis?.length ?? 0) - (a.kpis?.length ?? 0));
      hero = inV[0];
    }
    if (!hero) continue;
    out.push({
      verticalSlug: v.slug,
      verticalLabel: v.label,
      hero,
      hasFullStack: ANCHORED_SUBDOMAINS.has(hero.id),
      fallbackChain: candidates,
    });
  }
  return out;
}

export function getDemoFlow(verticalSlug: string): DemoFlowMeta | null {
  return listDemoFlows().find((f) => f.verticalSlug === verticalSlug) ?? null;
}

/** Three personas + 3 decisions each = the "pain" panel for screen 1. */
export function painForHero(hero: Subdomain): Array<{
  persona: { name: string; title: string; level: string };
  decisions: { id: string; statement: string }[];
}> {
  return hero.personas.slice(0, 2).map((p) => ({
    persona: { name: p.name, title: p.title, level: p.level },
    // Decisions are at the subdomain level (not per-persona in the YAML),
    // so each persona sees the top 3 owned by the subdomain.
    decisions: hero.decisions.slice(0, 3).map((d) => ({ id: d.id, statement: d.statement })),
  }));
}

/** KPI rollup for screen 2 — top 5 with linked source-system vendors. */
export function kpisWithLineage(
  hero: Subdomain,
): Array<{
  kpi: (typeof hero.kpis)[number];
  sources: { vendor: string; product: string; category: string }[];
}> {
  const sources = hero.sourceSystems.slice(0, 4);
  return hero.kpis.slice(0, 5).map((k) => ({ kpi: k, sources }));
}

/** Stack tiers for screen 3 — how data flows from sources to consumption. */
export function platformStack(hero: Subdomain): {
  sources: { vendor: string; product: string; category: string }[];
  ingest: string[];
  integrate: string[];
  model: string[];
  consume: string[];
} {
  return {
    sources: hero.sourceSystems.slice(0, 6),
    ingest: hero.connectors.slice(0, 4).map((c) => `${c.type} (${c.protocol})`),
    integrate: hero.ingestionChallenges.slice(0, 3),
    model: (hero.dataModel?.entities ?? []).slice(0, 5).map((e) => e.name),
    consume: hero.kpis.slice(0, 4).map((k) => k.name),
  };
}
