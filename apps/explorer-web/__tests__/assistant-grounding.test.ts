/**
 * Answer-quality benchmark suite for the Domain Explorer assistant.
 *
 * Two layers:
 *   1. Grounding-only tests (always run): drive `buildGrounding` directly and
 *      assert the registry traversal pulls the expected source records and
 *      KPIs for a given persona/question. No LLM involved.
 *   2. LLM smoke tests (gated on `ANTHROPIC_API_KEY` env): hit the chat
 *      route end-to-end and assert that key terms from the grounded context
 *      appear in the streamed answer. Skipped in CI by default.
 *
 * Run via `pnpm --filter explorer-web vitest run __tests__/assistant-grounding.test.ts`
 * or the root convenience script `pnpm test:assistant`.
 */
import { describe, it, expect } from "vitest";
import { resolve } from "node:path";
import { existsSync } from "node:fs";
import { buildGrounding } from "@/lib/grounding";
import {
  SUGGESTIONS,
  SUGGESTION_COUNT,
  suggestionsForVertical,
  tourSuggestions,
} from "@/lib/assistant-suggestions";
import {
  ALL_VARIANTS,
  GENERIC_VARIANT,
  systemPromptFor,
  variantFor,
} from "@/lib/assistant-prompts";

// `buildGrounding` reads from `data/taxonomy/`. Skip the heavy assertions if
// the data root isn't present (lets the test file load in stripped CI envs).
const REPO_DATA = resolve(__dirname, "..", "..", "..", "data");
const HAS_DATA = existsSync(resolve(REPO_DATA, "taxonomy"));

interface GroundingCase {
  /** Stable label for the case — used in test titles. */
  name: string;
  /** Question fed to the assistant. */
  question: string;
  /** Persona key (subdomainId::personaName) — optional. */
  personaKey?: string;
  /** Subdomain ids that should appear in `matchedSubdomains` (subset). */
  expectedSubdomains: string[];
  /** KPI ids that must appear in `kpis` (subset). */
  expectedKpiIds: string[];
  /** Vendor names that must appear in `sourceSystems` (subset, case-insensitive). */
  expectedVendors?: string[];
  /** Substrings that must appear in `recordsUsed`. */
  expectedRecordHints: string[];
  /** Vertical the question is anchored in (used for system-prompt assertion). */
  vertical?: string;
}

