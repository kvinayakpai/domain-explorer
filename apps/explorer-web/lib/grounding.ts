import "server-only";
import type { Subdomain, Persona, Kpi } from "@domain-explorer/metadata";
import { registry } from "@/lib/registry";
import {
  callKgApi,
  loadKgSnapshot,
  personaToKpis as kgPersonaToKpis,
} from "@/lib/kg";

export interface PersonaOption {
  /** unique key: subdomainId::personaName */
  key: string;
  subdomainId: string;
  subdomainName: string;
  vertical: string;
  name: string;
  title: string;
  level: string;
}

/** Flatten every persona across the registry into a selectable list. */
export function listPersonaOptions(): PersonaOption[] {
  const reg = registry();
  const out: PersonaOption[] = [];
  for (const sd of reg.subdomains) {
    for (const p of sd.personas) {
      out.push({
        key: `${sd.id}::${p.name}`,
        subdomainId: sd.id,
        subdomainName: sd.name,
        vertical: sd.vertical,
        name: p.name,
        title: p.title,
        level: p.level,
      });
    }
  }
  return out;
}

export interface GroundingBundle {
  persona?: PersonaOption;
  subdomain?: Subdomain;
  matchedSubdomains: Subdomain[];
  kpis: Kpi[];
  sourceSystems: { vendor: string; product: string; category: string }[];
  connectorPatterns: { type: string; protocol: string; auth: string }[];
  decisionsChain: {
    persona: Persona;
    decisions: { id: string; statement: string; supportingKpis: Kpi[] }[];
  } | null;
  /** Human-readable provenance — which YAML records were pulled. */
  recordsUsed: string[];
  /** Which backend was used: "kg-api", "kg-snapshot", or "yaml-direct". */
  backend: "kg-api" | "kg-snapshot" | "yaml-direct";
}

/** Light keyword scoring across subdomain content for question-driven retrieval. */
function scoreSubdomain(sd: Subdomain, q: string): number {
  if (!q.trim()) return 0;
  const haystack = [
    sd.id,
    sd.name,
    sd.vertical,
    sd.oneLiner,
    ...sd.personas.map((p) => `${p.name} ${p.title}`),
    ...sd.kpis.map((k) => `${k.id} ${k.name}`),
    ...sd.decisions.map((d) => d.statement),
    ...sd.sourceSystems.map((s) => `${s.vendor} ${s.product} ${s.category}`),
  ]
    .join(" ")
    .toLowerCase();
  const tokens = q
    .toLowerCase()
    .split(/[^a-z0-9]+/)
    .filter((t) => t.length > 2);
  let score = 0;
  for (const t of tokens) {
    if (haystack.includes(t)) score += 1;
  }
  return score;
}

/**
 * Build the grounding bundle the assistant sees.
 *
 * Mirrors the openCypher templates under `kg/cypher/` —
 * persona → decisions → KPIs → source systems → connectors.
 *
 * Resolution order:
 * 1. If `KG_API_URL` is set, call the live FastAPI service (NetworkX-backed).
 * 2. Else, load `kg/graph.json` and traverse in-process.
 * 3. Else, fall back to the YAML registry directly.
 *
 * The YAML registry is always loaded too — it's our source of truth for
 * subdomain detail like one-liners and ingestion challenges that aren't
 * stored verbatim in the graph.
 */
