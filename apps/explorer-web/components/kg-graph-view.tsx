"use client";
import * as React from "react";
import Link from "next/link";
import type { KgSnapshot, KgNode, KgEdge } from "@/lib/kg";

const KIND_FILL: Record<string, { fill: string; stroke: string; ring: string }> = {
  vertical: {
    fill: "fill-indigo-200 dark:fill-indigo-900/60",
    stroke: "stroke-indigo-600 dark:stroke-indigo-400",
    ring: "ring-indigo-500",
  },
  subdomain: {
    fill: "fill-emerald-200 dark:fill-emerald-900/60",
    stroke: "stroke-emerald-600 dark:stroke-emerald-400",
    ring: "ring-emerald-500",
  },
  persona: {
    fill: "fill-sky-200 dark:fill-sky-900/60",
    stroke: "stroke-sky-600 dark:stroke-sky-400",
    ring: "ring-sky-500",
  },
  decision: {
    fill: "fill-amber-200 dark:fill-amber-900/60",
    stroke: "stroke-amber-600 dark:stroke-amber-400",
    ring: "ring-amber-500",
  },
  kpi: {
    fill: "fill-rose-200 dark:fill-rose-900/60",
    stroke: "stroke-rose-600 dark:stroke-rose-400",
    ring: "ring-rose-500",
  },
  entity: {
    fill: "fill-violet-200 dark:fill-violet-900/60",
    stroke: "stroke-violet-600 dark:stroke-violet-400",
    ring: "ring-violet-500",
  },
  source: {
    fill: "fill-teal-200 dark:fill-teal-900/60",
    stroke: "stroke-teal-600 dark:stroke-teal-400",
    ring: "ring-teal-500",
  },
  source_local: {
    fill: "fill-teal-100 dark:fill-teal-900/40",
    stroke: "stroke-teal-500 dark:stroke-teal-400",
    ring: "ring-teal-500",
  },
  connector: {
    fill: "fill-orange-200 dark:fill-orange-900/60",
    stroke: "stroke-orange-600 dark:stroke-orange-400",
    ring: "ring-orange-500",
  },
  connector_local: {
    fill: "fill-orange-100 dark:fill-orange-900/40",
    stroke: "stroke-orange-500 dark:stroke-orange-400",
    ring: "ring-orange-500",
  },
  term: {
    fill: "fill-slate-200 dark:fill-slate-800",
    stroke: "stroke-slate-500 dark:stroke-slate-400",
    ring: "ring-slate-500",
  },
};

const KIND_RADIUS: Record<string, number> = {
  vertical: 18,
  subdomain: 14,
  persona: 11,
  decision: 9,
  kpi: 10,
  entity: 8,
  source: 9,
  source_local: 7,
  connector: 9,
  connector_local: 7,
  term: 6,
};

interface Props {
  snapshot: KgSnapshot;
  fullSnapshot: KgSnapshot;
  focusedNodeId?: string;
  verticalSlug: string;
}

