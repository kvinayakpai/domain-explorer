// Hand-curated column-level lineage graphs for the seven anchor subdomains.
// Each graph follows a six-column layout:
//   0: Source systems
//   1: Staging
//   2: Vault hubs / links
//   3: Vault satellites
//   4: Marts (star)
//   5: KPIs
// The diagram component (`components/lineage-diagram.tsx`) renders any of these.
//
// Names are pulled from the corresponding YAML in `data/taxonomy/<anchor>.yaml`
// and the DDL in `modeling/ddl/<anchor>_*.sql`. The intent is realism, not
// exhaustive coverage — about 30 nodes per anchor scans cleanly at desktop
// width and remains scrollable on mobile.

export type LineageKind = "source" | "stage" | "vault" | "mart" | "kpi";

export interface LineageNode {
  id: string;
  label: string;
  sub?: string;
  layer: number; // column index 0..5
  row: number; // row index 0..n
  kind: LineageKind;
}

export interface LineageEdge {
  from: string;
  to: string;
}

export interface LineageGraph {
  title: string;
  vertical: string;
  oneLiner: string;
  nodes: LineageNode[];
  edges: LineageEdge[];
}

export const ANCHOR_KEYS = [
  "payments",
  "p_and_c_claims",
  "merchandising",
  "demand_planning",
  "hotel_revenue_management",
  "mes_quality",
  "pharmacovigilance",
] as const;

export type AnchorKey = (typeof ANCHOR_KEYS)[number];

// ---------------------------------------------------------------------------
// payments
// ---------------------------------------------------------------------------

const payments: LineageGraph = {
  title: "Payments",
  vertical: "BFSI",
  oneLiner:
    "Money movement across cards, ACH, wires, and real-time rails — auth, clearing, settlement, and dispute handling end-to-end.",
  nodes: [
    // sources
    { id: "src.stripe", label: "Stripe", sub: "Acquirer/PSP", layer: 0, row: 0, kind: "source" },
    { id: "src.temenos", label: "Temenos Transact", sub: "Core Banking", layer: 0, row: 1, kind: "source" },
    { id: "src.fis", label: "FIS Profile", sub: "Core Banking", layer: 0, row: 2, kind: "source" },
    { id: "src.aci", label: "ACI EPS", sub: "Payments Hub", layer: 0, row: 3, kind: "source" },
    { id: "src.swift", label: "SWIFT Alliance", sub: "Messaging", layer: 0, row: 4, kind: "source" },
    // staging
    { id: "stg.payments", label: "stg_payments__payments", sub: "view", layer: 1, row: 0, kind: "stage" },
    { id: "stg.settle", label: "stg_payments__settlements", sub: "view", layer: 1, row: 1, kind: "stage" },
    { id: "stg.cb", label: "stg_payments__chargebacks", sub: "view", layer: 1, row: 2, kind: "stage" },
    { id: "stg.cust", label: "stg_payments__customers", sub: "view", layer: 1, row: 3, kind: "stage" },
    { id: "stg.merch", label: "stg_payments__merchants", sub: "view", layer: 1, row: 4, kind: "stage" },
    // vault hubs & links
    { id: "vault.h_payment", label: "hub_payment", sub: "Vault hub", layer: 2, row: 0, kind: "vault" },
    { id: "vault.h_customer", label: "hub_customer", sub: "Vault hub", layer: 2, row: 1, kind: "vault" },
    { id: "vault.h_merchant", label: "hub_merchant", sub: "Vault hub", layer: 2, row: 2, kind: "vault" },
    { id: "vault.l_pc", label: "link_payment_customer", sub: "Vault link", layer: 2, row: 3, kind: "vault" },
    { id: "vault.l_pm", label: "link_payment_merchant", sub: "Vault link", layer: 2, row: 4, kind: "vault" },
    // vault sats
    { id: "vault.s_payment", label: "sat_payment", sub: "Vault sat", layer: 3, row: 0, kind: "vault" },
    { id: "vault.s_settle", label: "sat_settlement", sub: "Vault sat", layer: 3, row: 1, kind: "vault" },
    { id: "vault.s_cb", label: "sat_chargeback", sub: "Vault sat", layer: 3, row: 2, kind: "vault" },
    { id: "vault.s_cust", label: "sat_customer", sub: "Vault sat", layer: 3, row: 3, kind: "vault" },
    { id: "vault.s_merch", label: "sat_merchant", sub: "Vault sat", layer: 3, row: 4, kind: "vault" },
    // marts
    { id: "mart.fct_payments", label: "fct_payments", sub: "fact (table)", layer: 4, row: 0, kind: "mart" },
    { id: "mart.fct_settle", label: "fct_settlements", sub: "fact (table)", layer: 4, row: 1, kind: "mart" },
    { id: "mart.fct_cb", label: "fct_chargebacks", sub: "fact (table)", layer: 4, row: 2, kind: "mart" },
    { id: "mart.dim_cust", label: "dim_customer", sub: "dim (table)", layer: 4, row: 3, kind: "mart" },
    { id: "mart.dim_merch", label: "dim_merchant", sub: "dim (table)", layer: 4, row: 4, kind: "mart" },
    // KPIs
    { id: "kpi.stp", label: "STP Rate", sub: "pay.kpi.stp_rate", layer: 5, row: 0, kind: "kpi" },
    { id: "kpi.lat", label: "Settlement Latency", sub: "pay.kpi.settlement_latency", layer: 5, row: 1, kind: "kpi" },
    { id: "kpi.cb", label: "Chargeback Ratio", sub: "pay.kpi.chargeback_ratio", layer: 5, row: 2, kind: "kpi" },
    { id: "kpi.afr", label: "Auth Failure Rate", sub: "pay.kpi.afr", layer: 5, row: 3, kind: "kpi" },
    { id: "kpi.ic", label: "Interchange Revenue", sub: "pay.kpi.interchange_revenue", layer: 5, row: 4, kind: "kpi" },
  ],
  edges: [
    { from: "src.stripe", to: "stg.payments" },
    { from: "src.aci", to: "stg.payments" },
    { from: "src.aci", to: "stg.settle" },
    { from: "src.swift", to: "stg.settle" },
    { from: "src.temenos", to: "stg.cb" },
    { from: "src.fis", to: "stg.cust" },
    { from: "src.temenos", to: "stg.cust" },
    { from: "src.stripe", to: "stg.merch" },
    { from: "stg.payments", to: "vault.h_payment" },
    { from: "stg.payments", to: "vault.s_payment" },
    { from: "stg.cust", to: "vault.h_customer" },
    { from: "stg.cust", to: "vault.s_cust" },
    { from: "stg.merch", to: "vault.h_merchant" },
    { from: "stg.merch", to: "vault.s_merch" },
    { from: "stg.settle", to: "vault.s_settle" },
    { from: "stg.cb", to: "vault.s_cb" },
    { from: "vault.h_payment", to: "vault.l_pc" },
    { from: "vault.h_customer", to: "vault.l_pc" },
    { from: "vault.h_payment", to: "vault.l_pm" },
    { from: "vault.h_merchant", to: "vault.l_pm" },
    { from: "vault.s_payment", to: "mart.fct_payments" },
    { from: "vault.l_pc", to: "mart.fct_payments" },
    { from: "vault.l_pm", to: "mart.fct_payments" },
    { from: "vault.s_settle", to: "mart.fct_settle" },
    { from: "vault.s_cb", to: "mart.fct_cb" },
    { from: "vault.s_cust", to: "mart.dim_cust" },
    { from: "vault.s_merch", to: "mart.dim_merch" },
    { from: "mart.fct_payments", to: "kpi.stp" },
    { from: "mart.fct_payments", to: "kpi.afr" },
    { from: "mart.fct_settle", to: "kpi.lat" },
    { from: "mart.fct_cb", to: "kpi.cb" },
    { from: "mart.fct_payments", to: "kpi.ic" },
  ],
};

