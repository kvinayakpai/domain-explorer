/**
 * Pre-canned suggestion questions for the Domain Explorer assistant.
 *
 * The chat UI in `components/assistant-chat.tsx` filters this list by the
 * currently-selected persona's vertical and renders the top 4-6 chips. If
 * no persona is selected the UI falls back to {@link tourSuggestions} —
 * a curated set spanning multiple verticals so the user gets a feel for
 * what the assistant can answer.
 *
 * Each entry carries:
 *   - `text`                     the question rendered on the chip
 *   - `vertical`                 vertical slug (matches registry verticals)
 *   - `personaKey?`              optional persona key (subdomainId::personaName)
 *                                 so clicking the chip can also re-select
 *                                 the persona that "owns" the question
 *   - `expectedAnswerSummary`    one-sentence ground truth used by the
 *                                 grounding test suite to assert keywords
 *
 * Persona keys mirror the format produced by `listPersonaOptions()` —
 * `<subdomainId>::<persona.name>`. They're optional: when a chip is clicked
 * with no persona key, only the question text is seeded.
 */

export type VerticalSlug =
  | "BFSI"
  | "Insurance"
  | "Retail"
  | "RCG"
  | "CPG"
  | "TTH"
  | "Manufacturing"
  | "LifeSciences"
  | "Healthcare"
  | "Telecom"
  | "Media"
  | "Energy"
  | "Utilities"
  | "PublicSector"
  | "HiTech"
  | "ProfessionalServices"
  | "CrossCutting";

export interface AssistantSuggestion {
  /** Stable id for the suggestion — useful for tests and analytics. */
  id: string;
  /** The question text shown on the chip and seeded into the chat. */
  text: string;
  /** Vertical tag used for filtering (CrossCutting = applicable anywhere). */
  vertical: VerticalSlug;
  /** Optional persona key (subdomainId::name) the chip points at. */
  personaKey?: string;
  /** One-sentence summary of the expected grounded answer (used by tests). */
  expectedAnswerSummary: string;
}

/**
 * Canonical suggestion library — keep additions vertical-balanced so the
 * /assistant page has a meaningful 4-6 chip set for any persona pick.
 */