export function buildGrounding(opts: {
  question: string;
  personaKey?: string;
}): GroundingBundle {
  const reg = registry();
  const recordsUsed: string[] = [];
  const snap = loadKgSnapshot();
  const backend: GroundingBundle["backend"] = snap ? "kg-snapshot" : "yaml-direct";

  // 1. Resolve persona, if any.
  let persona: PersonaOption | undefined;
  let subdomain: Subdomain | undefined;
  if (opts.personaKey) {
    const [sdId, ...rest] = opts.personaKey.split("::");
    const personaName = rest.join("::");
    const sd = reg.subdomains.find((s) => s.id === sdId);
    if (sd) {
      const p = sd.personas.find((px) => px.name === personaName);
      if (p) {
        persona = {
          key: opts.personaKey,
          subdomainId: sd.id,
          subdomainName: sd.name,
          vertical: sd.vertical,
          name: p.name,
          title: p.title,
          level: p.level,
        };
        subdomain = sd;
        recordsUsed.push(`taxonomy/${sd.id}.yaml#personas[${p.name}]`);
      }
    }
  }

  // 2. Score remaining subdomains by keyword match — pull the top 3 as backup context.
  const ranked = reg.subdomains
    .map((s) => ({ sd: s, score: scoreSubdomain(s, opts.question) }))
    .filter((r) => r.score > 0)
    .sort((a, b) => b.score - a.score)
    .slice(0, 3)
    .map((r) => r.sd);

  // If the persona's subdomain isn't already in the ranked list, prepend it.
  const matchedSubdomains: Subdomain[] = [];
  if (subdomain) matchedSubdomains.push(subdomain);
  for (const sd of ranked) {
    if (!matchedSubdomains.find((m) => m.id === sd.id)) matchedSubdomains.push(sd);
  }
  for (const sd of matchedSubdomains) {
    if (sd.id !== subdomain?.id) recordsUsed.push(`taxonomy/${sd.id}.yaml`);
  }

  // 3. Decisions chain for the persona's subdomain (persona → decisions → KPIs).
  let decisionsChain: GroundingBundle["decisionsChain"] = null;
  if (persona && subdomain) {
    // Try KG-snapshot traversal first; if it returns nothing, fall back to YAML.
    let decisions: { id: string; statement: string; supportingKpis: Kpi[] }[] = [];
    if (snap) {
      const personaSlug = personaSlugFor(persona);
      const personaNodeId = `persona:${persona.subdomainId}::${personaSlug}`;
      const traversed = kgPersonaToKpis(snap, personaNodeId);
      if (traversed.length) {
        decisions = traversed.map((row) => ({
          id: row.decision.extras["id"] as string,
          statement: (row.decision.extras["statement"] as string) ?? row.decision.label,
          supportingKpis: row.kpis
            .map((k) => subdomain!.kpis.find((kk) => kk.id === (k.extras["id"] as string)))
            .filter((kk): kk is Kpi => !!kk),
        }));
        recordsUsed.push(`kg/graph.json#${personaNodeId} (persona->decisions->KPIs)`);
      }
    }
    if (decisions.length === 0) {
      decisions = subdomain.decisions.map((d) => {
        const supportingKpis = subdomain!.kpis.filter((k) =>
          k.decisionsSupported.includes(d.id),
        );
        return { id: d.id, statement: d.statement, supportingKpis };
      });
    }
    decisionsChain = {
      persona: { name: persona.name, title: persona.title, level: persona.level as Persona["level"] },
      decisions,
    };
  }

  // 4. KPIs - union of matched subdomain KPIs.
  const kpis: Kpi[] = [];
  for (const sd of matchedSubdomains) {
    for (const k of sd.kpis) {
      if (!kpis.find((x) => x.id === k.id)) kpis.push(k);
    }
  }

  // 5. Source systems and connector patterns from matched subdomains.
  const sourceSystems = matchedSubdomains.flatMap((s) => s.sourceSystems).slice(0, 12);
  const connectorPatterns = matchedSubdomains.flatMap((s) => s.connectors).slice(0, 12);

  return {
    persona,
    subdomain,
    matchedSubdomains,
    kpis,
    sourceSystems,
    connectorPatterns,
    decisionsChain,
    recordsUsed,
    backend,
  };
}

function personaSlugFor(p: PersonaOption): string {
  return p.name
    .toLowerCase()
    .split("")
    .map((ch) => (/[a-z0-9]/.test(ch) ? ch : "_"))
    .join("")
    .replace(/_+/g, "_")
    .replace(/^_|_$/g, "");
}

/**
 * Async variant that prefers the live KG API if `KG_API_URL` is set.
 *
 * Returns the same {@link GroundingBundle} shape so callers can swap in
 * place. Falls back to the synchronous {@link buildGrounding} if the API
 * is unreachable.
 */
export async function buildGroundingAsync(opts: {
  question: string;
  personaKey?: string;
}): Promise<GroundingBundle> {
  const base = process.env.KG_API_URL;
  if (!base) return buildGrounding(opts);
  // Best-effort liveness check.
  const stats = await callKgApi<{ nodes: number }>("/kg/stats");
  if (!stats) return buildGrounding(opts);
  const bundle = buildGrounding(opts);
  return { ...bundle, backend: "kg-api", recordsUsed: [...bundle.recordsUsed, `kg-api: ${base}`] };
}