// ---------------------------------------------------------------------------
// p_and_c_claims
// ---------------------------------------------------------------------------

const pAndCClaims: LineageGraph = {
  title: "P&C Claims",
  vertical: "Insurance",
  oneLiner:
    "FNOL through closure for property & casualty claims — assignment, reserves, payouts, and recovery, with bitemporal reserve history.",
  nodes: [
    { id: "src.gw", label: "Guidewire ClaimCenter", sub: "Claims Platform", layer: 0, row: 0, kind: "source" },
    { id: "src.dc", label: "Duck Creek Claims", sub: "Claims Platform", layer: 0, row: 1, kind: "source" },
    { id: "src.sf", label: "Salesforce FSC", sub: "Customer 360", layer: 0, row: 2, kind: "source" },
    { id: "src.ir", label: "ImageRight", sub: "Claims Docs", layer: 0, row: 3, kind: "source" },
    { id: "src.iso", label: "ISO ClaimSearch", sub: "Industry Data", layer: 0, row: 4, kind: "source" },
    { id: "stg.claims", label: "stg_claims", sub: "view", layer: 1, row: 0, kind: "stage" },
    { id: "stg.policies", label: "stg_policies", sub: "view", layer: 1, row: 1, kind: "stage" },
    { id: "stg.adjusters", label: "stg_adjusters", sub: "view", layer: 1, row: 2, kind: "stage" },
    { id: "stg.fnol", label: "stg_fnol_events", sub: "view", layer: 1, row: 3, kind: "stage" },
    { id: "stg.payouts", label: "stg_claim_payments", sub: "view", layer: 1, row: 4, kind: "stage" },
    { id: "vault.h_claim", label: "hub_claim", sub: "Vault hub", layer: 2, row: 0, kind: "vault" },
    { id: "vault.h_policy", label: "hub_policy", sub: "Vault hub", layer: 2, row: 1, kind: "vault" },
    { id: "vault.h_adj", label: "hub_adjuster", sub: "Vault hub", layer: 2, row: 2, kind: "vault" },
    { id: "vault.l_cp", label: "link_claim_policy", sub: "Vault link", layer: 2, row: 3, kind: "vault" },
    { id: "vault.l_ca", label: "link_claim_adjuster", sub: "Vault link", layer: 2, row: 4, kind: "vault" },
    { id: "vault.s_cstate", label: "sat_claim_state", sub: "Vault sat", layer: 3, row: 0, kind: "vault" },
    { id: "vault.s_reserve", label: "sat_claim_reserve_bitemporal", sub: "Vault sat (bitemporal)", layer: 3, row: 1, kind: "vault" },
    { id: "vault.s_pol", label: "sat_policy_descriptive", sub: "Vault sat", layer: 3, row: 2, kind: "vault" },
    { id: "vault.s_phold", label: "sat_policyholder_descriptive", sub: "Vault sat", layer: 3, row: 3, kind: "vault" },
    { id: "vault.s_pay", label: "sat_payout_state", sub: "Vault sat", layer: 3, row: 4, kind: "vault" },
    { id: "mart.fct_claim", label: "fact_claim_event", sub: "fact (table)", layer: 4, row: 0, kind: "mart" },
    { id: "mart.fct_pay", label: "fact_claim_payment_daily", sub: "fact (daily)", layer: 4, row: 1, kind: "mart" },
    { id: "mart.fct_tri", label: "fact_loss_triangle", sub: "fact (table)", layer: 4, row: 2, kind: "mart" },
    { id: "mart.dim_pol", label: "dim_policy", sub: "dim (SCD2)", layer: 4, row: 3, kind: "mart" },
    { id: "mart.dim_adj", label: "dim_adjuster", sub: "dim (table)", layer: 4, row: 4, kind: "mart" },
    { id: "kpi.cycle", label: "Claim Cycle Time", sub: "pcc.kpi.cycle_time", layer: 5, row: 0, kind: "kpi" },
    { id: "kpi.leak", label: "Claims Leakage", sub: "pcc.kpi.leakage", layer: 5, row: 1, kind: "kpi" },
    { id: "kpi.sev", label: "Severity", sub: "pcc.kpi.severity", layer: 5, row: 2, kind: "kpi" },
    { id: "kpi.freq", label: "Frequency", sub: "pcc.kpi.frequency", layer: 5, row: 3, kind: "kpi" },
    { id: "kpi.lae", label: "LAE Ratio", sub: "pcc.kpi.lae_ratio", layer: 5, row: 4, kind: "kpi" },
  ],
  edges: [
    { from: "src.gw", to: "stg.claims" },
    { from: "src.dc", to: "stg.claims" },
    { from: "src.gw", to: "stg.fnol" },
    { from: "src.gw", to: "stg.payouts" },
    { from: "src.dc", to: "stg.policies" },
    { from: "src.sf", to: "stg.policies" },
    { from: "src.sf", to: "stg.adjusters" },
    { from: "src.ir", to: "stg.fnol" },
    { from: "src.iso", to: "stg.claims" },
    { from: "stg.claims", to: "vault.h_claim" },
    { from: "stg.claims", to: "vault.s_cstate" },
    { from: "stg.payouts", to: "vault.s_reserve" },
    { from: "stg.policies", to: "vault.h_policy" },
    { from: "stg.policies", to: "vault.s_pol" },
    { from: "stg.policies", to: "vault.s_phold" },
    { from: "stg.adjusters", to: "vault.h_adj" },
    { from: "stg.payouts", to: "vault.s_pay" },
    { from: "vault.h_claim", to: "vault.l_cp" },
    { from: "vault.h_policy", to: "vault.l_cp" },
    { from: "vault.h_claim", to: "vault.l_ca" },
    { from: "vault.h_adj", to: "vault.l_ca" },
    { from: "vault.s_cstate", to: "mart.fct_claim" },
    { from: "vault.l_cp", to: "mart.fct_claim" },
    { from: "vault.l_ca", to: "mart.fct_claim" },
    { from: "vault.s_pay", to: "mart.fct_pay" },
    { from: "vault.s_reserve", to: "mart.fct_tri" },
    { from: "vault.s_pol", to: "mart.dim_pol" },
    { from: "vault.s_phold", to: "mart.dim_pol" },
    { from: "vault.h_adj", to: "mart.dim_adj" },
    { from: "mart.fct_claim", to: "kpi.cycle" },
    { from: "mart.fct_claim", to: "kpi.leak" },
    { from: "mart.fct_claim", to: "kpi.sev" },
    { from: "mart.fct_claim", to: "kpi.freq" },
    { from: "mart.fct_pay", to: "kpi.lae" },
    { from: "mart.fct_tri", to: "kpi.lae" },
  ],
};

