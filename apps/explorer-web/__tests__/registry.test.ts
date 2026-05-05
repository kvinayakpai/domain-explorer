import { describe, it, expect } from "vitest";
import { resolve } from "node:path";
import { existsSync, readdirSync } from "node:fs";
import { loadRegistry } from "@domain-explorer/metadata";

const REPO_DATA = resolve(__dirname, "..", "..", "..", "data");
const HAS_DATA = existsSync(resolve(REPO_DATA, "taxonomy"));

describe.skipIf(!HAS_DATA)("loadRegistry against the real data/", () => {
  it("loads >= 80 subdomains", () => {
    const reg = loadRegistry(REPO_DATA);
    expect(reg.subdomains.length).toBeGreaterThanOrEqual(80);
  });
  it("loads at least one KPI from the cross-vertical registry", () => {
    const reg = loadRegistry(REPO_DATA);
    expect(reg.kpis.length).toBeGreaterThan(0);
  });
  it("loads at least one source system", () => {
    const reg = loadRegistry(REPO_DATA);
    expect(reg.sourceSystems.length).toBeGreaterThan(0);
  });
  it("loads at least one connector pattern", () => {
    const reg = loadRegistry(REPO_DATA);
    expect(reg.connectors.length).toBeGreaterThan(0);
  });
  it("loads glossary terms", () => {
    const reg = loadRegistry(REPO_DATA);
    expect(reg.glossary.length).toBeGreaterThan(0);
  });
  it("every subdomain has at least one persona", () => {
    const reg = loadRegistry(REPO_DATA);
    for (const s of reg.subdomains) {
      expect(s.personas.length, `${s.id} missing personas`).toBeGreaterThan(0);
    }
  });
  it("subdomain count matches taxonomy YAML count", () => {
    const reg = loadRegistry(REPO_DATA);
    const onDisk = readdirSync(resolve(REPO_DATA, "taxonomy")).filter(
      (f) => f.endsWith(".yaml") || f.endsWith(".yml"),
    ).length;
    expect(reg.subdomains.length).toBe(onDisk);
  });
  it("subdomains include the BFSI Payments anchor", () => {
    const reg = loadRegistry(REPO_DATA);
    const payments = reg.subdomains.find((s) => s.id === "payments");
    expect(payments).toBeDefined();
    expect(payments?.vertical).toBe("BFSI");
    expect(payments?.kpis.length).toBeGreaterThanOrEqual(4);
  });
});
