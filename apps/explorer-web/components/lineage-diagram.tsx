import * as React from "react";
import type { LineageEdge, LineageGraph, LineageKind, LineageNode } from "@/lib/lineage-data";

const COLS = 6; // source · stage · vault hub · vault sat · mart · kpi
const COL_W = 200;
const ROW_H = 70;
const NODE_W = 168;
const NODE_H = 50;

const KIND_FILL: Record<LineageKind, string> = {
  source: "fill-sky-100 stroke-sky-400 dark:fill-sky-900/40 dark:stroke-sky-500",
  stage: "fill-violet-100 stroke-violet-400 dark:fill-violet-900/40 dark:stroke-violet-500",
  vault: "fill-amber-100 stroke-amber-400 dark:fill-amber-900/40 dark:stroke-amber-500",
  mart: "fill-emerald-100 stroke-emerald-400 dark:fill-emerald-900/40 dark:stroke-emerald-500",
  kpi: "fill-rose-100 stroke-rose-400 dark:fill-rose-900/40 dark:stroke-rose-500",
};

const COL_LABELS = [
  "Source systems",
  "Staging",
  "Vault hubs / links",
  "Vault satellites",
  "Marts (star)",
  "KPIs",
];

function nodePos(n: LineageNode) {
  return {
    x: 20 + n.layer * COL_W,
    y: 60 + n.row * ROW_H,
  };
}

function edgePath(a: LineageNode, b: LineageNode): string {
  const ap = nodePos(a);
  const bp = nodePos(b);
  const x1 = ap.x + NODE_W;
  const y1 = ap.y + NODE_H / 2;
  const x2 = bp.x;
  const y2 = bp.y + NODE_H / 2;
  const cx = (x1 + x2) / 2;
  return `M ${x1} ${y1} C ${cx} ${y1}, ${cx} ${y2}, ${x2} ${y2}`;
}

interface LineageDiagramProps {
  graph: LineageGraph;
  /** Optional ARIA label override. Defaults to "<title> column-level lineage". */
  ariaLabel?: string;
}

export function LineageDiagram({ graph, ariaLabel }: LineageDiagramProps) {
  const { nodes, edges } = graph;
  const maxRow = nodes.reduce((m, n) => Math.max(m, n.row), 0);
  const width = 20 + COL_W * COLS + NODE_W - COL_W + 20;
  const height = 60 + ROW_H * (maxRow + 1) + 40;
  const nodeMap = new Map(nodes.map((n) => [n.id, n] as const));
  return (
    <div className="overflow-x-auto rounded-lg border bg-card">
      <svg
        role="img"
        aria-label={ariaLabel ?? `${graph.title} column-level lineage`}
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
          {edges.map((e: LineageEdge, i) => {
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
        {nodes.map((n) => {
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

/**
 * Small SVG thumbnail of a lineage graph — six colored dots in a row, one per
 * layer, with the count of nodes in that layer rendered inside. Used by the
 * index page card.
 */
export function LineageThumbnail({ graph }: { graph: LineageGraph }) {
  const cols = [0, 1, 2, 3, 4, 5];
  const counts = cols.map((c) => graph.nodes.filter((n) => n.layer === c).length);
  const w = 240;
  const h = 60;
  const colW = w / cols.length;
  return (
    <svg
      viewBox={`0 0 ${w} ${h}`}
      role="img"
      aria-hidden="true"
      className="h-12 w-full"
    >
      <line
        x1={colW / 2}
        y1={h / 2}
        x2={w - colW / 2}
        y2={h / 2}
        className="stroke-muted-foreground/30"
        strokeWidth={1}
        strokeDasharray="2 3"
      />
      {cols.map((c, i) => {
        const cx = colW * (i + 0.5);
        const kind: LineageKind =
          c === 0 ? "source" : c === 1 ? "stage" : c <= 3 ? "vault" : c === 4 ? "mart" : "kpi";
        return (
          <g key={c}>
            <circle cx={cx} cy={h / 2} r={11} className={KIND_FILL[kind]} strokeWidth={1} />
            <text
              x={cx}
              y={h / 2 + 3}
              textAnchor="middle"
              className="fill-foreground text-[10px] font-semibold"
            >
              {counts[i]}
            </text>
          </g>
        );
      })}
    </svg>
  );
}