// ---------------------------------------------------------------------------
// merchandising
// ---------------------------------------------------------------------------

const merchandising: LineageGraph = {
  title: "Merchandising",
  vertical: "Retail",
  oneLiner:
    "Plan, buy, allocate, price, and clear assortments — sales, inventory, markdowns, and supplier performance across stores and channels.",
  nodes: [
    { id: "src.rms", label: "Oracle RMS", sub: "MMS", layer: 0, row: 0, kind: "source" },
    { id: "src.sap", label: "SAP IS-Retail", sub: "ERP", layer: 0, row: 1, kind: "source" },
    { id: "src.mhn", label: "Manhattan Active Omni", sub: "OMS", layer: 0, row: 2, kind: "source" },
    { id: "src.by", label: "Blue Yonder Planning", sub: "Planning", layer: 0, row: 3, kind: "source" },
    { id: "src.pos", label: "Toshiba TCx", sub: "Store POS", layer: 0, row: 4, kind: "source" },
    { id: "stg.sku", label: "stg_sku", sub: "view", layer: 1, row: 0, kind: "stage" },
    { id: "stg.inv", label: "stg_inventory", sub: "view", layer: 1, row: 1, kind: "stage" },
    { id: "stg.sales", label: "stg_sales_lines", sub: "view", layer: 1, row: 2, kind: "stage" },
    { id: "stg.po", label: "stg_purchase_orders", sub: "view", layer: 1, row: 3, kind: "stage" },
    { id: "stg.store", label: "stg_stores", sub: "view", layer: 1, row: 4, kind: "stage" },
    { id: "vault.h_sku", label: "hub_sku", sub: "Vault hub", layer: 2, row: 0, kind: "vault" },
    { id: "vault.h_store", label: "hub_store", sub: "Vault hub", layer: 2, row: 1, kind: "vault" },
    { id: "vault.h_supp", label: "hub_supplier", sub: "Vault hub", layer: 2, row: 2, kind: "vault" },
    { id: "vault.l_sales", label: "link_sales_line", sub: "Vault link", layer: 2, row: 3, kind: "vault" },
    { id: "vault.l_inv", label: "link_inventory_position", sub: "Vault link", layer: 2, row: 4, kind: "vault" },
    { id: "vault.s_sku", label: "sat_sku_descriptive", sub: "Vault sat", layer: 3, row: 0, kind: "vault" },
    { id: "vault.s_price", label: "sat_sku_pricing", sub: "Vault sat", layer: 3, row: 1, kind: "vault" },
    { id: "vault.s_store", label: "sat_store_descriptive", sub: "Vault sat", layer: 3, row: 2, kind: "vault" },
    { id: "vault.s_inv", label: "sat_inventory_position", sub: "Vault sat", layer: 3, row: 3, kind: "vault" },
    { id: "vault.s_sales", label: "sat_sales_line_state", sub: "Vault sat", layer: 3, row: 4, kind: "vault" },
    { id: "mart.fct_sales", label: "fact_sales_daily", sub: "fact (daily)", layer: 4, row: 0, kind: "mart" },
    { id: "mart.fct_inv", label: "fact_inventory_snapshot", sub: "fact (snap)", layer: 4, row: 1, kind: "mart" },
    { id: "mart.fct_md", label: "fact_markdown", sub: "fact (table)", layer: 4, row: 2, kind: "mart" },
    { id: "mart.dim_sku", label: "dim_sku", sub: "dim (SCD2)", layer: 4, row: 3, kind: "mart" },
    { id: "mart.dim_store", label: "dim_store", sub: "dim (table)", layer: 4, row: 4, kind: "mart" },
    { id: "kpi.st", label: "Sell-through %", sub: "mer.kpi.sell_through", layer: 5, row: 0, kind: "kpi" },
    { id: "kpi.gmroi", label: "GMROI", sub: "mer.kpi.gmroi", layer: 5, row: 1, kind: "kpi" },
    { id: "kpi.md", label: "Markdown %", sub: "mer.kpi.markdown_pct", layer: 5, row: 2, kind: "kpi" },
    { id: "kpi.turn", label: "Inventory Turn", sub: "mer.kpi.inventory_turn", layer: 5, row: 3, kind: "kpi" },
    { id: "kpi.oos", label: "Out-of-Stock Rate", sub: "mer.kpi.oos", layer: 5, row: 4, kind: "kpi" },
  ],
  edges: [
    { from: "src.rms", to: "stg.sku" },
    { from: "src.sap", to: "stg.sku" },
    { from: "src.rms", to: "stg.inv" },
    { from: "src.mhn", to: "stg.inv" },
    { from: "src.pos", to: "stg.sales" },
    { from: "src.mhn", to: "stg.sales" },
    { from: "src.sap", to: "stg.po" },
    { from: "src.by", to: "stg.po" },
    { from: "src.rms", to: "stg.store" },
    { from: "stg.sku", to: "vault.h_sku" },
    { from: "stg.sku", to: "vault.s_sku" },
    { from: "stg.sku", to: "vault.s_price" },
    { from: "stg.store", to: "vault.h_store" },
    { from: "stg.store", to: "vault.s_store" },
    { from: "stg.po", to: "vault.h_supp" },
    { from: "stg.inv", to: "vault.l_inv" },
    { from: "stg.inv", to: "vault.s_inv" },
    { from: "stg.sales", to: "vault.l_sales" },
    { from: "stg.sales", to: "vault.s_sales" },
    { from: "vault.h_sku", to: "vault.l_inv" },
    { from: "vault.h_store", to: "vault.l_inv" },
    { from: "vault.h_sku", to: "vault.l_sales" },
    { from: "vault.h_store", to: "vault.l_sales" },
    { from: "vault.l_sales", to: "mart.fct_sales" },
    { from: "vault.s_sales", to: "mart.fct_sales" },
    { from: "vault.l_inv", to: "mart.fct_inv" },
    { from: "vault.s_inv", to: "mart.fct_inv" },
    { from: "vault.s_price", to: "mart.fct_md" },
    { from: "vault.s_sku", to: "mart.dim_sku" },
    { from: "vault.s_store", to: "mart.dim_store" },
    { from: "mart.fct_sales", to: "kpi.st" },
    { from: "mart.fct_sales", to: "kpi.gmroi" },
    { from: "mart.fct_md", to: "kpi.md" },
    { from: "mart.fct_inv", to: "kpi.turn" },
    { from: "mart.fct_inv", to: "kpi.oos" },
  ],
};

