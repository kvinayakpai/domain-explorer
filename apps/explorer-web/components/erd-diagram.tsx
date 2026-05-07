import * as React from "react";
import type { ErdEntity, ErdGraph, ErdRelationship, ModelStyle } from "@/lib/erd-derive";

const CARD_W = 240;
const HEADER_H = 26;
const ROW_H = 16;
const COL_W = 300; // entity card + horizontal gap
const ROW_GAP = 24;
const PAD = 24;

interface PositionedEntity extends ErdEntity {
  col: number;
  row: number;
  x: number;
  y: number;
  height: number;
}

/**
 * Lay out entities left-to-right in columns based on a topological-ish
 * ordering: entities with no incoming edges go in column 0, then their
 * dependents in column 1, etc. Column count is capped so very wide diagrams
 * still wrap.
 */
function layout(graph: ErdGraph): { positioned: PositionedEntity[]; width: number; height: number } {
  const { entities, relationships } = graph;
  const incoming = new Map<string, number>();
  for (const e of entities) incoming.set(e.name, 0);
  for (const r of relationships) {
    if (incoming.has(r.to)) incoming.set(r.to, (incoming.get(r.to) ?? 0) + 1);
  }
  // Sort: low incoming first, then alphabetical for stability.
  const sorted = [...entities].sort((a, b) => {
    const ia = incoming.get(a.name) ?? 0;
    const ib = incoming.get(b.name) ?? 0;
    if (ia !== ib) return ia - ib;
    return a.name.localeCompare(b.name);
  });
  // Choose number of columns such that each column has ≤ 5 cards.
  const cols = Math.min(5, Math.max(2, Math.ceil(sorted.length / 5)));
  const colHeights = Array(cols).fill(0);
  const positioned: PositionedEntity[] = sorted.map((e, i) => {
    const col = i % cols;
    const row = Math.floor(i / cols);
    const height = HEADER_H + Math.max(1, e.attributes.length) * ROW_H + 8;
    const x = PAD + col * COL_W;
    const y = PAD + colHeights[col];
    colHeights[col] = colHeights[col] + height + ROW_GAP;
    return { ...e, col, row, x, y, height };
  });
  const width = PAD * 2 + cols * COL_W - (COL_W - CARD_W);
  const height = PAD * 2 + Math.max(...colHeights, 60);
  return { positioned, width, height };
}

interface AttrAnchor {
  entity: string;
  attr: string;
  side: "left" | "right";
  x: number;
  y: number;
}

function attrAnchor(p: PositionedEntity, attr: string, side: "left" | "right"): AttrAnchor {
  const idx = Math.max(0, p.attributes.findIndex((a) => a.name === attr));
  const x = side === "right" ? p.x + CARD_W : p.x;
  const y = p.y + HEADER_H + idx * ROW_H + ROW_H / 2;
  return { entity: p.name, attr, side, x, y };
}

function relPath(a: AttrAnchor, b: AttrAnchor): string {
  const dx = Math.max(40, Math.abs(b.x - a.x) / 2);
  const c1x = a.side === "right" ? a.x + dx : a.x - dx;
  const c2x = b.side === "right" ? b.x + dx : b.x - dx;
  return `M ${a.x} ${a.y} C ${c1x} ${a.y}, ${c2x} ${b.y}, ${b.x} ${b.y}`;
}

export interface ERDDiagramProps {
  graph: ErdGraph;
  style: ModelStyle;
  ariaLabel?: string;
}