export function KgGraphView({ snapshot, fullSnapshot, focusedNodeId, verticalSlug }: Props) {
  const [hover, setHover] = React.useState<string | null>(null);

  const nodeMap = React.useMemo(
    () => new Map<string, KgNode>(snapshot.nodes.map((n) => [n.id, n])),
    [snapshot],
  );

  // Recentre the precomputed layout to fit the subgraph's actual bbox.
  const bbox = React.useMemo(() => {
    if (snapshot.nodes.length === 0) return { x0: 0, y0: 0, x1: 1000, y1: 700 };
    let x0 = Infinity,
      y0 = Infinity,
      x1 = -Infinity,
      y1 = -Infinity;
    for (const n of snapshot.nodes) {
      x0 = Math.min(x0, n.x);
      y0 = Math.min(y0, n.y);
      x1 = Math.max(x1, n.x);
      y1 = Math.max(y1, n.y);
    }
    return { x0, y0, x1, y1 };
  }, [snapshot]);

  const W = 1000;
  const H = 600;
  const padX = 40;
  const padY = 30;
  const sx = (W - 2 * padX) / Math.max(bbox.x1 - bbox.x0, 1);
  const sy = (H - 2 * padY) / Math.max(bbox.y1 - bbox.y0, 1);
  const scale = Math.min(sx, sy);
  const project = (n: KgNode) => ({
    x: padX + (n.x - bbox.x0) * scale,
    y: padY + (n.y - bbox.y0) * scale,
  });

  const focused = focusedNodeId ? nodeMap.get(focusedNodeId) : null;

  // Compute neighbours for the focused node (from the full snapshot).
  const neighbourhood = React.useMemo(() => {
    if (!focused) return null;
    const incident = fullSnapshot.edges.filter(
      (e) => e.source === focused.id || e.target === focused.id,
    );
    const seen = new Set<string>([focused.id]);
    const neighbours: KgNode[] = [];
    for (const e of incident) {
      const otherId = e.source === focused.id ? e.target : e.source;
      if (seen.has(otherId)) continue;
      seen.add(otherId);
      const n = fullSnapshot.nodes.find((x) => x.id === otherId);
      if (n) neighbours.push(n);
    }
    return { incident, neighbours };
  }, [focused, fullSnapshot]);

  return (
    <div className="grid gap-4 lg:grid-cols-[2fr,1fr]">
      <div className="overflow-x-auto rounded-md border bg-card">
        <svg
          viewBox={`0 0 ${W} ${H}`}
          role="img"
          aria-label="Knowledge graph subgraph"
          className="block w-full"
        >
          <defs>
            <marker
              id="kg-arrow"
              viewBox="0 0 10 10"
              refX="8"
              refY="5"
              markerWidth="5"
              markerHeight="5"
              orient="auto-start-reverse"
            >
              <path d="M 0 0 L 10 5 L 0 10 z" className="fill-muted-foreground/70" />
            </marker>
          </defs>
          <g className="stroke-muted-foreground/40" strokeWidth={0.7} fill="none">
            {snapshot.edges.map((e: KgEdge, i: number) => {
              const a = nodeMap.get(e.source);
              const b = nodeMap.get(e.target);
              if (!a || !b) return null;
              const ap = project(a);
              const bp = project(b);
              const isHi =
                hover && (hover === e.source || hover === e.target)
                  ? true
                  : focused && (e.source === focused.id || e.target === focused.id);
              return (
                <line
                  key={`e-${i}`}
                  x1={ap.x}
                  y1={ap.y}
                  x2={bp.x}
                  y2={bp.y}
                  className={
                    isHi
                      ? "stroke-foreground/70"
                      : "stroke-muted-foreground/40"
                  }
                  strokeWidth={isHi ? 1.4 : 0.7}
                  markerEnd="url(#kg-arrow)"
                />
              );
            })}
          </g>
          {snapshot.nodes.map((n) => {
            const p = project(n);
            const r = KIND_RADIUS[n.kind] ?? 7;
            const palette = KIND_FILL[n.kind] ?? KIND_FILL.term!;
            const isFocus = focused?.id === n.id;
            return (
              <Link
                key={n.id}
                href={`/kg?v=${verticalSlug}&n=${encodeURIComponent(n.id)}`}
                aria-label={`Focus ${n.label}`}
              >
                <g
                  onMouseEnter={() => setHover(n.id)}
                  onMouseLeave={() => setHover(null)}
                  className="cursor-pointer"
                >
                  <circle
                    cx={p.x}
                    cy={p.y}
                    r={r}
                    className={`${palette.fill} ${palette.stroke}`}
                    strokeWidth={isFocus ? 2.5 : 1.1}
                  />
                  {(isFocus || hover === n.id || n.kind === "subdomain" || n.kind === "vertical") && (
                    <text
                      x={p.x + r + 4}
                      y={p.y + 3}
                      className="fill-foreground text-[9.5px]"
                    >
                      {n.label}
                    </text>
                  )}
                </g>
              </Link>
            );
          })}
        </svg>
      </div>

      <aside className="space-y-3 text-sm">
        {focused ? (
          <div className="rounded-md border bg-card p-4">
            <div className="text-[10px] font-semibold uppercase tracking-wide text-muted-foreground">
              {focused.kind}
            </div>
            <div className="text-base font-semibold">{focused.label}</div>
            <div className="mt-1 break-all text-xs text-muted-foreground">{focused.id}</div>
            {neighbourhood && (
              <div className="mt-3">
                <div className="text-xs font-medium text-muted-foreground">
                  1-hop neighbourhood ({neighbourhood.neighbours.length})
                </div>
                <ul className="mt-1 max-h-72 space-y-1 overflow-y-auto pr-1 text-xs">
                  {neighbourhood.neighbours.map((nn) => (
                    <li key={nn.id} className="flex items-center justify-between gap-2">
                      <Link
                        href={`/kg?v=${verticalSlug}&n=${encodeURIComponent(nn.id)}`}
                        className="truncate hover:underline"
                      >
                        {nn.label}
                      </Link>
                      <span className="shrink-0 rounded bg-muted px-1.5 py-0.5 font-mono text-[10px] text-muted-foreground">
                        {nn.kind}
                      </span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        ) : (
          <div className="rounded-md border bg-card p-4 text-xs text-muted-foreground">
            <p className="font-medium text-foreground">Click a node to inspect it.</p>
            <p className="mt-2">
              Each node carries its kind, label, and registry id. The 1-hop neighbourhood
              is computed against the <em>full</em> graph (not just this filtered subgraph).
            </p>
          </div>
        )}

        <div className="rounded-md border bg-card p-4">
          <div className="text-xs font-medium text-muted-foreground">Legend</div>
          <div className="mt-2 grid grid-cols-2 gap-y-1 text-[11px]">
            {(
              [
                "vertical",
                "subdomain",
                "persona",
                "decision",
                "kpi",
                "entity",
                "source",
                "connector",
              ] as const
            ).map((k) => (
              <div key={k} className="flex items-center gap-1.5">
                <svg viewBox="-10 -10 20 20" className="h-3 w-3">
                  <circle r={6} className={`${KIND_FILL[k]?.fill} ${KIND_FILL[k]?.stroke}`} />
                </svg>
                <span>{k}</span>
              </div>
            ))}
          </div>
        </div>
      </aside>
    </div>
  );
}