// ---------------------------------------------------------------------------
// demand_planning
// ---------------------------------------------------------------------------

const demandPlanning: LineageGraph = {
  title: "Demand Planning",
  vertical: "CPG",
  oneLiner:
    "Statistical and consensus forecasts with safety-stock and OTIF checks — driving production, replenishment, and S&OP decisions.",
  nodes: [
    { id: "src.ibp", label: "SAP IBP", sub: "Demand Planning", layer: 0, row: 0, kind: "source" },
    { id: "src.kx", label: "Kinaxis RapidResponse", sub: "Concurrent Planning", layer: 0, row: 1, kind: "source" },
    { id: "src.o9", label: "o9 Digital Brain", sub: "Planning", layer: 0, row: 2, kind: "source" },
    { id: "src.ana", label: "Anaplan", sub: "Planning", layer: 0, row: 3, kind: "source" },
    { id: "src.s4", label: "SAP S/4HANA", sub: "ERP / Orders", layer: 0, row: 4, kind: "source" },
    { id: "stg.fc", label: "stg_forecasts", sub: "view", layer: 1, row: 0, kind: "stage" },
    { id: "stg.ord", label: "stg_orders", sub: "view", layer: 1, row: 1, kind: "stage" },
    { id: "stg.invp", label: "stg_inventory", sub: "view", layer: 1, row: 2, kind: "stage" },
    { id: "stg.promo", label: "stg_promotions", sub: "view", layer: 1, row: 3, kind: "stage" },
    { id: "stg.ss", label: "stg_safety_stock", sub: "view", layer: 1, row: 4, kind: "stage" },
    { id: "vault.h_prod", label: "hub_product", sub: "Vault hub", layer: 2, row: 0, kind: "vault" },
    { id: "vault.h_loc", label: "hub_location", sub: "Vault hub", layer: 2, row: 1, kind: "vault" },
    { id: "vault.h_fc", label: "hub_forecast_cycle", sub: "Vault hub", layer: 2, row: 2, kind: "vault" },
    { id: "vault.l_fp", label: "link_forecast_point", sub: "Vault link", layer: 2, row: 3, kind: "vault" },
    { id: "vault.l_ol", label: "link_order_line", sub: "Vault link", layer: 2, row: 4, kind: "vault" },
    { id: "vault.s_fp", label: "sat_forecast_point_value", sub: "Vault sat", layer: 3, row: 0, kind: "vault" },
    { id: "vault.s_ol", label: "sat_order_line_state", sub: "Vault sat", layer: 3, row: 1, kind: "vault" },
    { id: "vault.s_ss", label: "sat_safety_stock_value", sub: "Vault sat", layer: 3, row: 2, kind: "vault" },
    { id: "vault.s_prod", label: "sat_product_descriptive", sub: "Vault sat", layer: 3, row: 3, kind: "vault" },
    { id: "vault.s_cust", label: "sat_customer_descriptive", sub: "Vault sat", layer: 3, row: 4, kind: "vault" },
    { id: "mart.fct_fva", label: "fact_forecast_vs_actual", sub: "fact (table)", layer: 4, row: 0, kind: "mart" },
    { id: "mart.fct_ord", label: "fact_orders_daily", sub: "fact (daily)", layer: 4, row: 1, kind: "mart" },
    { id: "mart.fct_inv", label: "fact_inventory_position", sub: "fact (snap)", layer: 4, row: 2, kind: "mart" },
    { id: "mart.fct_pl", label: "fact_promo_lift", sub: "fact (table)", layer: 4, row: 3, kind: "mart" },
    { id: "mart.dim_prod", label: "dim_product", sub: "dim (SCD2)", layer: 4, row: 4, kind: "mart" },
    { id: "kpi.mape", label: "Forecast Accuracy (MAPE)", sub: "dem.kpi.mape", layer: 5, row: 0, kind: "kpi" },
    { id: "kpi.bias", label: "Forecast Bias", sub: "dem.kpi.bias", layer: 5, row: 1, kind: "kpi" },
    { id: "kpi.fr", label: "Fill Rate", sub: "dem.kpi.fill_rate", layer: 5, row: 2, kind: "kpi" },
    { id: "kpi.otif", label: "OTIF", sub: "dem.kpi.otif", layer: 5, row: 3, kind: "kpi" },
    { id: "kpi.id", label: "Inventory Days", sub: "dem.kpi.inventory_days", layer: 5, row: 4, kind: "kpi" },
  ],
  edges: [
    { from: "src.ibp", to: "stg.fc" },
    { from: "src.kx", to: "stg.fc" },
    { from: "src.o9", to: "stg.fc" },
    { from: "src.ana", to: "stg.fc" },
    { from: "src.s4", to: "stg.ord" },
    { from: "src.s4", to: "stg.invp" },
    { from: "src.kx", to: "stg.invp" },
    { from: "src.ibp", to: "stg.promo" },
    { from: "src.ibp", to: "stg.ss" },
    { from: "stg.fc", to: "vault.h_prod" },
    { from: "stg.fc", to: "vault.h_fc" },
    { from: "stg.fc", to: "vault.l_fp" },
    { from: "stg.fc", to: "vault.s_fp" },
    { from: "stg.ord", to: "vault.l_ol" },
    { from: "stg.ord", to: "vault.s_ol" },
    { from: "stg.ss", to: "vault.s_ss" },
    { from: "stg.invp", to: "vault.h_loc" },
    { from: "stg.invp", to: "vault.s_prod" },
    { from: "stg.ord", to: "vault.s_cust" },
    { from: "vault.h_prod", to: "vault.l_fp" },
    { from: "vault.h_loc", to: "vault.l_fp" },
    { from: "vault.h_fc", to: "vault.l_fp" },
    { from: "vault.h_prod", to: "vault.l_ol" },
    { from: "vault.l_fp", to: "mart.fct_fva" },
    { from: "vault.s_fp", to: "mart.fct_fva" },
    { from: "vault.s_ol", to: "mart.fct_ord" },
    { from: "vault.l_ol", to: "mart.fct_ord" },
    { from: "vault.s_ss", to: "mart.fct_inv" },
    { from: "vault.s_fp", to: "mart.fct_pl" },
    { from: "vault.s_prod", to: "mart.dim_prod" },
    { from: "mart.fct_fva", to: "kpi.mape" },
    { from: "mart.fct_fva", to: "kpi.bias" },
    { from: "mart.fct_ord", to: "kpi.fr" },
    { from: "mart.fct_ord", to: "kpi.otif" },
    { from: "mart.fct_inv", to: "kpi.id" },
  ],
};

