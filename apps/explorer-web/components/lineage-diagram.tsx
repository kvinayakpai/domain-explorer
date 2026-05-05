import * as React from "react";

interface Node {
  id: string;
  label: string;
  sub?: string;
  layer: number;
  row: number;
  kind: "source" | "stage" | "vault" | "mart" | "kpi";
}

interface Edge {
  from: string;
  to: string;
}

const COLS = 6; // source · stage · vault hub · vault sat · mart · kpi
const COL_W = 200;
const ROW_H = 70;
const NODE_W = 168;
const NODE_H = 50;

const KIND_FILL: Record<Node["kind"], string> = {
  source: "fill-sky-100 stroke-sky-400 dark:fill-sky-900/40 dark:stroke-sky-500",
  stage: "fill-violet-100 stroke-violet-400 dark:fill-violet-900/40 dark:stroke-violet-500",
  vault: "fill-amber-100 stroke-amber-400 dark:fill-amber-900/40 dark:stroke-amber-500",
  mart: "fill-emerald-100 stroke-emerald-400 dark:fill-emerald-900/40 dark:stroke-emerald-500",
  kpi: "fill-rose-100 stroke-rose-400 dark:fill-rose-900/40 dark:stroke-rose-500",
};

const NODES: Node[] = [
  // col 0 — source systems
  { id: "src.stripe", label: "Stripe", sub: "Acquirer/PSP", layer: 0, row: 0, kind: "source" },
  { id: "src.temenos", label: "Temenos Transact", sub: "Core Banking", layer: 0, row: 1, kind: "source" },
  { id: "src.fis", label: "FIS Profile", sub: "Core Banking", layer: 0, row: 2, kind: "source" },
  { id: "src.aci", label: "ACI EPS", sub: "Payments Hub", layer: 0, row: 3, kind: "source" },
  { id: "src.swift", label: "SWIFT Alliance", sub: "Messaging", layer: 0, row: 4, kind: "source" },
  // col 1 — staging
  { id: "stg.payments", label: "stg_payments__payments", sub: "view", layer: 1, row: 0, kind: "stage" },
  { id: "stg.settle", label: "stg_payments__settlements", sub: "view", layer: 1, row: 1, kind: "stage" },
  { id: "stg.cb", label: "stg_payments__chargebacks", sub: "view", layer: 1, row: 2, kind: "stage" },
  { id: "stg.cust", label: "stg_payments__customers", sub: "view", layer: 1, row: 3, kind: "stage" },
  { id: "stg.merch", label: "stg_payments__merchants", sub: "view", layer: 1, row: 4, kind: "stage" },
  // col 2 — vault hubs (left-side of vault column)
  { id: "vault.h_payment", label: "hub_payment", sub: "Vault hub", layer: 2, row: 0, kind: "vault" },
  { id: "vault.h_customer", label: "hub_customer", sub: "Vault hub", layer: 2, row: 1, kind: "vault" },
  { id: "vault.h_merchant", label: "hub_merchant", sub: "Vault hub", layer: 2, row: 2, kind: "vault" },
  { id: "vault.l_pc", label: "link_payment_customer", sub: "Vault link", layer: 2, row: 3, kind: "vault" },
  { id: "vault.l_pm", label: "link_payment_merchant", sub: "Vault link", layer: 2, row: 4, kind: "vault" },
  // col 3 — vault sats
  { id: "vault.s_payment", label: "sat_payment", sub: "Vault sat", layer: 3, row: 0, kind: "vault" },
  { id: "vault.s_settle", label: "sat_settlement", sub: "Vault sat", layer: 3, row: 1, kind: "vault" },
  { id: "vault.s_cb", label: "sat_chargeback", sub: "Vault sat", layer: 3, row: 2, kind: "vault" },
  { id: "vault.s_cust", label: "sat_customer", sub: "Vault sat", layer: 3, row: 3, kind: "vault" },
  { id: "vault.s_merch", label: "sat_merchant", sub: "Vault sat", layer: 3, row: 4, kind: "vault" },
  // col 4 — marts
  { id: "mart.fct_payments", label: "fct_payments", sub: "fact (table)", layer: 4, row: 0, kind: "mart" },
  { id: "mart.fct_settle", label: "fct_settlements", sub: "fact (table)", layer: 4, row: 1, kind: "mart" },
  { id: "mart.fct_cb", label: "fct_chargebacks", sub: "fact (table)", layer: 4, row: 2, kind: "mart" },
  { id: "mart.dim_cust", label: "dim_customer", sub: "dim (table)", layer: 4, row: 3, kind: "mart" },
  { id: "mart.dim_merch", label: "dim_merchant", sub: "dim (table)", layer: 4, row: 4, kind: "mart" },
  // col 5 — KPIs
  { id: "kpi.stp", label: "STP Rate", sub: "pay.kpi.stp_rate", layer: 5, row: 0, kind: "kpi" },
  { id: "kpi.lat", label: "Settlement Latency", sub: "pay.kpi.settlement_latency", layer: 5, row: 1, kind: "kpi" },
  { id: "kpi.cb", label: "Chargeback Ratio", sub: "pay.kpi.chargeback_ratio", layer: 5, row: 2, kind: "kpi" },
  { id: "kpi.afr", label: "Auth Failure Rate", sub: "pay.kpi.afr", layer: 5, row: 3, kind: "kpi" },
  { id: "kpi.ic", label: "Interchange Revenue", sub: "pay.kpi.interchange_revenue", layer: 5, row: 4, kind: "kpi" },
];

