import { describe, it, expect } from "vitest";
import {
  Subdomain,
  Persona,
  Kpi,
  Connector,
  ConnectorPattern,
  KpiRegistryEntry,
  SourceSystemEntry,
  GlossaryTerm,
} from "@domain-explorer/metadata/schema";

describe("Persona schema", () => {
  it("accepts known levels", () => {
    expect(() =>
      Persona.parse({ name: "X", title: "Head of X", level: "VP" }),
    ).not.toThrow();
  });
  it("rejects unknown level", () => {
    expect(() =>
      Persona.parse({ name: "X", title: "Head of X", level: "Wizard" }),
    ).toThrow();
  });
  it("rejects empty name", () => {
    expect(() =>
      Persona.parse({ name: "", title: "x", level: "Director" }),
    ).toThrow();
  });
});

describe("Kpi schema", () => {
  const base = {
    id: "k.x",
    name: "X",
    formula: "a/b",
    unit: "%",
    direction: "higher_is_better" as const,
  };
  it("accepts a well-formed KPI", () => {
    expect(() => Kpi.parse({ ...base, decisionsSupported: ["d.1"] })).not.toThrow();
  });
  it("defaults decisionsSupported to []", () => {
    const out = Kpi.parse(base);
    expect(out.decisionsSupported).toEqual([]);
  });
  it("rejects bogus direction", () => {
    expect(() => Kpi.parse({ ...base, direction: "up" })).toThrow();
  });
});

describe("Connector / ConnectorPattern", () => {
  it("Connector requires type/protocol/auth", () => {
    expect(() =>
      Connector.parse({ type: "REST", protocol: "HTTPS", auth: "OAuth" }),
    ).not.toThrow();
    expect(() => Connector.parse({ type: "REST" })).toThrow();
  });
  it("ConnectorPattern enforces latency enum", () => {
    expect(() =>
      ConnectorPattern.parse({
        id: "c.x",
        type: "REST",
        protocol: "HTTPS",
        auth: "OAuth",
        latency: "instant",
      }),
    ).toThrow();
    expect(() =>
      ConnectorPattern.parse({
        id: "c.x",
        type: "REST",
        protocol: "HTTPS",
        auth: "OAuth",
        latency: "realtime",
      }),
    ).not.toThrow();
  });
});

describe("Subdomain schema", () => {
  const ok = {
    id: "test_sub",
    name: "Test",
    vertical: "BFSI" as const,
    oneLiner: "x",
    personas: [{ name: "X", title: "Head of X", level: "VP" as const }],
  };
  it("accepts a minimal valid subdomain", () => {
    expect(() => Subdomain.parse(ok)).not.toThrow();
  });
  it("requires at least one persona", () => {
    expect(() => Subdomain.parse({ ...ok, personas: [] })).toThrow();
  });
  it("rejects unknown vertical", () => {
    expect(() => Subdomain.parse({ ...ok, vertical: "Bogus" })).toThrow();
  });
  it("defaults dataModel.entities to []", () => {
    const out = Subdomain.parse(ok);
    expect(out.dataModel.entities).toEqual([]);
  });
  it("propagates kpi.decisionsSupported", () => {
    const out = Subdomain.parse({
      ...ok,
      decisions: [{ id: "d.1", statement: "x" }],
      kpis: [
        {
          id: "k.1",
          name: "K1",
          formula: "a/b",
          unit: "%",
          direction: "higher_is_better",
          decisionsSupported: ["d.1"],
        },
      ],
    });
    expect(out.kpis[0]?.decisionsSupported).toEqual(["d.1"]);
  });
});

describe("KpiRegistryEntry / SourceSystemEntry / GlossaryTerm", () => {
  it("KpiRegistryEntry inherits Kpi shape and adds vertical", () => {
    expect(() =>
      KpiRegistryEntry.parse({
        id: "k.1",
        name: "K1",
        formula: "a/b",
        unit: "%",
        direction: "higher_is_better",
        vertical: "BFSI",
      }),
    ).not.toThrow();
  });
  it("SourceSystemEntry primaryConnectors defaults to []", () => {
    const out = SourceSystemEntry.parse({
      id: "s.x",
      vendor: "V",
      product: "P",
      category: "C",
    });
    expect(out.primaryConnectors).toEqual([]);
  });
  it("GlossaryTerm requires definition", () => {
    expect(() =>
      GlossaryTerm.parse({ name: "ACH", definition: "" }),
    ).toThrow();
    expect(() =>
      GlossaryTerm.parse({ name: "ACH", definition: "Automated Clearing House" }),
    ).not.toThrow();
  });
});