// ---------------------------------------------------------------------------
// hotel_revenue_management
// ---------------------------------------------------------------------------

const hotelRevenueManagement: LineageGraph = {
  title: "Hotel Revenue Management",
  vertical: "Travel & Hospitality",
  oneLiner:
    "Dynamic pricing for room nights — BAR ladders, demand forecasts, channel mix, and compset benchmarks driving RevPAR, ADR, and occupancy.",
  nodes: [
    { id: "src.opera", label: "Oracle Opera PMS", sub: "PMS", layer: 0, row: 0, kind: "source" },
    { id: "src.amad", label: "Amadeus HotSOS / RMS", sub: "GDS/RMS", layer: 0, row: 1, kind: "source" },
    { id: "src.ideas", label: "IDeaS G3 RMS", sub: "RMS", layer: 0, row: 2, kind: "source" },
    { id: "src.duetto", label: "Duetto GameChanger", sub: "RMS", layer: 0, row: 3, kind: "source" },
    { id: "src.str", label: "STR", sub: "Compset Benchmarks", layer: 0, row: 4, kind: "source" },
    { id: "stg.res", label: "stg_reservations", sub: "view", layer: 1, row: 0, kind: "stage" },
    { id: "stg.rn", label: "stg_room_nights", sub: "view", layer: 1, row: 1, kind: "stage" },
    { id: "stg.rate", label: "stg_rate_plans", sub: "view", layer: 1, row: 2, kind: "stage" },
    { id: "stg.compset", label: "stg_compset", sub: "view", layer: 1, row: 3, kind: "stage" },
    { id: "stg.bar", label: "stg_bar_history", sub: "view", layer: 1, row: 4, kind: "stage" },
    { id: "vault.h_prop", label: "hub_property", sub: "Vault hub", layer: 2, row: 0, kind: "vault" },
    { id: "vault.h_res", label: "hub_reservation", sub: "Vault hub", layer: 2, row: 1, kind: "vault" },
    { id: "vault.h_rate", label: "hub_rate_plan", sub: "Vault hub", layer: 2, row: 2, kind: "vault" },
    { id: "vault.l_rn", label: "link_room_night", sub: "Vault link", layer: 2, row: 3, kind: "vault" },
    { id: "vault.l_bar", label: "link_bar_rate", sub: "Vault link", layer: 2, row: 4, kind: "vault" },
    { id: "vault.s_res", label: "sat_reservation_state", sub: "Vault sat", layer: 3, row: 0, kind: "vault" },
    { id: "vault.s_prop", label: "sat_property_descriptive", sub: "Vault sat", layer: 3, row: 1, kind: "vault" },
    { id: "vault.s_rate", label: "sat_rate_plan_descriptive", sub: "Vault sat", layer: 3, row: 2, kind: "vault" },
    { id: "vault.s_rn", label: "sat_room_night_state", sub: "Vault sat", layer: 3, row: 3, kind: "vault" },
    { id: "vault.s_bar", label: "sat_bar_rate", sub: "Vault sat", layer: 3, row: 4, kind: "vault" },
    { id: "mart.fct_rn", label: "fact_room_night", sub: "fact (table)", layer: 4, row: 0, kind: "mart" },
    { id: "mart.fct_bc", label: "fact_booking_curve", sub: "fact (table)", layer: 4, row: 1, kind: "mart" },
    { id: "mart.fct_cs", label: "fact_compset", sub: "fact (table)", layer: 4, row: 2, kind: "mart" },
    { id: "mart.fct_bar", label: "fact_bar_history", sub: "fact (table)", layer: 4, row: 3, kind: "mart" },
    { id: "mart.dim_prop", label: "dim_property", sub: "dim (table)", layer: 4, row: 4, kind: "mart" },
    { id: "kpi.revpar", label: "RevPAR", sub: "hrm.kpi.revpar", layer: 5, row: 0, kind: "kpi" },
    { id: "kpi.adr", label: "ADR", sub: "hrm.kpi.adr", layer: 5, row: 1, kind: "kpi" },
    { id: "kpi.occ", label: "Occupancy", sub: "hrm.kpi.occupancy", layer: 5, row: 2, kind: "kpi" },
    { id: "kpi.mpi", label: "MPI", sub: "hrm.kpi.mpi", layer: 5, row: 3, kind: "kpi" },
    { id: "kpi.rgi", label: "RGI", sub: "hrm.kpi.rgi", layer: 5, row: 4, kind: "kpi" },
  ],
  edges: [
    { from: "src.opera", to: "stg.res" },
    { from: "src.opera", to: "stg.rn" },
    { from: "src.amad", to: "stg.res" },
    { from: "src.ideas", to: "stg.rate" },
    { from: "src.duetto", to: "stg.bar" },
    { from: "src.ideas", to: "stg.bar" },
    { from: "src.str", to: "stg.compset" },
    { from: "stg.res", to: "vault.h_res" },
    { from: "stg.res", to: "vault.s_res" },
    { from: "stg.rn", to: "vault.l_rn" },
    { from: "stg.rn", to: "vault.s_rn" },
    { from: "stg.rate", to: "vault.h_rate" },
    { from: "stg.rate", to: "vault.s_rate" },
    { from: "stg.rate", to: "vault.h_prop" },
    { from: "stg.bar", to: "vault.l_bar" },
    { from: "stg.bar", to: "vault.s_bar" },
    { from: "stg.compset", to: "vault.s_prop" },
    { from: "vault.h_res", to: "vault.l_rn" },
    { from: "vault.h_prop", to: "vault.l_rn" },
    { from: "vault.h_rate", to: "vault.l_bar" },
    { from: "vault.h_prop", to: "vault.l_bar" },
    { from: "vault.l_rn", to: "mart.fct_rn" },
    { from: "vault.s_rn", to: "mart.fct_rn" },
    { from: "vault.s_res", to: "mart.fct_bc" },
    { from: "vault.s_bar", to: "mart.fct_bar" },
    { from: "vault.l_bar", to: "mart.fct_bar" },
    { from: "vault.s_prop", to: "mart.dim_prop" },
    { from: "vault.s_prop", to: "mart.fct_cs" },
    { from: "mart.fct_rn", to: "kpi.revpar" },
    { from: "mart.fct_rn", to: "kpi.adr" },
    { from: "mart.fct_rn", to: "kpi.occ" },
    { from: "mart.fct_cs", to: "kpi.mpi" },
    { from: "mart.fct_cs", to: "kpi.rgi" },
  ],
};

