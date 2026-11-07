import { describe, expect, it } from "vitest";
import { SUBDOMAIN_DEMOS } from "@/lib/demos";
import { loadRegistry } from "@domain-explorer/metadata";
import path from "node:path";

describe("subdomain demos", () => {
  it("only point at subdomains that exist", async () => {
    const reg = await loadRegistry(path.resolve(__dirname, "../../../data"));
    const ids = new Set(reg.subdomains.map((s) => s.id));
    for (const id of Object.keys(SUBDOMAIN_DEMOS)) {
      expect(ids.has(id), id).toBe(true);
    }
  });

  it("link to the published Factory to Field page", () => {
    for (const demo of Object.values(SUBDOMAIN_DEMOS)) {
      expect(demo.url).toBe("https://kvinayakpai.github.io/domain-explorer/factory-to-field/");
      expect(demo.blurb.length).toBeGreaterThan(40);
    }
  });
});