export const SUGGESTIONS: AssistantSuggestion[] = [
  // -------- BFSI ---------------------------------------------------------
  {
    id: "bfsi.payments.head.kpis",
    text: "What KPIs does the Head of Payments care about?",
    vertical: "BFSI",
    personaKey: "payments::Head of Payments",
    expectedAnswerSummary:
      "STP rate, settlement latency, chargeback ratio, and auth failure rate are the core four for the Head of Payments.",
  },
  {
    id: "bfsi.payments.lineage",
    text: "Walk me from STP rate down to the source-system field.",
    vertical: "BFSI",
    personaKey: "payments::Head of Payments",
    expectedAnswerSummary:
      "STP rate rolls up from per-transaction is_straight_through flags built from acquirer events and the clearing file.",
  },
  {
    id: "bfsi.fraud.detection",
    text: "How does our fraud platform balance detection vs false positives?",
    vertical: "BFSI",
    personaKey: "fraud::Head of Fraud",
    expectedAnswerSummary:
      "Detection rate vs false positive rate trade off in the fraud subdomain, sourced from the alert and disposition streams.",
  },
  {
    id: "bfsi.fraud.time_to_disposition",
    text: "Why does time-to-disposition matter for a fraud ops team?",
    vertical: "BFSI",
    personaKey: "fraud::Fraud Ops Manager",
    expectedAnswerSummary:
      "Time-to-disposition compresses queue exposure and is the alert_ts to disposition_ts delta on the fraud alert fact.",
  },

  // -------- Insurance ---------------------------------------------------
  {
    id: "ins.claims.leakage",
    text: "How would I detect claim leakage in our data?",
    vertical: "Insurance",
    personaKey: "claims_subrogation::Head of Claims",
    expectedAnswerSummary:
      "Claim leakage compares actual paid versus expected paid on closed claims, sourced from the claims admin system.",
  },
  {
    id: "ins.claims.cycle",
    text: "What pulls claim cycle time longer than target?",
    vertical: "Insurance",
    personaKey: "claims_subrogation::Head of Claims",
    expectedAnswerSummary:
      "Claim cycle time = avg(closed_ts - opened_ts); reopen rate, LAE ratio, and subrogation feed the same fact.",
  },
  {
    id: "ins.subrogation.recovery",
    text: "How is subrogation recovery rate built?",
    vertical: "Insurance",
    personaKey: "claims_subrogation::Subrogation Lead",
    expectedAnswerSummary:
      "Subrogation recovery rate = recovered / recoverable, joining claims to recovery ledger entries.",
  },

  // -------- Retail ------------------------------------------------------
  {
    id: "retail.markdown.spike",
    text: "Why is my markdown rate spiking in store cluster 3?",
    vertical: "Retail",
    expectedAnswerSummary:
      "Markdown rate = markdown_units / total_sold_units; investigate cluster 3 via the merchandising mart and store_attributes dim.",
  },
  {
    id: "retail.shrink",
    text: "Which source systems feed shrink for store ops?",
    vertical: "Retail",
    personaKey: "store_ops::Loss Prevention Lead",
    expectedAnswerSummary:
      "Shrink = shrink_dollars / net_sales, sourced from POS, inventory snapshots, and audit fact in store_ops.",
  },
  {
    id: "retail.ecom.conversion",
    text: "What KPIs should a VP Digital have on their dashboard?",
    vertical: "Retail",
    personaKey: "ecommerce::VP Digital",
    expectedAnswerSummary:
      "Conversion rate, AOV, cart abandonment, and CAC from the ecommerce subdomain.",
  },

  // -------- CPG ---------------------------------------------------------
  {
    id: "cpg.tpm.roi",
    text: "How is promo ROI computed for trade promotion?",
    vertical: "CPG",
    personaKey: "trade_promotion::Trade Marketing Director",
    expectedAnswerSummary:
      "Promo ROI = incremental_profit / promo_spend; lift and deduction aging anchor the trade_promotion mart.",
  },
  {
    id: "cpg.deductions",
    text: "Why is unauthorized deduction percentage rising?",
    vertical: "CPG",
    personaKey: "trade_promotion::Deduction Resolution Lead",
    expectedAnswerSummary:
      "Unauthorized deduction % is unauthorized / total deductions on the trade_promotion deduction fact.",
  },

  // -------- TTH (Travel/Hospitality) ------------------------------------
  {
    id: "tth.revpar.lineage",
    text: "Walk me from RevPAR back to the operational dataset.",
    vertical: "TTH",
    expectedAnswerSummary:
      "RevPAR = ADR x occupancy; ADR sources from PMS folio, occupancy from PMS over rooms_available.",
  },
  {
    id: "tth.airline.yield",
    text: "How do RASK and yield differ in airline revenue management?",
    vertical: "TTH",
    personaKey: "airline_revenue_management::VP Revenue Management",
    expectedAnswerSummary:
      "RASK = revenue / ASK while yield = passenger_revenue / RPK; load factor links the two.",
  },
  {
    id: "tth.distribution.parity",
    text: "What KPIs does a Channel Manager track for hotel distribution?",
    vertical: "TTH",
    personaKey: "hotel_distribution::Channel Manager",
    expectedAnswerSummary:
      "Direct booking share, channel commission %, rate parity breaks, and avg booking lead time anchor hotel distribution.",
  },

  // -------- Manufacturing ----------------------------------------------
  {
    id: "mfg.oee.sources",
    text: "Which data sources do I need to compute OEE end-to-end?",
    vertical: "Manufacturing",
    personaKey: "shop_floor_iot::IIoT Architect",
    expectedAnswerSummary:
      "OEE = Availability x Performance x Quality, sourced from MES, historian, and QMS in shop_floor_iot.",
  },
  {
    id: "mfg.warranty.spike",
    text: "How do I trace a warranty spike back to the production batch?",
    vertical: "Manufacturing",
    personaKey: "warranty::Quality Engineer",
    expectedAnswerSummary:
      "Join warranty claims fact to MES genealogy (serial->lot->batch); supplier_quality attaches PPAP to BOM components.",
  },
  {
    id: "mfg.pdm.precision",
    text: "How do precision and recall trade off for predictive maintenance?",
    vertical: "Manufacturing",
    personaKey: "predictive_maintenance::Data Science Lead",
    expectedAnswerSummary:
      "Precision = tp/(tp+fp), recall = tp/(tp+fn); the predictive_maintenance subdomain tracks both alongside MTBF and unplanned downtime.",
  },

  // -------- LifeSciences ------------------------------------------------
  {
    id: "ls.adverse.event.path",
    text: "What's the data path from an adverse event to the regulatory submission?",
    vertical: "LifeSciences",
    personaKey: "pharma_supply_chain::Serialization Lead",
    expectedAnswerSummary:
      "AE intake -> safety database (MedDRA-coded) -> E2B(R3) export to AERS/EVDAS, with signal detection on the case fact.",
  },
  {
    id: "ls.cold_chain",
    text: "How are cold chain excursions monitored for pharma supply chain?",
    vertical: "LifeSciences",
    personaKey: "pharma_supply_chain::Cold Chain Manager",
    expectedAnswerSummary:
      "Cold chain excursions = excursions / shipments; sourced from in-transit IoT loggers joined to shipment manifests.",
  },

  // -------- Healthcare --------------------------------------------------
  {
    id: "hc.fhir.kpis",
    text: "Which FHIR resources feed our care quality KPIs?",
    vertical: "Healthcare",
    personaKey: "value_based_care::Pop Health Director",
    expectedAnswerSummary:
      "Patient, Encounter, Observation, Condition, MedicationRequest are the core FHIR resources behind the value_based_care HEDIS gap KPIs.",
  },
  {
    id: "hc.denial.spike",
    text: "How do I diagnose a denial-rate spike?",
    vertical: "Healthcare",
    personaKey: "revenue_cycle::Denials Manager",
    expectedAnswerSummary:
      "Denial rate is from 835 ERA segments joined to 837 submissions in revenue_cycle; slice by payer and reason code.",
  },
  {
    id: "hc.vbc.readmits",
    text: "What's the read-mission KPI everyone watches in value-based care?",
    vertical: "Healthcare",
    personaKey: "value_based_care::VP VBC",
    expectedAnswerSummary:
      "30-day readmit rate = readmits / discharges in value_based_care, alongside acute admits per 1k members.",
  },

  // -------- Telecom -----------------------------------------------------
  {
    id: "tel.churn.dashboard",
    text: "Which KPIs sit on a churn manager's dashboard?",
    vertical: "Telecom",
    personaKey: "churn_management::Head of Retention",
    expectedAnswerSummary:
      "Monthly churn rate, win-back rate, save offer acceptance, and involuntary churn share from churn_management.",
  },
  {
    id: "tel.billing.leakage",
    text: "How is revenue leakage detected in subscriber billing?",
    vertical: "Telecom",
    personaKey: "subscriber_billing::Revenue Assurance Lead",
    expectedAnswerSummary:
      "Revenue leakage = unbilled_usage / total_usage on the rated CDR fact in subscriber_billing.",
  },
  {
    id: "tel.qoe",
    text: "What signals feed video QoE scoring?",
    vertical: "Telecom",
    personaKey: "video_streaming_qoe::CDN Architect",
    expectedAnswerSummary:
      "Startup time, rebuffer ratio, average bitrate, and playback failure rate from the video_streaming_qoe player beacons.",
  },

  // -------- Media -------------------------------------------------------
  {
    id: "media.saas.retention",
    text: "What's the canonical SaaS retention KPI stack?",
    vertical: "Media",
    personaKey: "saas_metrics::VP RevOps",
    expectedAnswerSummary:
      "ARR, NRR, gross logo churn, and CAC payback anchor saas_metrics; cohort retention hangs off the subscription fact.",
  },

  // -------- Energy ------------------------------------------------------
  {
    id: "energy.capacity_factor",
    text: "How do I compute capacity factor for a wind site?",
    vertical: "Energy",
    personaKey: "renewable_generation::Forecasting Lead",
    expectedAnswerSummary:
      "Capacity factor = actual_mwh / nameplate_max from the SCADA historian aggregated hourly in renewable_generation.",
  },

  // -------- Utilities ---------------------------------------------------
  {
    id: "util.saidi_saifi",
    text: "How do SAIDI and SAIFI relate, and what feeds them?",
    vertical: "Utilities",
    personaKey: "outage_management::Outage Manager",
    expectedAnswerSummary:
      "SAIDI = customer-minutes lost / customers; SAIFI = interruptions / customers; CAIDI = SAIDI/SAIFI. All from the OMS event stream.",
  },

  // -------- PublicSector ------------------------------------------------
  {
    id: "ps.eligibility",
    text: "Which KPIs matter for a benefits eligibility program?",
    vertical: "PublicSector",
    personaKey: "social_services_case_management::Eligibility Worker Lead",
    expectedAnswerSummary:
      "Eligibility determination cycle, timely recerts, improper payment rate, and caseworker load from social_services_case_management.",
  },

  // -------- HiTech ------------------------------------------------------
  {
    id: "hitech.yield",
    text: "Which KPIs do yield engineers track at wafer level?",
    vertical: "HiTech",
    personaKey: "semiconductor_yield::Yield Engineer",
    expectedAnswerSummary:
      "Die yield, parametric yield, defect density, and line yield from semiconductor_yield.",
  },

  // -------- ProfessionalServices ----------------------------------------
  {
    id: "ps.utilisation",
    text: "How do utilisation and realisation differ for billable teams?",
    vertical: "ProfessionalServices",
    personaKey: "time_and_billing::Engagement Manager",
    expectedAnswerSummary:
      "Utilisation = billable / available hours from the timecard fact; realisation = collected / standard from the invoice fact.",
  },
  {
    id: "ps.lockup",
    text: "What goes into lockup days, and how do I shorten it?",
    vertical: "ProfessionalServices",
    personaKey: "time_and_billing::Billing Director",
    expectedAnswerSummary:
      "Lockup days = WIP days + AR days; the time_and_billing mart joins timecards, invoices, and AR aging.",
  },

  // -------- Cross-cutting ----------------------------------------------
  {
    id: "x.lineage.fact_payments",
    text: "Show me the lineage for fact_payments_daily.",
    vertical: "CrossCutting",
    expectedAnswerSummary:
      "fact_payments_daily is a dimensional fact built from acquirer events, clearing, and settlement in the payments subdomain.",
  },
  {
    id: "x.modelled_subdomains",
    text: "Which subdomains have full data models vs lightweight?",
    vertical: "CrossCutting",
    expectedAnswerSummary:
      "Most subdomains carry KPIs and decisions; full ERD/DDL artifacts exist for payments, claims, merchandising, demand_planning, and hotel_revenue_management.",
  },
  {
    id: "x.persona_drilldown",
    text: "Pick any persona and show me their decisions and supporting KPIs.",
    vertical: "CrossCutting",
    expectedAnswerSummary:
      "The grounding traversal walks persona->decisions->KPIs and lists each with formula and unit.",
  },
];

