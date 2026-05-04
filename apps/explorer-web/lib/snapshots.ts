import "server-only";
import { queryOne } from "./duckdb";

export type Stat = {
  label: string;
  value: string;
  hint?: string;
};

type StatBuilder = () => Promise<Stat[]>;

const num = (v: any): number | null => {
  if (v === null || v === undefined) return null;
  const n = typeof v === "number" ? v : Number(v);
  return Number.isFinite(n) ? n : null;
};
const fmt = (v: any, opts: Intl.NumberFormatOptions = {}): string => {
  const n = num(v);
  return n === null ? "—" : new Intl.NumberFormat("en-US", opts).format(n);
};
const pct = (v: any, digits = 2): string => {
  const n = num(v);
  return n === null ? "—" : `${n.toFixed(digits)}%`;
};
const dollars = (v: any, digits = 0): string => {
  const n = num(v);
  return n === null
    ? "—"
    : `$${new Intl.NumberFormat("en-US", { maximumFractionDigits: digits }).format(n)}`;
};

const BUILDERS: Record<string, StatBuilder> = {
  payments: async () => {
    const r = await queryOne<any>(`
      SELECT
        (SELECT count(*) FROM payments.payments) AS total_payments,
        (SELECT 100.0 * sum(case when is_stp then 1 else 0 end) / count(*) FROM payments.payments) AS stp_rate,
        (SELECT quantile_cont(date_diff('minute', auth_ts, settlement_ts) / 60.0, 0.95)
           FROM payments.payments WHERE auth_status = 'approved') AS p95_latency_h,
        (SELECT 100.0 * (SELECT count(*) FROM payments.chargebacks)
                      / (SELECT count(*) FROM payments.payments)) AS cb_ratio
    `);
    if (!r) return [];
    return [
      { label: "Total payments", value: fmt(r.total_payments) },
      { label: "STP rate", value: pct(r.stp_rate) },
      { label: "p95 settlement latency", value: `${num(r.p95_latency_h)?.toFixed(1) ?? "—"} h` },
      { label: "Chargeback ratio", value: pct(r.cb_ratio, 3) },
    ];
  },

  p_and_c_claims: async () => {
    const r = await queryOne<any>(`
      SELECT
        (SELECT count(*) FROM p_and_c_claims.claims WHERE status='open') AS claims_open,
        (SELECT avg(incurred_amount) FROM p_and_c_claims.claims) AS avg_incurred,
        (SELECT 100.0 * sum(case when severity in ('high','catastrophic') then 1 else 0 end) / count(*)
           FROM p_and_c_claims.claims) AS pct_serious,
        (SELECT sum(amount) FROM p_and_c_claims.claim_payments) AS total_paid
    `);
    if (!r) return [];
    return [
      { label: "Open claims", value: fmt(r.claims_open) },
      { label: "Avg incurred", value: dollars(r.avg_incurred) },
      { label: "High/catastrophic share", value: pct(r.pct_serious, 1) },
      { label: "Total paid (lifetime)", value: dollars(r.total_paid) },
    ];
  },

  merchandising: async () => {
    const r = await queryOne<any>(`
      SELECT
        (SELECT count(*) FROM merchandising.products) AS sku_count,
        (SELECT sum(extended_amount) FROM merchandising.sales_lines) AS revenue,
        (SELECT avg(extended_amount) FROM merchandising.sales_lines) AS avg_basket,
        (SELECT 100.0 * (SELECT count(*) FROM merchandising.returns)
                      / (SELECT count(*) FROM merchandising.sales_lines)) AS return_rate
    `);
    if (!r) return [];
    return [
      { label: "Active SKUs", value: fmt(r.sku_count) },
      { label: "Revenue (lifetime)", value: dollars(r.revenue) },
      { label: "Avg basket line", value: dollars(r.avg_basket, 2) },
      { label: "Return rate", value: pct(r.return_rate, 2) },
    ];
  },

  demand_planning: async () => {
    const r = await queryOne<any>(`
      SELECT
        (SELECT count(*) FROM demand_planning.forecasts) AS forecast_count,
        (SELECT avg(ape) FROM demand_planning.forecast_errors) AS mean_ape,
        (SELECT 100.0 * sum(case when on_time then 1 else 0 end) / count(*) FROM demand_planning.shipments) AS otd,
        (SELECT count(distinct location_id) FROM demand_planning.inventory_positions WHERE on_hand > 0) AS stocked_locations
    `);
    if (!r) return [];
    const ape = num(r.mean_ape);
    return [
      { label: "Active forecasts", value: fmt(r.forecast_count) },
      { label: "Mean APE", value: ape === null ? "—" : `${(ape * 100).toFixed(2)}%` },
      { label: "On-time delivery", value: pct(r.otd, 2) },
      { label: "Stocked locations", value: fmt(r.stocked_locations) },
    ];
  },

  hotel_revenue_management: async () => {
    const r = await queryOne<any>(`
      SELECT
        (SELECT avg(adr) FROM hotel_revenue_management.reservations) AS adr,
        (SELECT 100.0 * sum(sold) / nullif(sum(sold) + sum(available), 0)
           FROM hotel_revenue_management.daily_inventory) AS occupancy,
        (SELECT count(*) FROM hotel_revenue_management.reservations) AS reservations,
        (SELECT 100.0 * sum(case when status='cancelled' then 1 else 0 end) / count(*)
           FROM hotel_revenue_management.reservations) AS cancel_rate
    `);
    if (!r) return [];
    const adr = num(r.adr);
    return [
      { label: "ADR", value: adr === null ? "—" : `$${adr.toFixed(2)}` },
      { label: "Occupancy", value: pct(r.occupancy, 1) },
      { label: "Reservations", value: fmt(r.reservations) },
      { label: "Cancellation rate", value: pct(r.cancel_rate, 1) },
    ];
  },

  mes_quality: async () => {
    const r = await queryOne<any>(`
      SELECT
        (SELECT 100.0 * sum(qty_produced) / nullif(sum(qty_planned), 0) FROM mes_quality.work_orders) AS yield_pct,
        (SELECT count(*) FROM mes_quality.sensor_readings WHERE anomaly) AS anomalies,
        (SELECT avg(duration_minutes) FROM mes_quality.downtime_events) AS avg_downtime_min,
        (SELECT 100.0 * sum(case when result='fail' then 1 else 0 end) / count(*)
           FROM mes_quality.inspections) AS defect_rate
    `);
    if (!r) return [];
    const dt = num(r.avg_downtime_min);
    return [
      { label: "Yield", value: pct(r.yield_pct, 2) },
      { label: "Anomalous readings", value: fmt(r.anomalies) },
      { label: "Avg downtime per event", value: dt === null ? "—" : `${dt.toFixed(1)} min` },
      { label: "Inspection fail rate", value: pct(r.defect_rate, 2) },
    ];
  },

  pharmacovigilance: async () => {
    const r = await queryOne<any>(`
      SELECT
        (SELECT count(*) FROM pharmacovigilance.cases) AS cases,
        (SELECT 100.0 * sum(case when seriousness in ('serious','life_threatening','death') then 1 else 0 end) / count(*)
           FROM pharmacovigilance.cases) AS serious_share,
        (SELECT count(distinct country) FROM pharmacovigilance.cases) AS countries,
        (SELECT count(*) FROM pharmacovigilance.signals WHERE status='validated') AS validated_signals
    `);
    if (!r) return [];
    return [
      { label: "Cases", value: fmt(r.cases) },
      { label: "Serious share", value: pct(r.serious_share, 1) },
      { label: "Countries reported", value: fmt(r.countries) },
      { label: "Validated signals", value: fmt(r.validated_signals) },
    ];
  },
};

export async function getSnapshot(subdomainId: string): Promise<Stat[] | null> {
  const builder = BUILDERS[subdomainId];
  if (!builder) return null;
  try {
    return await builder();
  } catch (err) {
    console.error(`[snapshot:${subdomainId}]`, err);
    return null;
  }
}