const CASES: GroundingCase[] = [
  {
    name: "BFSI / Payments — Head of Payments KPIs",
    question: "What KPIs does the Head of Payments care about?",
    personaKey: "payments::Head of Payments",
    expectedSubdomains: ["payments"],
    expectedKpiIds: ["pay.kpi.stp_rate", "pay.kpi.settlement_latency", "pay.kpi.chargeback_ratio"],
    expectedRecordHints: ["payments.yaml"],
    vertical: "BFSI",
  },
  {
    name: "BFSI / Payments — STP rate lineage",
    question: "Walk me from STP rate down to the source-system field",
    personaKey: "payments::Head of Payments",
    expectedSubdomains: ["payments"],
    expectedKpiIds: ["pay.kpi.stp_rate"],
    expectedRecordHints: ["payments.yaml"],
    vertical: "BFSI",
  },
  {
    name: "BFSI / Fraud — detection vs false positives",
    question: "How does our fraud platform balance detection vs false positives?",
    personaKey: "fraud::Head of Fraud",
    expectedSubdomains: ["fraud"],
    expectedKpiIds: ["fraud.kpi.detection_rate", "fraud.kpi.false_positive_rate"],
    expectedRecordHints: ["fraud.yaml"],
    vertical: "BFSI",
  },
  {
    name: "Insurance / Claims — leakage detection",
    question: "How would I detect claim leakage in our data?",
    personaKey: "claims_subrogation::Head of Claims",
    expectedSubdomains: ["claims_subrogation"],
    expectedKpiIds: ["clm.kpi.cycle_time", "clm.kpi.subrogation_recovery"],
    expectedRecordHints: ["claims_subrogation.yaml"],
    vertical: "Insurance",
  },
  {
    name: "Retail / Store ops — shrink",
    question: "Which source systems feed shrink for store ops?",
    personaKey: "store_ops::Loss Prevention Lead",
    expectedSubdomains: ["store_ops"],
    expectedKpiIds: ["ops.kpi.shrink"],
    expectedRecordHints: ["store_ops.yaml"],
    vertical: "Retail",
  },
  {
    name: "Retail / Ecommerce — VP Digital dashboard",
    question: "What KPIs should a VP Digital have on their dashboard?",
    personaKey: "ecommerce::VP Digital",
    expectedSubdomains: ["ecommerce"],
    expectedKpiIds: ["ecom.kpi.conversion_rate", "ecom.kpi.aov"],
    expectedRecordHints: ["ecommerce.yaml"],
    vertical: "Retail",
  },
  {
    name: "CPG / Trade Promotion — promo ROI",
    question: "How is promo ROI computed for trade promotion?",
    personaKey: "trade_promotion::Trade Marketing Director",
    expectedSubdomains: ["trade_promotion"],
    expectedKpiIds: ["tpm.kpi.promo_roi", "tpm.kpi.lift_pct"],
    expectedRecordHints: ["trade_promotion.yaml"],
    vertical: "CPG",
  },
  {
    name: "TTH / Hotel distribution — channel manager KPIs",
    question: "What KPIs does a Channel Manager track for hotel distribution?",
    personaKey: "hotel_distribution::Channel Manager",
    expectedSubdomains: ["hotel_distribution"],
    expectedKpiIds: ["hdist.kpi.direct_share", "hdist.kpi.commission_cost"],
    expectedRecordHints: ["hotel_distribution.yaml"],
    vertical: "TTH",
  },
  {
    name: "TTH / Airline RM — RASK vs yield",
    question: "How do RASK and yield differ in airline revenue management?",
    personaKey: "airline_revenue_management::VP Revenue Management",
    expectedSubdomains: ["airline_revenue_management"],
    expectedKpiIds: ["arm.kpi.rask", "arm.kpi.yield", "arm.kpi.load_factor"],
    expectedRecordHints: ["airline_revenue_management.yaml"],
    vertical: "TTH",
  },
  {
    name: "Manufacturing / Shop floor IoT — OEE composition",
    question: "Which data sources do I need to compute OEE end-to-end?",
    personaKey: "shop_floor_iot::IIoT Architect",
    expectedSubdomains: ["shop_floor_iot"],
    expectedKpiIds: ["iiot.kpi.oee", "iiot.kpi.mttr"],
    expectedRecordHints: ["shop_floor_iot.yaml"],
    vertical: "Manufacturing",
  },
  {
    name: "Manufacturing / Warranty — claim spike",
    question: "How do I trace a warranty spike back to the production batch?",
    personaKey: "warranty::Quality Engineer",
    expectedSubdomains: ["warranty"],
    expectedKpiIds: ["war.kpi.claim_rate", "war.kpi.cost_per_unit_sold"],
    expectedRecordHints: ["warranty.yaml"],
    vertical: "Manufacturing",
  },
  {
    name: "LifeSciences / Pharma SC — cold chain",
    question: "How are cold chain excursions monitored for pharma supply chain?",
    personaKey: "pharma_supply_chain::Cold Chain Manager",
    expectedSubdomains: ["pharma_supply_chain"],
    expectedKpiIds: ["psc.kpi.cold_chain_excursions"],
    expectedRecordHints: ["pharma_supply_chain.yaml"],
    vertical: "LifeSciences",
  },
  {
    name: "Healthcare / Value-based care — readmits",
    question: "What's the read-mission KPI everyone watches in value-based care?",
    personaKey: "value_based_care::VP VBC",
    expectedSubdomains: ["value_based_care"],
    expectedKpiIds: ["vbc.kpi.readmit_30", "vbc.kpi.acute_admits_per_k"],
    expectedRecordHints: ["value_based_care.yaml"],
    vertical: "Healthcare",
  },
  {
    name: "Healthcare / Revenue cycle — denial diagnosis",
    question: "How do I diagnose a denial-rate spike?",
    personaKey: "revenue_cycle::Denials Manager",
    expectedSubdomains: ["revenue_cycle"],
    expectedKpiIds: ["rcm.kpi.denial_rate", "rcm.kpi.first_pass_paid"],
    expectedRecordHints: ["revenue_cycle.yaml"],
    vertical: "Healthcare",
  },
  {
    name: "Telecom / Churn management — dashboard",
    question: "Which KPIs sit on a churn manager's dashboard?",
    personaKey: "churn_management::Head of Retention",
    expectedSubdomains: ["churn_management"],
    expectedKpiIds: ["chrn.kpi.monthly_churn", "chrn.kpi.win_back"],
    expectedRecordHints: ["churn_management.yaml"],
    vertical: "Telecom",
  },
  {
    name: "Telecom / Subscriber billing — leakage",
    question: "How is revenue leakage detected in subscriber billing?",
    personaKey: "subscriber_billing::Revenue Assurance Lead",
    expectedSubdomains: ["subscriber_billing"],
    expectedKpiIds: ["bill.kpi.rev_leakage", "bill.kpi.bill_accuracy"],
    expectedRecordHints: ["subscriber_billing.yaml"],
    vertical: "Telecom",
  },
  {
    name: "Energy / Renewable generation — capacity factor",
    question: "How do I compute capacity factor for a wind site?",
    personaKey: "renewable_generation::Forecasting Lead",
    expectedSubdomains: ["renewable_generation"],
    expectedKpiIds: ["rg.kpi.capacity_factor"],
    expectedRecordHints: ["renewable_generation.yaml"],
    vertical: "Energy",
  },
  {
    name: "Utilities / Outage management — SAIDI/SAIFI",
    question: "How do SAIDI and SAIFI relate, and what feeds them?",
    personaKey: "outage_management::Outage Manager",
    expectedSubdomains: ["outage_management"],
    expectedKpiIds: ["out.kpi.saidi", "out.kpi.saifi"],
    expectedRecordHints: ["outage_management.yaml"],
    vertical: "Utilities",
  },
  {
    name: "PublicSector / Eligibility — KPIs",
    question: "Which KPIs matter for a benefits eligibility program?",
    personaKey: "social_services_case_management::Eligibility Worker Lead",
    expectedSubdomains: ["social_services_case_management"],
    expectedKpiIds: ["ssc.kpi.eligibility_cycle", "ssc.kpi.timely_recerts"],
    expectedRecordHints: ["social_services_case_management.yaml"],
    vertical: "PublicSector",
  },
  {
    name: "ProfessionalServices / Time & Billing — utilisation",
    question: "How do utilisation and realisation differ for billable teams?",
    personaKey: "time_and_billing::Engagement Manager",
    expectedSubdomains: ["time_and_billing"],
    expectedKpiIds: ["tb.kpi.realization_rate", "tb.kpi.lockup"],
    expectedRecordHints: ["time_and_billing.yaml"],
    vertical: "ProfessionalServices",
  },
];

