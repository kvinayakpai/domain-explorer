// Vitest suite for @domain-explorer/init.
// 10 tests across validate, filter, rebrand, and a smoke end-to-end run.

import { describe, it, expect, beforeAll, afterAll } from "vitest";
import path from "node:path";
import os from "node:os";
import fs from "node:fs";
import fse from "fs-extra";
import { fileURLToPath } from "node:url";

import { validate, customerLabelFor } from "../src/steps/01-validate.js";
import { filterSubdomains } from "../src/steps/03-filter-subdomains.js";
import { rebrand } from "../src/steps/04-rebrand.js";
import { init } from "../src/index.js";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// The source repo is the workspace root: 3 levels up from this test file.
const SOURCE_REPO = path.resolve(__dirname, "..", "..", "..");

function tmpdir(prefix) {
  return fs.mkdtempSync(path.join(os.tmpdir(), `de-cli-${prefix}-`));
}

/** Build a tiny synthetic source tree we can run filter+rebrand against
 *  without copying the real (huge) repo every test. */
function buildFakeRepo(root) {
  fse.ensureDirSync(path.join(root, "data", "taxonomy"));
  fse.ensureDirSync(path.join(root, "data", "kpis"));
  fse.ensureDirSync(path.join(root, "apps", "explorer-web", "app"));
  fse.ensureDirSync(path.join(root, "apps", "explorer-web", "public"));
  fs.writeFileSync(
    path.join(root, "package.json"),
    JSON.stringify({ name: "domain-explorer", version: "0.1.0" }, null, 2),
  );
  fs.writeFileSync(
    path.join(root, "apps", "explorer-web", "package.json"),
    JSON.stringify({ name: "explorer-web", version: "0.1.0" }, null, 2),
  );
  fs.writeFileSync(path.join(root, "README.md"), "# Domain Explorer\n\nLead.\n");
  fs.writeFileSync(
    path.join(root, ".env.example"),
    "# Domain Explorer environment variables.\nFOO=bar\n",
  );
  fs.writeFileSync(
    path.join(root, "apps", "explorer-web", "app", "page.tsx"),
    `<Badge>Deep Domain Explorer</Badge>\n`,
  );
  fs.writeFileSync(
    path.join(root, "apps", "explorer-web", "app", "layout.tsx"),
    `title: "Domain Explorer"\n` +
      `description: "Metadata-driven explorer for industry verticals, subdomains, KPIs, and integration patterns."\n` +
      `Domain Explorer · MIT · 16 verticals\n`,
  );
  // Three taxonomy files: 2 BFSI, 1 Insurance.
  fs.writeFileSync(
    path.join(root, "data", "taxonomy", "payments.yaml"),
    "id: payments\nname: Payments\nvertical: BFSI\n",
  );
  fs.writeFileSync(
    path.join(root, "data", "taxonomy", "cards.yaml"),
    "id: cards\nname: Cards\nvertical: BFSI\n",
  );
  fs.writeFileSync(
    path.join(root, "data", "taxonomy", "underwriting.yaml"),
    "id: underwriting\nname: Underwriting\nvertical: Insurance\n",
  );
  // Tiny KPI master with one BFSI and one Insurance row.
  fs.writeFileSync(
    path.join(root, "data", "kpis", "kpis.yaml"),
    [
      "kpis:",
      "  - { id: pay.kpi.stp, name: STP Rate, vertical: BFSI }",
      "  - { id: pcc.kpi.cycle, name: Cycle Time, vertical: Insurance }",
      "",
    ].join("\n"),
  );
}

describe("validate()", () => {
  it("accepts a valid configuration", async () => {
    const r = await validate({
      customer: "acme-bank",
      vertical: "bfsi",
      cloud: "snowflake",
      persona: "cdo",
      sourceRepo: SOURCE_REPO,
      outputDir: tmpdir("validate-good"),
    });
    expect(r.ok).toBe(true);
    expect(r.context.customer).toBe("acme-bank");
    expect(r.context.customerLabel).toBe("Acme Bank");
    expect(r.context.vertical.canonical).toBe("BFSI");
    expect(r.context.cloud.slug).toBe("snowflake");
    expect(r.context.persona.id).toBe("cdo");
  });

  it("rejects an invalid customer slug", async () => {
    const r = await validate({
      customer: "ab", // too short
      vertical: "bfsi",
      sourceRepo: SOURCE_REPO,
    });
    expect(r.ok).toBe(false);
    expect(r.error).toMatch(/Invalid customer name|length/);
  });

  it("rejects an unknown vertical", async () => {
    const r = await validate({
      customer: "acme-bank",
      vertical: "supercalifragilistic",
      sourceRepo: SOURCE_REPO,
    });
    expect(r.ok).toBe(false);
    expect(r.error).toMatch(/Unknown vertical/);
  });

  it("requires --vertical", async () => {
    const r = await validate({
      customer: "acme-bank",
      sourceRepo: SOURCE_REPO,
    });
    expect(r.ok).toBe(false);
    expect(r.error).toMatch(/Missing --vertical/);
  });

  it("derives a label from a hyphenated slug", () => {
    expect(customerLabelFor("acme-bank")).toBe("Acme Bank");
    expect(customerLabelFor("first-republic-co")).toBe("First Republic Co");
  });
});

