import { describe, it, expect } from "vitest";
import { resolve } from "node:path";
import { existsSync, readFileSync } from "node:fs";
import {
  buildAdjacency,
  neighbourhood,
  personaToKpis,
  subgraphForVertical,
  type KgSnapshot,
} from "@/lib/kg";

const SNAP_PATH = resolve(__dirname, "..", "..", "..", "kg", "graph.json");
const HAS_SNAP = existsSync(SNAP_PATH);

const fixture: KgSnapshot = {
  schemaVersion: 1,
  stats: {
    nodes: 5,
    edges: 4,
    byKind: { vertical: 1, subdomain: 1, persona: 1, decision: 1, kpi: 1 },
  },
  nodes: [
    { id: "vertical:BFSI", kind: "vertical", label: "BFSI", x: 0, y: 0, extras: {} },
    { id: "subdomain:test", kind: "subdomain", label: "Test", vertical: "BFSI", x: 100, y: 0, extras: {} },
    { id: "persona:test::vp_a", kind: "persona", label: "VP A", subdomain: "test", x: 200, y: 0, extras: { id: "test::vp_a" } },
    { id: "decision:t.d.1", kind: "decision", label: "Decide", subdomain: "test", x: 300, y: 0, extras: { id: "t.d.1", statement: "Decide stuff." } },
    { id: "kpi:t.k.1", kind: "kpi", label: "K1", subdomain: "test", x: 400, y: 0, extras: { id: "t.k.1", formula: "a/b" } },
  ],
  edges: [
    { source: "vertical:BFSI", target: "subdomain:test", label: "hasSubdomain" },
    { source: "subdomain:test", target: "persona:test::vp_a", label: "hasPersona" },
    { source: "persona:test::vp_a", target: "decision:t.d.1", label: "owns" },
    { source: "kpi:t.k.1", target: "decision:t.d.1", label: "supportsDecision" },
  ],
};

describe("kg helpers", () => {
  it("buildAdjacency includes both directions per edge", () => {
    const adj = buildAdjacency(fixture);
    expect(adj.get("vertical:BFSI")?.length).toBe(1);
    expect(adj.get("subdomain:test")?.length).toBe(2);
    expect(adj.get("decision:t.d.1")?.length).toBe(2);
  });
  it("neighbourhood returns 1-hop neighbours and incident edges", () => {
    const out = neighbourhood(fixture, "subdomain:test");
    expect(out).not.toBeNull();
    expect(out!.neighbours.map((n) => n.id).sort()).toEqual([
      "persona:test::vp_a",
      "vertical:BFSI",
    ]);
    expect(out!.edges.length).toBe(2);
  });
  it("personaToKpis traverses persona->decision<-kpi", () => {
    const rows = personaToKpis(fixture, "persona:test::vp_a");
    expect(rows.length).toBe(1);
    expect(rows[0]?.decision.id).toBe("decision:t.d.1");
    expect(rows[0]?.kpis.map((k) => k.id)).toEqual(["kpi:t.k.1"]);
  });
  it("personaToKpis returns [] when persona has no owned decisions", () => {
    const rows = personaToKpis(fixture, "persona:bogus");
    expect(rows).toEqual([]);
  });
  it("subgraphForVertical filters around the vertical node", () => {
    const sub = subgraphForVertical(fixture, "BFSI", 50);
    expect(sub.nodes.find((n) => n.id === "vertical:BFSI")).toBeDefined();
    expect(sub.nodes.find((n) => n.id === "subdomain:test")).toBeDefined();
    // Disconnected nodes shouldn't appear (we don't have any in this fixture).
    expect(sub.stats.nodes).toBeLessThanOrEqual(fixture.nodes.length);
  });
  it("neighbourhood returns null for unknown nodes", () => {
    expect(neighbourhood(fixture, "vertical:Bogus")).toBeNull();
  });
});

describe.skipIf(!HAS_SNAP)("kg snapshot integrity", () => {
  it("graph.json parses and has 16 verticals", () => {
    const raw = JSON.parse(readFileSync(SNAP_PATH, "utf8")) as KgSnapshot;
    expect(raw.schemaVersion).toBe(1);
    expect(raw.stats.byKind.vertical).toBe(16);
    expect(raw.stats.nodes).toBeGreaterThan(500);
    expect(raw.stats.edges).toBeGreaterThan(500);
  });
  it("every edge endpoint resolves to a node", () => {
    const raw = JSON.parse(readFileSync(SNAP_PATH, "utf8")) as KgSnapshot;
    const ids = new Set(raw.nodes.map((n) => n.id));
    for (const e of raw.edges) {
      expect(ids.has(e.source), `dangling source: ${e.source}`).toBe(true);
      expect(ids.has(e.target), `dangling target: ${e.target}`).toBe(true);
    }
  });
});