// ---------------------------------------------------------------------------
// mes_quality
// ---------------------------------------------------------------------------

const mesQuality: LineageGraph = {
  title: "MES & Quality",
  vertical: "Manufacturing",
  oneLiner:
    "Shop-floor execution and quality — work orders, downtime, sensor reads, scrap, and non-conformance feeding OEE and reliability.",
  nodes: [
    { id: "src.siemens", label: "Siemens Opcenter", sub: "MES", layer: 0, row: 0, kind: "source" },
    { id: "src.rock", label: "Rockwell FactoryTalk PC", sub: "MES", layer: 0, row: 1, kind: "source" },
    { id: "src.ge", label: "GE Proficy Plant Apps", sub: "MES", layer: 0, row: 2, kind: "source" },
    { id: "src.sapdm", label: "SAP Digital Manufacturing", sub: "MES", layer: 0, row: 3, kind: "source" },
    { id: "src.pi", label: "AVEVA PI System", sub: "Historian", layer: 0, row: 4, kind: "source" },
    { id: "stg.wo", label: "stg_work_orders", sub: "view", layer: 1, row: 0, kind: "stage" },
    { id: "stg.sens", label: "stg_sensor_readings", sub: "view", layer: 1, row: 1, kind: "stage" },
    { id: "stg.dt", label: "stg_downtime_events", sub: "view", layer: 1, row: 2, kind: "stage" },
    { id: "stg.qc", label: "stg_quality_checks", sub: "view", layer: 1, row: 3, kind: "stage" },
    { id: "stg.nc", label: "stg_nonconformance", sub: "view", layer: 1, row: 4, kind: "stage" },
    { id: "vault.h_wo", label: "hub_work_order", sub: "Vault hub", layer: 2, row: 0, kind: "vault" },
    { id: "vault.h_eq", label: "hub_equipment", sub: "Vault hub", layer: 2, row: 1, kind: "vault" },
    { id: "vault.h_line", label: "hub_line", sub: "Vault hub", layer: 2, row: 2, kind: "vault" },
    { id: "vault.l_el", label: "link_equipment_line", sub: "Vault link", layer: 2, row: 3, kind: "vault" },
    { id: "vault.l_nc", label: "link_nc", sub: "Vault link", layer: 2, row: 4, kind: "vault" },
    { id: "vault.s_wo", label: "sat_wo_state", sub: "Vault sat", layer: 3, row: 0, kind: "vault" },
    { id: "vault.s_eq", label: "sat_equipment_descriptive", sub: "Vault sat", layer: 3, row: 1, kind: "vault" },
    { id: "vault.s_sens", label: "sat_sensor_reading", sub: "Vault sat", layer: 3, row: 2, kind: "vault" },
    { id: "vault.s_dt", label: "sat_downtime_event", sub: "Vault sat", layer: 3, row: 3, kind: "vault" },
    { id: "vault.s_nc", label: "sat_nc_descriptive", sub: "Vault sat", layer: 3, row: 4, kind: "vault" },
    { id: "mart.fct_oee", label: "fact_oee_hourly", sub: "fact (hourly)", layer: 4, row: 0, kind: "mart" },
    { id: "mart.fct_qc", label: "fact_quality_check", sub: "fact (table)", layer: 4, row: 1, kind: "mart" },
    { id: "mart.fct_dt", label: "fact_downtime", sub: "fact (table)", layer: 4, row: 2, kind: "mart" },
    { id: "mart.fct_rel", label: "fact_equipment_reliability", sub: "fact (table)", layer: 4, row: 3, kind: "mart" },
    { id: "mart.dim_eq", label: "dim_equipment", sub: "dim (table)", layer: 4, row: 4, kind: "mart" },
    { id: "kpi.oee", label: "OEE", sub: "mes.kpi.oee", layer: 5, row: 0, kind: "kpi" },
    { id: "kpi.fpy", label: "First Pass Yield", sub: "mes.kpi.fpy", layer: 5, row: 1, kind: "kpi" },
    { id: "kpi.scrap", label: "Scrap Rate", sub: "mes.kpi.scrap", layer: 5, row: 2, kind: "kpi" },
    { id: "kpi.mtbf", label: "MTBF", sub: "mes.kpi.mtbf", layer: 5, row: 3, kind: "kpi" },
    { id: "kpi.mttr", label: "MTTR", sub: "mes.kpi.mttr", layer: 5, row: 4, kind: "kpi" },
  ],
  edges: [
    { from: "src.siemens", to: "stg.wo" },
    { from: "src.rock", to: "stg.wo" },
    { from: "src.sapdm", to: "stg.wo" },
    { from: "src.pi", to: "stg.sens" },
    { from: "src.ge", to: "stg.sens" },
    { from: "src.rock", to: "stg.dt" },
    { from: "src.siemens", to: "stg.dt" },
    { from: "src.ge", to: "stg.qc" },
    { from: "src.siemens", to: "stg.nc" },
    { from: "stg.wo", to: "vault.h_wo" },
    { from: "stg.wo", to: "vault.s_wo" },
    { from: "stg.sens", to: "vault.h_eq" },
    { from: "stg.sens", to: "vault.s_sens" },
    { from: "stg.sens", to: "vault.s_eq" },
    { from: "stg.dt", to: "vault.s_dt" },
    { from: "stg.dt", to: "vault.h_line" },
    { from: "stg.nc", to: "vault.l_nc" },
    { from: "stg.nc", to: "vault.s_nc" },
    { from: "vault.h_eq", to: "vault.l_el" },
    { from: "vault.h_line", to: "vault.l_el" },
    { from: "vault.h_wo", to: "vault.l_nc" },
    { from: "vault.l_el", to: "mart.fct_oee" },
    { from: "vault.s_sens", to: "mart.fct_oee" },
    { from: "vault.s_wo", to: "mart.fct_qc" },
    { from: "vault.l_nc", to: "mart.fct_qc" },
    { from: "vault.s_dt", to: "mart.fct_dt" },
    { from: "vault.s_eq", to: "mart.fct_rel" },
    { from: "vault.s_eq", to: "mart.dim_eq" },
    { from: "mart.fct_oee", to: "kpi.oee" },
    { from: "mart.fct_qc", to: "kpi.fpy" },
    { from: "mart.fct_qc", to: "kpi.scrap" },
    { from: "mart.fct_rel", to: "kpi.mtbf" },
    { from: "mart.fct_dt", to: "kpi.mttr" },
  ],
};

