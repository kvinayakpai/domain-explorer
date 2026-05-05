import "server-only";
import { readFileSync, existsSync } from "node:fs";
import { dirname, resolve } from "node:path";

/**
 * Knowledge graph client.
 *
 * The KG is built by `python kg/build_graph.py` which emits both
 * `kg/graph.gpickle` (NetworkX binary, used by the FastAPI service) and
 * `kg/graph.json` (precomputed force-directed snapshot).
 *
 * In the browser/server runtime we stick with the JSON snapshot — fast to
 * load, no native dep, identical to what the API would serve from
 * `GET /kg/snapshot`.
 *
 * The assistant grounding layer prefers calling the API at
 * `process.env.KG_API_URL` (so demos can show "live KG traversal") and
 * falls back to the JSON snapshot when the API isn't reachable.
 */

export interface KgNode {
  id: string;
  kind: string;
  label: string;
  vertical?: string | null;
  subdomain?: string | null;
  x: number;
  y: number;
  extras: Record<string, unknown>;
}

export interface KgEdge {
  source: string;
  target: string;
  label: string;
}

export interface KgSnapshot {
  schemaVersion: number;
  stats: { nodes: number; edges: number; byKind: Record<string, number> };
  nodes: KgNode[];
  edges: KgEdge[];
}

let cached: KgSnapshot | null = null;

function findKgJson(): string | null {
  let dir = resolve(process.cwd());
  for (let i = 0; i < 8; i++) {
    const candidate = resolve(dir, "kg", "graph.json");
    if (existsSync(candidate)) return candidate;
    const parent = dirname(dir);
    if (parent === dir) break;
    dir = parent;
  }
  return null;
}

export function loadKgSnapshot(): KgSnapshot | null {
  if (cached) return cached;
  const path = findKgJson();
  if (!path) return null;
  cached = JSON.parse(readFileSync(path, "utf8")) as KgSnapshot;
  return cached;
}

/** Return adjacency as a Map<nodeId, edges>. */
export function buildAdjacency(snap: KgSnapshot): Map<string, KgEdge[]> {
  const adj = new Map<string, KgEdge[]>();
  for (const e of snap.edges) {
    if (!adj.has(e.source)) adj.set(e.source, []);
    if (!adj.has(e.target)) adj.set(e.target, []);
    adj.get(e.source)!.push(e);
    adj.get(e.target)!.push(e);
  }
  return adj;
}

/** 1-hop neighbourhood for a node. */
export function neighbourhood(
  snap: KgSnapshot,
  nodeId: string,
): { node: KgNode; neighbours: KgNode[]; edges: KgEdge[] } | null {
  const node = snap.nodes.find((n) => n.id === nodeId);
  if (!node) return null;
  const adj = buildAdjacency(snap);
  const edges = adj.get(nodeId) ?? [];
  const seen = new Set<string>();
  const neighbours: KgNode[] = [];
  for (const e of edges) {
    const other = e.source === nodeId ? e.target : e.source;
    if (seen.has(other)) continue;
    seen.add(other);
    const nn = snap.nodes.find((x) => x.id === other);
    if (nn) neighbours.push(nn);
  }
  return { node, neighbours, edges };
}

/** Traverse persona → owns → decision ← supportsDecision ← KPI. */
export function personaToKpis(
  snap: KgSnapshot,
  personaId: string,
): { decision: KgNode; kpis: KgNode[] }[] {
  const out: { decision: KgNode; kpis: KgNode[] }[] = [];
  const decisions = snap.edges
    .filter((e) => e.source === personaId && e.label === "owns")
    .map((e) => snap.nodes.find((n) => n.id === e.target))
    .filter((n): n is KgNode => !!n && n.kind === "decision");
  for (const d of decisions) {
    const kpis = snap.edges
      .filter((e) => e.target === d.id && e.label === "supportsDecision")
      .map((e) => snap.nodes.find((n) => n.id === e.source))
      .filter((n): n is KgNode => !!n && n.kind === "kpi");
    out.push({ decision: d, kpis });
  }
  return out;
}

/** Filter the graph to subgraphs anchored on a vertical (for demo / /kg view). */
export function subgraphForVertical(
  snap: KgSnapshot,
  verticalSlug: string,
  maxNodes = 50,
): KgSnapshot {
  const verticalId = `vertical:${verticalSlug}`;
  const seeds = new Set<string>([verticalId]);
  for (const e of snap.edges) {
    if (e.source === verticalId) seeds.add(e.target);
  }
  // Expand to subdomains' personas + KPIs.
  for (const e of snap.edges) {
    if (
      seeds.has(e.source) &&
      (e.label === "hasPersona" || e.label === "hasKpi" || e.label === "hasEntity")
    ) {
      seeds.add(e.target);
    }
  }
  // Trim to maxNodes — biased toward subdomains + KPIs first.
  const sorted = Array.from(seeds).sort((a, b) => {
    const ra = priorityForKind(snap.nodes.find((n) => n.id === a)?.kind);
    const rb = priorityForKind(snap.nodes.find((n) => n.id === b)?.kind);
    return ra - rb;
  });
  const keep = new Set(sorted.slice(0, maxNodes));
  const nodes = snap.nodes.filter((n) => keep.has(n.id));
  const edges = snap.edges.filter((e) => keep.has(e.source) && keep.has(e.target));
  const counts: Record<string, number> = {};
  for (const n of nodes) counts[n.kind] = (counts[n.kind] ?? 0) + 1;
  return {
    schemaVersion: snap.schemaVersion,
    stats: { nodes: nodes.length, edges: edges.length, byKind: counts },
    nodes,
    edges,
  };
}

function priorityForKind(kind: string | undefined): number {
  switch (kind) {
    case "vertical":
      return 0;
    case "subdomain":
      return 1;
    case "kpi":
      return 2;
    case "persona":
      return 3;
    case "entity":
      return 4;
    case "decision":
      return 5;
    default:
      return 9;
  }
}

/** Try to call the live API (optional); fall back to local snapshot. */
export async function callKgApi<T = unknown>(
  pathSeg: string,
  init?: RequestInit,
): Promise<T | null> {
  const base = process.env.KG_API_URL;
  if (!base) return null;
  try {
    const res = await fetch(`${base.replace(/\/$/, "")}${pathSeg}`, {
      cache: "no-store",
      ...init,
    });
    if (!res.ok) return null;
    return (await res.json()) as T;
  } catch {
    return null;
  }
}