/** Compact text bundle for the LLM (or for the canned-response template). */
export function renderGroundingForLlm(g: GroundingBundle): string {
  const lines: string[] = [];
  lines.push(
    `=== GROUNDING CONTEXT (backend: ${g.backend}) ===`,
  );
  if (g.persona) {
    lines.push(
      `PERSONA: ${g.persona.name} (${g.persona.title}, ${g.persona.level}) in subdomain "${g.persona.subdomainName}" / vertical ${g.persona.vertical}.`,
    );
  }
  if (g.matchedSubdomains.length) {
    lines.push("");
    lines.push("MATCHED SUBDOMAINS:");
    for (const sd of g.matchedSubdomains) {
      lines.push(`- ${sd.name} (${sd.vertical}, id=${sd.id}): ${sd.oneLiner}`);
    }
  }
  if (g.decisionsChain) {
    lines.push("");
    lines.push(`DECISIONS THIS PERSONA OWNS (with supporting KPIs):`);
    for (const d of g.decisionsChain.decisions) {
      lines.push(`- ${d.id}: ${d.statement}`);
      for (const k of d.supportingKpis) {
        lines.push(`    KPI: ${k.name} (${k.id}) = ${k.formula} [${k.unit}, ${k.direction}]`);
      }
    }
  }
  if (g.kpis.length) {
    lines.push("");
    lines.push(`KPIs IN SCOPE (${g.kpis.length}):`);
    for (const k of g.kpis.slice(0, 12)) {
      lines.push(`- ${k.name} (${k.id}): ${k.formula} - ${k.unit}, ${k.direction}`);
    }
  }
  if (g.sourceSystems.length) {
    lines.push("");
    lines.push(`SOURCE SYSTEMS:`);
    for (const s of g.sourceSystems) {
      lines.push(`- ${s.vendor} ${s.product} (${s.category})`);
    }
  }
  if (g.connectorPatterns.length) {
    lines.push("");
    lines.push(`CONNECTOR PATTERNS:`);
    for (const c of g.connectorPatterns) {
      lines.push(`- ${c.type} via ${c.protocol} (auth: ${c.auth})`);
    }
  }
  return lines.join("\n");
}

/** Deterministic canned answer used when no API key is configured. */
export function buildCannedAnswer(question: string, g: GroundingBundle): string {
  const parts: string[] = [];
  parts.push("(demo mode - set ANTHROPIC_API_KEY for live answers)");
  parts.push("");
  if (g.persona) {
    parts.push(
      `For **${g.persona.name}** (${g.persona.title}) in **${g.persona.subdomainName}**:`,
    );
  } else if (g.matchedSubdomains[0]) {
    const sd = g.matchedSubdomains[0];
    parts.push(`Based on **${sd.name}** (${sd.vertical}):`);
  } else {
    parts.push("I couldn't ground this question against a specific subdomain. Try selecting a persona or asking about a known subdomain (e.g. payments, hotel revenue management).");
    return parts.join("\n");
  }
  parts.push("");
  if (g.decisionsChain && g.decisionsChain.decisions.length) {
    parts.push("Key decisions this persona owns:");
    for (const d of g.decisionsChain.decisions.slice(0, 4)) {
      parts.push(`- ${d.statement}`);
      if (d.supportingKpis.length) {
        const kpiNames = d.supportingKpis.map((k) => k.name).join(", ");
        parts.push(`  Supported by KPIs: ${kpiNames}.`);
      }
    }
    parts.push("");
  }
  if (g.kpis.length) {
    parts.push(`Top KPIs in scope: ${g.kpis.slice(0, 6).map((k) => k.name).join(", ")}.`);
  }
  if (g.sourceSystems.length) {
    parts.push(
      `Likely source systems: ${g.sourceSystems.slice(0, 5).map((s) => `${s.vendor} ${s.product}`).join(", ")}.`,
    );
  }
  if (g.connectorPatterns.length) {
    parts.push(
      `Common connector patterns: ${g.connectorPatterns.slice(0, 4).map((c) => `${c.type} (${c.protocol})`).join(", ")}.`,
    );
  }
  parts.push("");
  parts.push(`Question understood: "${question.trim()}"`);
  return parts.join("\n");
}