describe.skipIf(!HAS_DATA)("assistant grounding — registry traversal", () => {
  for (const c of CASES) {
    it(c.name, () => {
      const g = buildGrounding({ question: c.question, personaKey: c.personaKey });

      // Subdomain match — every expected id should be in matchedSubdomains.
      const matchedIds = g.matchedSubdomains.map((s) => s.id);
      for (const sd of c.expectedSubdomains) {
        expect(matchedIds, `subdomain ${sd} not matched for "${c.name}"`).toContain(sd);
      }

      // KPI presence — every expected KPI id should be in the bundle.
      const kpiIds = g.kpis.map((k) => k.id);
      for (const id of c.expectedKpiIds) {
        expect(kpiIds, `KPI ${id} not grounded for "${c.name}"`).toContain(id);
      }

      // Record hints — provenance trail should mention the relevant YAML file.
      for (const hint of c.expectedRecordHints) {
        const hit = g.recordsUsed.some((r) => r.includes(hint));
        expect(hit, `recordsUsed missing "${hint}" for "${c.name}". Got: ${g.recordsUsed.join(", ")}`).toBe(true);
      }

      // Vendor presence (optional).
      if (c.expectedVendors?.length) {
        const vendors = g.sourceSystems.map((s) => s.vendor.toLowerCase());
        for (const v of c.expectedVendors) {
          expect(vendors, `vendor ${v} missing for "${c.name}"`).toContain(v.toLowerCase());
        }
      }
    });
  }

  it("benchmark suite covers >= 15 cases", () => {
    expect(CASES.length).toBeGreaterThanOrEqual(15);
  });

  it("decisions chain is populated when a persona is selected", () => {
    const g = buildGrounding({
      question: "What decisions does the Head of Payments own?",
      personaKey: "payments::Head of Payments",
    });
    expect(g.decisionsChain).not.toBeNull();
    expect(g.decisionsChain!.decisions.length).toBeGreaterThan(0);
  });

  it("falls back to keyword-only matching when no persona is selected", () => {
    const g = buildGrounding({ question: "STP rate and settlement latency for payments" });
    expect(g.persona).toBeUndefined();
    const ids = g.matchedSubdomains.map((s) => s.id);
    expect(ids).toContain("payments");
  });
});

describe("assistant-prompts variant resolution", () => {
  it("includes a variant for every vertical slug used by cases", () => {
    for (const c of CASES) {
      if (!c.vertical) continue;
      const v = variantFor(c.vertical);
      expect(v.vertical).not.toBe("Generic");
    }
  });

  it("falls back to the generic variant when vertical is unknown", () => {
    expect(variantFor(undefined)).toBe(GENERIC_VARIANT);
    expect(variantFor("Bogus")).toBe(GENERIC_VARIANT);
  });

  it("renders a non-trivial system prompt for every variant", () => {
    for (const v of ALL_VARIANTS) {
      const text = systemPromptFor(v.vertical === "Generic" ? undefined : v.vertical);
      expect(text.length).toBeGreaterThan(200);
      expect(text).toContain("GROUNDING CONTEXT" /* base hard rules reference */);
    }
  });

  it("the BFSI variant carries STP rate vocabulary", () => {
    const text = systemPromptFor("BFSI");
    expect(text.toLowerCase()).toContain("stp rate");
  });

  it("the Healthcare variant references FHIR", () => {
    const text = systemPromptFor("Healthcare");
    expect(text).toContain("FHIR");
  });

  it("renders >= 16 vertical variants total (incl. RCG)", () => {
    // 16 verticals + Generic = 17 total
    expect(ALL_VARIANTS.length).toBeGreaterThanOrEqual(16);
  });
});