describe("filterSubdomains()", () => {
  it("keeps only BFSI taxonomy files", async () => {
    const root = tmpdir("filter-bfsi");
    buildFakeRepo(root);
    const ctx = {
      outputDir: root,
      vertical: { canonical: "BFSI", label: "BFSI", slug: "bfsi" },
      dryRun: false,
    };
    const r = await filterSubdomains(ctx);
    expect(r.kept).toBe(2);
    expect(r.dropped).toBe(1);
    const remaining = fs.readdirSync(path.join(root, "data", "taxonomy"));
    expect(remaining.sort()).toEqual(["cards.yaml", "payments.yaml"]);
  });

  it("filters the cross-vertical KPI master", async () => {
    const root = tmpdir("filter-kpi");
    buildFakeRepo(root);
    const ctx = {
      outputDir: root,
      vertical: { canonical: "BFSI", label: "BFSI", slug: "bfsi" },
      dryRun: false,
    };
    const r = await filterSubdomains(ctx);
    expect(r.kpisKept).toBe(1);
    expect(r.kpisDropped).toBe(1);
    const text = fs.readFileSync(path.join(root, "data", "kpis", "kpis.yaml"), "utf8");
    expect(text).toMatch(/STP Rate/);
    expect(text).not.toMatch(/Cycle Time/);
  });
});

describe("rebrand()", () => {
  it("rewrites root + app package.json names", async () => {
    const root = tmpdir("rebrand-pkg");
    buildFakeRepo(root);
    await rebrand({
      outputDir: root,
      customer: "acme-bank",
      customerLabel: "Acme Bank",
      vertical: { canonical: "BFSI" },
      cloud: { slug: "snowflake" },
      persona: { id: "cdo", label: "Chief Data Officer" },
      tagline: "",
      logo: null,
      dryRun: false,
    });
    const root2 = JSON.parse(fs.readFileSync(path.join(root, "package.json"), "utf8"));
    expect(root2.name).toBe("acme-bank-domain-explorer");
    const app = JSON.parse(
      fs.readFileSync(path.join(root, "apps", "explorer-web", "package.json"), "utf8"),
    );
    expect(app.name).toBe("acme-bank-explorer-web");
  });

  it("updates the README, hero badge, layout title and footer", async () => {
    const root = tmpdir("rebrand-strings");
    buildFakeRepo(root);
    await rebrand({
      outputDir: root,
      customer: "acme-bank",
      customerLabel: "Acme Bank",
      vertical: { canonical: "BFSI" },
      cloud: { slug: "duckdb" },
      persona: null,
      tagline: "Banking, evolved.",
      logo: null,
      dryRun: false,
    });
    expect(fs.readFileSync(path.join(root, "README.md"), "utf8")).toMatch(
      /Acme Bank — Domain Explorer/,
    );
    expect(
      fs.readFileSync(path.join(root, "apps", "explorer-web", "app", "page.tsx"), "utf8"),
    ).toMatch(/Acme Bank — Domain Explorer/);
    const layout = fs.readFileSync(
      path.join(root, "apps", "explorer-web", "app", "layout.tsx"),
      "utf8",
    );
    expect(layout).toMatch(/Acme Bank — Domain Explorer/);
    expect(layout).toMatch(/Acme Bank · Domain Explorer · MIT/);
  });

  it("writes a customer.json metadata file", async () => {
    const root = tmpdir("rebrand-meta");
    buildFakeRepo(root);
    await rebrand({
      outputDir: root,
      customer: "globex",
      customerLabel: "Globex",
      vertical: { canonical: "BFSI" },
      cloud: { slug: "snowflake" },
      persona: { id: "cdo", label: "Chief Data Officer" },
      tagline: null,
      logo: null,
      dryRun: false,
    });
    const meta = JSON.parse(fs.readFileSync(path.join(root, "customer.json"), "utf8"));
    expect(meta.customer).toBe("globex");
    expect(meta.vertical).toBe("BFSI");
    expect(meta.cloud).toBe("snowflake");
    expect(meta.persona).toBe("cdo");
  });
});

describe("init() smoke test (end-to-end)", () => {
  let tmp;
  let outDir;
  beforeAll(() => {
    tmp = tmpdir("smoke-source");
    buildFakeRepo(tmp);
    outDir = path.join(tmpdir("smoke-output"), "out");
  });
  afterAll(() => {
    try {
      fse.removeSync(tmp);
    } catch {}
  });

  it("produces a branded clone with a customer.json marker", async () => {
    const r = await init({
      customer: "acme-bank",
      vertical: "bfsi",
      cloud: "snowflake",
      persona: "cdo",
      sourceRepo: tmp,
      outputDir: outDir,
      git: false, // skip git in test
      quiet: true,
    });
    expect(r.exitCode).toBe(0);
    // package.json was rewritten
    const pkg = JSON.parse(fs.readFileSync(path.join(outDir, "package.json"), "utf8"));
    expect(pkg.name).toBe("acme-bank-domain-explorer");
    // Snowflake profile was generated
    expect(
      fs.existsSync(path.join(outDir, "modeling", "dbt", "profiles-snowflake.yml")),
    ).toBe(true);
    // customer.json marker
    const meta = JSON.parse(fs.readFileSync(path.join(outDir, "customer.json"), "utf8"));
    expect(meta.customer).toBe("acme-bank");
    // Persona defaults file
    expect(
      fs.existsSync(
        path.join(outDir, "apps", "explorer-web", "lib", "customer-defaults.json"),
      ),
    ).toBe(true);
    // Filtered to BFSI only
    const taxos = fs.readdirSync(path.join(outDir, "data", "taxonomy"));
    expect(taxos.sort()).toEqual(["cards.yaml", "payments.yaml"]);
  });
});
