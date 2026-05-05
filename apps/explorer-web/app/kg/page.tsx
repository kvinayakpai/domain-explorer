import Link from "next/link";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { loadKgSnapshot, subgraphForVertical, type KgSnapshot } from "@/lib/kg";
import { VERTICALS } from "@/lib/registry";
import { KgGraphView } from "@/components/kg-graph-view";

interface PageProps {
  searchParams: { v?: string; n?: string };
}

export default function KgPage({ searchParams }: PageProps) {
  const snap = loadKgSnapshot();
  if (!snap) {
    return (
      <div className="space-y-4">
        <h1 className="text-2xl font-semibold tracking-tight">Knowledge Graph</h1>
        <p className="text-sm text-muted-foreground">
          The graph snapshot has not been built yet. Run{" "}
          <code className="rounded bg-muted px-1.5 py-0.5">npm run kg:build</code> to
          regenerate <code>kg/graph.json</code>.
        </p>
      </div>
    );
  }
  const verticalSlug = searchParams.v ?? "BFSI";
  const sub = subgraphForVertical(snap, verticalSlug, 50);
  const focusedNodeId = searchParams.n;

  // Top-level stats.
  const byKind = snap.stats.byKind;
  const kindBadges: { kind: string; count: number }[] = Object.entries(byKind)
    .sort((a, b) => b[1] - a[1])
    .map(([k, n]) => ({ kind: k, count: n }));

  return (
    <div className="space-y-6">
      <header className="space-y-2">
        <div className="flex flex-wrap items-baseline justify-between gap-3">
          <div>
            <h1 className="text-2xl font-semibold tracking-tight">Knowledge Graph</h1>
            <p className="text-sm text-muted-foreground">
              The same graph the assistant uses to ground every answer. Built from the
              YAML registry by <code>kg/build_graph.py</code>; persisted as a NetworkX
              MultiDiGraph and a JSON snapshot.
            </p>
          </div>
          <div className="flex flex-wrap gap-1.5">
            <Badge variant="secondary">{snap.stats.nodes.toLocaleString()} nodes</Badge>
            <Badge variant="secondary">{snap.stats.edges.toLocaleString()} edges</Badge>
            <Badge variant="secondary">schema v{snap.schemaVersion}</Badge>
          </div>
        </div>
        <div className="flex flex-wrap items-center gap-1">
          <span className="text-xs text-muted-foreground mr-1">Filter by vertical:</span>
          {VERTICALS.map((v) => (
            <Link
              key={v.slug}
              href={`/kg?v=${v.slug}`}
              className={
                "rounded-md border px-2 py-0.5 text-xs hover:bg-accent" +
                (verticalSlug === v.slug ? " border-foreground bg-accent" : " border-transparent bg-muted")
              }
            >
              {v.slug}
            </Link>
          ))}
        </div>
      </header>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">
            Vertical: {VERTICALS.find((v) => v.slug === verticalSlug)?.label ?? verticalSlug}
            <span className="ml-2 text-xs text-muted-foreground">
              {sub.nodes.length} nodes / {sub.edges.length} edges
            </span>
          </CardTitle>
          <CardDescription>
            Force-directed layout precomputed at build time (no D3 in the browser).
            Click a node to load its 1-hop neighbourhood.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <KgGraphView snapshot={sub} fullSnapshot={snap} focusedNodeId={focusedNodeId} verticalSlug={verticalSlug} />
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Schema (node kinds)</CardTitle>
          <CardDescription>
            How the registry decomposes into typed nodes. Edges follow the openCypher
            templates under <code>kg/cypher/</code>.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-2 text-xs">
            {kindBadges.map(({ kind, count }) => (
              <span
                key={kind}
                className="rounded-md border bg-card px-2 py-1 font-mono"
              >
                <span className="text-muted-foreground">{kind}</span>{" "}
                <span className="font-semibold">{count.toLocaleString()}</span>
              </span>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

export const dynamic = "force-dynamic";

// Help TS narrow `searchParams` (kept inside the file for now).
export type _PageSnapshot = KgSnapshot;