describe("assistant-suggestions library shape", () => {
  it("has 30+ canonical questions", () => {
    expect(SUGGESTION_COUNT).toBeGreaterThanOrEqual(30);
  });

  it("covers at least 12 verticals", () => {
    const verticals = new Set(SUGGESTIONS.map((s) => s.vertical));
    expect(verticals.size).toBeGreaterThanOrEqual(12);
  });

  it("each suggestion carries a non-empty expected_answer_summary", () => {
    for (const s of SUGGESTIONS) {
      expect(s.expectedAnswerSummary.length, `${s.id} missing summary`).toBeGreaterThan(10);
    }
  });

  it("filters by vertical and pads sparse verticals to >= 4 chips", () => {
    for (const v of ["BFSI", "Healthcare", "Energy", "PublicSector", "ProfessionalServices"]) {
      const out = suggestionsForVertical(v, 6);
      expect(out.length, `vertical ${v} produced fewer than 4 chips`).toBeGreaterThanOrEqual(4);
    }
  });

  it("returns the curated tour when no vertical is supplied", () => {
    const out = suggestionsForVertical(undefined, 6);
    expect(out).toBe(tourSuggestions);
  });
});

// ----- LLM smoke tests -----------------------------------------------------
// Gated on ANTHROPIC_API_KEY so they don't run in CI by default. They exercise
// the route handler end-to-end (vertical-aware system prompt + grounded
// context) and assert that key terms from the grounded context appear in the
// streamed answer.
const HAS_LLM = Boolean(process.env.ANTHROPIC_API_KEY);

interface LlmSmokeCase {
  name: string;
  question: string;
  personaKey: string;
  /** Substrings (case-insensitive) that should appear in the streamed answer. */
  expectedKeywords: string[];
}

const LLM_CASES: LlmSmokeCase[] = [
  {
    name: "BFSI / Payments — STP rate",
    question: "What KPIs does the Head of Payments care about?",
    personaKey: "payments::Head of Payments",
    expectedKeywords: ["STP", "settlement"],
  },
  {
    name: "Insurance / Claims — leakage",
    question: "How would I detect claim leakage in our data?",
    personaKey: "claims_subrogation::Head of Claims",
    expectedKeywords: ["claim", "leakage"],
  },
  {
    name: "Manufacturing / OEE composition",
    question: "Which data sources do I need to compute OEE end-to-end?",
    personaKey: "shop_floor_iot::IIoT Architect",
    expectedKeywords: ["OEE", "MES"],
  },
  {
    name: "Healthcare / FHIR resources",
    question: "Which FHIR resources feed our care quality KPIs?",
    personaKey: "value_based_care::Pop Health Director",
    expectedKeywords: ["FHIR"],
  },
];

async function callChatRoute(question: string, personaKey: string): Promise<string> {
  // Lazy-import the route module so this file still parses when next isn't
  // installed in the test sandbox.
  const mod = (await import("../app/api/chat/route")) as {
    POST(req: Request): Promise<Response>;
  };
  const req = new Request("http://localhost/api/chat", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ message: question, personaKey, history: [] }),
  });
  const res = await mod.POST(req as never);
  // Read the SSE-ish stream into a flat string of delta payloads.
  const reader = res.body?.getReader();
  if (!reader) return "";
  const decoder = new TextDecoder();
  let raw = "";
  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    raw += decoder.decode(value, { stream: true });
  }
  // Parse out every `data: { "text": ... }` event payload.
  const out: string[] = [];
  for (const block of raw.split("\n\n")) {
    if (!block.includes("event: delta")) continue;
    const m = block.match(/data: (\{[\s\S]*\})/);
    if (!m) continue;
    try {
      const parsed = JSON.parse(m[1]) as { text?: string };
      if (parsed.text) out.push(parsed.text);
    } catch {
      /* ignore */
    }
  }
  return out.join("");
}

describe.skipIf(!HAS_LLM || !HAS_DATA)("assistant LLM smoke tests (live mode)", () => {
  for (const c of LLM_CASES) {
    it(c.name, async () => {
      const answer = await callChatRoute(c.question, c.personaKey);
      expect(answer.length, `empty answer for "${c.name}"`).toBeGreaterThan(20);
      const lower = answer.toLowerCase();
      for (const kw of c.expectedKeywords) {
        expect(lower, `answer for "${c.name}" missing keyword "${kw}"`).toContain(kw.toLowerCase());
      }
    }, 30_000);
  }
});