const EDGES: Edge[] = [
  // sources -> staging
  { from: "src.stripe", to: "stg.payments" },
  { from: "src.aci", to: "stg.payments" },
  { from: "src.aci", to: "stg.settle" },
  { from: "src.swift", to: "stg.settle" },
  { from: "src.temenos", to: "stg.cb" },
  { from: "src.fis", to: "stg.cust" },
  { from: "src.temenos", to: "stg.cust" },
  { from: "src.stripe", to: "stg.merch" },
  // staging -> vault
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
  // vault -> marts
  { from: "vault.s_payment", to: "mart.fct_payments" },
  { from: "vault.l_pc", to: "mart.fct_payments" },
  { from: "vault.l_pm", to: "mart.fct_payments" },
  { from: "vault.s_settle", to: "mart.fct_settle" },
  { from: "vault.s_cb", to: "mart.fct_cb" },
  { from: "vault.s_cust", to: "mart.dim_cust" },
  { from: "vault.s_merch", to: "mart.dim_merch" },
  // marts -> KPIs
  { from: "mart.fct_payments", to: "kpi.stp" },
  { from: "mart.fct_payments", to: "kpi.afr" },
  { from: "mart.fct_settle", to: "kpi.lat" },
  { from: "mart.fct_cb", to: "kpi.cb" },
  { from: "mart.fct_payments", to: "kpi.ic" },
];

function nodePos(n: Node) {
  return {
    x: 20 + n.layer * COL_W,
    y: 60 + n.row * ROW_H,
  };
}

function edgePath(a: Node, b: Node): string {
  const ap = nodePos(a);
  const bp = nodePos(b);
  const x1 = ap.x + NODE_W;
  const y1 = ap.y + NODE_H / 2;
  const x2 = bp.x;
  const y2 = bp.y + NODE_H / 2;
  const cx = (x1 + x2) / 2;
  return `M ${x1} ${y1} C ${cx} ${y1}, ${cx} ${y2}, ${x2} ${y2}`;
}

const COL_LABELS = [
  "Source systems",
  "Staging",
  "Vault hubs / links",
  "Vault satellites",
  "Marts (star)",
  "KPIs",
];

export function LineageDiagram() {
  const width = 20 + COL_W * COLS + NODE_W - COL_W + 20;
  const height = 60 + ROW_H * 5 + 40;
  const nodeMap = new Map(NODES.map((n) => [n.id, n] as const));
  return (
    <div className="overflow-x-auto rounded-lg border bg-card">
      <svg
        role="img"
        aria-label="Payments column-level lineage"
        viewBox={`0 0 ${width} ${height}`}
        className="block min-w-[1100px] w-full"
      >
        <defs>
          <marker
            id="arrow"
            viewBox="0 0 10 10"
            refX="8"
            refY="5"
            markerWidth="6"
            markerHeight="6"
            orient="auto-start-reverse"
          >
            <path d="M 0 0 L 10 5 L 0 10 z" className="fill-muted-foreground" />
          </marker>
        </defs>
        {COL_LABELS.map((label, i) => (
          <text
            key={label}
            x={20 + i * COL_W + NODE_W / 2}
            y={32}
            textAnchor="middle"
            className="fill-muted-foreground text-[11px] font-semibold uppercase tracking-wide"
          >
            {label}
          </text>
        ))}
        <g className="stroke-muted-foreground/50" strokeWidth={1.2} fill="none">
          {EDGES.map((e, i) => {
            const a = nodeMap.get(e.from);
            const b = nodeMap.get(e.to);
            if (!a || !b) return null;
            return (
              <path
                key={`${e.from}->${e.to}-${i}`}
                d={edgePath(a, b)}
                markerEnd="url(#arrow)"
                opacity={0.9}
              />
            );
          })}
        </g>
        {NODES.map((n) => {
          const p = nodePos(n);
          return (
            <g key={n.id}>
              <rect
                x={p.x}
                y={p.y}
                width={NODE_W}
                height={NODE_H}
                rx={6}
                className={KIND_FILL[n.kind]}
                strokeWidth={1}
              />
              <text
                x={p.x + 10}
                y={p.y + 20}
                className="fill-foreground text-[12px] font-medium"
              >
                {n.label}
              </text>
              {n.sub && (
                <text
                  x={p.x + 10}
                  y={p.y + 36}
                  className="fill-muted-foreground text-[10px]"
                >
                  {n.sub}
                </text>
              )}
            </g>
          );
        })}
      </svg>
    </div>
  );
}