export function ERDDiagram({ graph, style, ariaLabel }: ERDDiagramProps) {
  const { positioned, width, height } = layout(graph);
  const byName = new Map(positioned.map((p) => [p.name, p] as const));
  // For each relationship, find the FK column on the source entity and the PK on the target.
  const lines = graph.relationships
    .map((r: ErdRelationship, i: number) => {
      const from = byName.get(r.from);
      const to = byName.get(r.to);
      if (!from || !to) return null;
      const fkAttr = r.via ?? from.attributes.find((a) => a.isForeignKey && a.references?.startsWith(r.to))?.name;
      const pkAttr = to.attributes.find((a) => a.isPrimaryKey)?.name ?? to.attributes[0]?.name ?? "";
      if (!fkAttr) return null;
      const fromSide: "left" | "right" = from.x < to.x ? "right" : "left";
      const toSide: "left" | "right" = from.x < to.x ? "left" : "right";
      const a = attrAnchor(from, fkAttr, fromSide);
      const b = attrAnchor(to, pkAttr, toSide);
      return { id: `${r.from}.${fkAttr}->${r.to}.${pkAttr}-${i}`, a, b, kind: r.kind };
    })
    .filter((x): x is { id: string; a: AttrAnchor; b: AttrAnchor; kind: ErdRelationship["kind"] } => x !== null);
  const styleHints: Record<ModelStyle, string> = {
    "3nf": "fill-sky-50 stroke-sky-300 dark:fill-sky-900/30 dark:stroke-sky-600",
    vault: "fill-amber-50 stroke-amber-300 dark:fill-amber-900/30 dark:stroke-amber-600",
    dim: "fill-emerald-50 stroke-emerald-300 dark:fill-emerald-900/30 dark:stroke-emerald-600",
  };
  return (
    <div className="overflow-x-auto rounded-lg border bg-card">
      <svg
        role="img"
        aria-label={ariaLabel ?? `Entity-relationship diagram (${style})`}
        viewBox={`0 0 ${width} ${height}`}
        className="block w-full"
        style={{ minWidth: Math.min(width, 1100) }}
      >
        <defs>
          <marker
            id={`erd-arrow-${style}`}
            viewBox="0 0 10 10"
            refX="9"
            refY="5"
            markerWidth="8"
            markerHeight="8"
            orient="auto-start-reverse"
          >
            <path d="M 0 0 L 10 5 L 0 10 z" className="fill-muted-foreground" />
          </marker>
        </defs>
        <g className="stroke-muted-foreground/60" strokeWidth={1.2} fill="none">
          {lines.map((l) => (
            <path key={l.id} d={relPath(l.a, l.b)} markerEnd={`url(#erd-arrow-${style})`} />
          ))}
        </g>
        {positioned.map((p) => (
          <g key={p.name}>
            <rect
              x={p.x}
              y={p.y}
              width={CARD_W}
              height={p.height}
              rx={6}
              className={styleHints[style]}
              strokeWidth={1.2}
            />
            <rect
              x={p.x}
              y={p.y}
              width={CARD_W}
              height={HEADER_H}
              rx={6}
              className={styleHints[style] + " opacity-80"}
            />
            <text
              x={p.x + 10}
              y={p.y + HEADER_H - 8}
              className="fill-foreground text-[12px] font-semibold"
            >
              {p.name}
            </text>
            {p.attributes.map((a, i) => {
              const y = p.y + HEADER_H + i * ROW_H + ROW_H - 4;
              const flag = a.isPrimaryKey
                ? "PK"
                : a.isForeignKey
                  ? "FK"
                  : "";
              return (
                <g key={`${p.name}.${a.name}`}>
                  <text
                    x={p.x + 10}
                    y={y}
                    className={
                      a.isPrimaryKey
                        ? "fill-foreground text-[10px] font-bold"
                        : a.isForeignKey
                          ? "fill-foreground text-[10px] italic"
                          : "fill-foreground text-[10px]"
                    }
                  >
                    {flag ? `${flag} ` : ""}
                    {a.name}
                  </text>
                  <text
                    x={p.x + CARD_W - 10}
                    y={y}
                    textAnchor="end"
                    className="fill-muted-foreground text-[10px]"
                  >
                    {a.type}
                  </text>
                </g>
              );
            })}
          </g>
        ))}
      </svg>
    </div>
  );
}

export function ERDThumbnail({ entityCount, style }: { entityCount: number; style: ModelStyle }) {
  const cols = Math.min(4, Math.max(1, Math.ceil(entityCount / 3)));
  const rows = Math.min(3, Math.max(1, Math.ceil(entityCount / cols)));
  const w = 240;
  const h = 60;
  const cw = w / cols;
  const rh = h / rows;
  const fill =
    style === "vault"
      ? "fill-amber-200 stroke-amber-400 dark:fill-amber-900/60 dark:stroke-amber-500"
      : style === "dim"
        ? "fill-emerald-200 stroke-emerald-400 dark:fill-emerald-900/60 dark:stroke-emerald-500"
        : "fill-sky-200 stroke-sky-400 dark:fill-sky-900/60 dark:stroke-sky-500";
  const cards: React.ReactElement[] = [];
  for (let r = 0; r < rows; r++) {
    for (let c = 0; c < cols; c++) {
      cards.push(
        <rect
          key={`${r}-${c}`}
          x={c * cw + 4}
          y={r * rh + 4}
          width={cw - 8}
          height={rh - 8}
          rx={2}
          className={fill}
          strokeWidth={1}
        />,
      );
    }
  }
  return (
    <svg viewBox={`0 0 ${w} ${h}`} role="img" aria-hidden="true" className="h-12 w-full">
      {cards}
    </svg>
  );
}