// ---------------------------------------------------------------------------
// pharmacovigilance
// ---------------------------------------------------------------------------

const pharmacovigilance: LineageGraph = {
  title: "Pharmacovigilance",
  vertical: "Life Sciences",
  oneLiner:
    "ICSR intake, MedDRA coding, regulatory submission, and signal detection — drug safety operations end-to-end.",
  nodes: [
    { id: "src.argus", label: "Oracle Argus Safety", sub: "Safety Database", layer: 0, row: 0, kind: "source" },
    { id: "src.aris", label: "ArisGlobal LifeSphere", sub: "Safety Database", layer: 0, row: 1, kind: "source" },
    { id: "src.veeva", label: "Veeva Vault Safety", sub: "Safety Database", layer: 0, row: 2, kind: "source" },
    { id: "src.faers", label: "FDA FAERS", sub: "Public AE Feed", layer: 0, row: 3, kind: "source" },
    { id: "src.meddra", label: "MedDRA", sub: "Terminology", layer: 0, row: 4, kind: "source" },
    { id: "stg.icsr", label: "stg_icsrs", sub: "view", layer: 1, row: 0, kind: "stage" },
    { id: "stg.ae", label: "stg_ae_terms", sub: "view", layer: 1, row: 1, kind: "stage" },
    { id: "stg.sub", label: "stg_submissions", sub: "view", layer: 1, row: 2, kind: "stage" },
    { id: "stg.sig", label: "stg_signals", sub: "view", layer: 1, row: 3, kind: "stage" },
    { id: "stg.prod", label: "stg_products", sub: "view", layer: 1, row: 4, kind: "stage" },
    { id: "vault.h_icsr", label: "hub_icsr", sub: "Vault hub", layer: 2, row: 0, kind: "vault" },
    { id: "vault.h_prod", label: "hub_product", sub: "Vault hub", layer: 2, row: 1, kind: "vault" },
    { id: "vault.h_md", label: "hub_meddra_term", sub: "Vault hub", layer: 2, row: 2, kind: "vault" },
    { id: "vault.l_ae", label: "link_ae_meddra", sub: "Vault link", layer: 2, row: 3, kind: "vault" },
    { id: "vault.l_sub", label: "link_submission", sub: "Vault link", layer: 2, row: 4, kind: "vault" },
    { id: "vault.s_icsr", label: "sat_icsr_state", sub: "Vault sat", layer: 3, row: 0, kind: "vault" },
    { id: "vault.s_prod", label: "sat_product_descriptive", sub: "Vault sat", layer: 3, row: 1, kind: "vault" },
    { id: "vault.s_md", label: "sat_meddra_descriptive", sub: "Vault sat", layer: 3, row: 2, kind: "vault" },
    { id: "vault.s_sub", label: "sat_submission_state", sub: "Vault sat", layer: 3, row: 3, kind: "vault" },
    { id: "vault.s_sig", label: "sat_signal_state", sub: "Vault sat", layer: 3, row: 4, kind: "vault" },
    { id: "mart.fct_icsr", label: "fact_icsr", sub: "fact (table)", layer: 4, row: 0, kind: "mart" },
    { id: "mart.fct_sub", label: "fact_submission", sub: "fact (table)", layer: 4, row: 1, kind: "mart" },
    { id: "mart.fct_sig", label: "fact_signal", sub: "fact (table)", layer: 4, row: 2, kind: "mart" },
    { id: "mart.fct_vol", label: "fact_case_volume_daily", sub: "fact (daily)", layer: 4, row: 3, kind: "mart" },
    { id: "mart.dim_md", label: "dim_meddra", sub: "dim (SCD2)", layer: 4, row: 4, kind: "mart" },
    { id: "kpi.cpt", label: "Case Processing Time", sub: "pv.kpi.case_processing_time", layer: 5, row: 0, kind: "kpi" },
    { id: "kpi.sl", label: "Signal Detection Latency", sub: "pv.kpi.signal_latency", layer: 5, row: 1, kind: "kpi" },
    { id: "kpi.st", label: "Submission Timeliness", sub: "pv.kpi.submission_timeliness", layer: 5, row: 2, kind: "kpi" },
    { id: "kpi.vol", label: "ICSR Volume", sub: "pv.kpi.icsr_volume", layer: 5, row: 3, kind: "kpi" },
    { id: "kpi.acc", label: "AE→PT Mapping Accuracy", sub: "pv.kpi.ae_pt_accuracy", layer: 5, row: 4, kind: "kpi" },
  ],
  edges: [
    { from: "src.argus", to: "stg.icsr" },
    { from: "src.aris", to: "stg.icsr" },
    { from: "src.veeva", to: "stg.icsr" },
    { from: "src.faers", to: "stg.icsr" },
    { from: "src.meddra", to: "stg.ae" },
    { from: "src.argus", to: "stg.ae" },
    { from: "src.argus", to: "stg.sub" },
    { from: "src.veeva", to: "stg.sub" },
    { from: "src.aris", to: "stg.sig" },
    { from: "src.argus", to: "stg.prod" },
    { from: "stg.icsr", to: "vault.h_icsr" },
    { from: "stg.icsr", to: "vault.s_icsr" },
    { from: "stg.prod", to: "vault.h_prod" },
    { from: "stg.prod", to: "vault.s_prod" },
    { from: "stg.ae", to: "vault.h_md" },
    { from: "stg.ae", to: "vault.s_md" },
    { from: "stg.ae", to: "vault.l_ae" },
    { from: "stg.sub", to: "vault.l_sub" },
    { from: "stg.sub", to: "vault.s_sub" },
    { from: "stg.sig", to: "vault.s_sig" },
    { from: "vault.h_icsr", to: "vault.l_ae" },
    { from: "vault.h_md", to: "vault.l_ae" },
    { from: "vault.h_icsr", to: "vault.l_sub" },
    { from: "vault.s_icsr", to: "mart.fct_icsr" },
    { from: "vault.l_ae", to: "mart.fct_icsr" },
    { from: "vault.l_sub", to: "mart.fct_sub" },
    { from: "vault.s_sub", to: "mart.fct_sub" },
    { from: "vault.s_sig", to: "mart.fct_sig" },
    { from: "vault.s_icsr", to: "mart.fct_vol" },
    { from: "vault.s_md", to: "mart.dim_md" },
    { from: "mart.fct_icsr", to: "kpi.cpt" },
    { from: "mart.fct_sig", to: "kpi.sl" },
    { from: "mart.fct_sub", to: "kpi.st" },
    { from: "mart.fct_vol", to: "kpi.vol" },
    { from: "mart.fct_icsr", to: "kpi.acc" },
  ],
};

export const anchorLineages: Record<AnchorKey, LineageGraph> = {
  payments,
  p_and_c_claims: pAndCClaims,
  merchandising,
  demand_planning: demandPlanning,
  hotel_revenue_management: hotelRevenueManagement,
  mes_quality: mesQuality,
  pharmacovigilance,
};

// Slug used in the URL — same as the AnchorKey but we keep them aligned
// so that the registry's subdomain id (which uses underscores) maps cleanly.
export const anchorSlugs: Record<AnchorKey, string> = {
  payments: "payments",
  p_and_c_claims: "p_and_c_claims",
  merchandising: "merchandising",
  demand_planning: "demand_planning",
  hotel_revenue_management: "hotel_revenue_management",
  mes_quality: "mes_quality",
  pharmacovigilance: "pharmacovigilance",
};