/**
 * Suggestions used as the "tour" set when no persona is selected. Hand-picked
 * to span verticals so the user sees breadth.
 */
const TOUR_IDS = [
  "bfsi.payments.head.kpis",
  "tth.revpar.lineage",
  "mfg.oee.sources",
  "hc.fhir.kpis",
  "ls.adverse.event.path",
  "x.lineage.fact_payments",
];

/** The cross-vertical chip set rendered when no persona is selected. */
export const tourSuggestions: AssistantSuggestion[] = TOUR_IDS.map((id) => {
  const s = SUGGESTIONS.find((x) => x.id === id);
  if (!s) throw new Error(`tour suggestion id not found: ${id}`);
  return s;
});

/**
 * Filter suggestions for a vertical. Pads with cross-cutting and a couple of
 * tour entries when the vertical is sparse, so the chip card always has at
 * least 4 entries.
 */
export function suggestionsForVertical(
  vertical?: string | null,
  limit = 6,
): AssistantSuggestion[] {
  if (!vertical) return tourSuggestions.slice(0, limit);
  const exact = SUGGESTIONS.filter((s) => s.vertical === vertical);
  if (exact.length >= limit) return exact.slice(0, limit);
  const cross = SUGGESTIONS.filter((s) => s.vertical === "CrossCutting");
  const merged = [...exact, ...cross];
  // Backfill with tour entries if still short.
  for (const t of tourSuggestions) {
    if (merged.length >= limit) break;
    if (!merged.find((m) => m.id === t.id)) merged.push(t);
  }
  return merged.slice(0, limit);
}

/** Total suggestion count — exposed so the UI / tests can sanity-check. */
export const SUGGESTION_COUNT = SUGGESTIONS.length;
