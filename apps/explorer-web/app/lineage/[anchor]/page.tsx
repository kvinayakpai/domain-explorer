import Link from "next/link";
import { notFound } from "next/navigation";
import { ArrowLeft } from "lucide-react";
import { Breadcrumb } from "@/components/ui/breadcrumb";
import { Badge } from "@/components/ui/badge";
import { LineageDiagram } from "@/components/lineage-diagram";
import {
  ANCHOR_KEYS,
  anchorLineages,
  anchorSlugs,
  type AnchorKey,
} from "@/lib/lineage-data";

export const dynamic = "force-static";

export function generateStaticParams() {
  return ANCHOR_KEYS.map((key) => ({ anchor: anchorSlugs[key] }));
}

const LEGEND = [
  { kind: "source", label: "Source system", swatch: "bg-sky-200 dark:bg-sky-700" },
  { kind: "stage", label: "Staging view", swatch: "bg-violet-200 dark:bg-violet-700" },
  { kind: "vault", label: "Data Vault hub / link / sat", swatch: "bg-amber-200 dark:bg-amber-700" },
  { kind: "mart", label: "Star-schema mart", swatch: "bg-emerald-200 dark:bg-emerald-700" },
  { kind: "kpi", label: "KPI", swatch: "bg-rose-200 dark:bg-rose-700" },
];

function resolveAnchor(slug: string): AnchorKey | null {
  for (const key of ANCHOR_KEYS) {
    if (anchorSlugs[key] === slug) return key;
  }
  return null;
}

export function generateMetadata({ params }: { params: { anchor: string } }) {
  const key = resolveAnchor(params.anchor);
  if (!key) return { title: "Lineage · Domain Explorer" };
  const g = anchorLineages[key];
  return {
    title: `${g.title} lineage · Domain Explorer`,
    description: `${g.title} column-level lineage — ${g.nodes.length} nodes from sources through Data Vault to KPIs.`,
  };
}

export default function AnchorLineagePage({ params }: { params: { anchor: string } }) {
  const key = resolveAnchor(params.anchor);
  if (!key) notFound();
  const graph = anchorLineages[key];

  // Layer counts for the inline summary.
  const counts = [0, 1, 2, 3, 4, 5].map(
    (c) => graph.nodes.filter((n) => n.layer === c).length,
  );

  return (
    <div className="space-y-6">
      <Breadcrumb
        items={[
          { label: "Verticals", href: "/" },
          { label: "Governance", href: "/governance" },
          { label: "Lineage", href: "/lineage" },
          { label: graph.title },
        ]}
      />
      <header className="space-y-2">
        <div className="flex flex-wrap items-center gap-2">
          <h1 className="text-2xl font-bold tracking-tight md:text-3xl">
            {graph.title} lineage
          </h1>
          <Badge className="text-[10px]">{graph.vertical}</Badge>
        </div>
        <p className="max-w-3xl text-muted-foreground">{graph.oneLiner}</p>
      </header>

      <div className="flex flex-wrap items-center gap-3 text-xs text-muted-foreground">
        {LEGEND.map((l) => (
          <span key={l.kind} className="inline-flex items-center gap-1.5">
            <span className={`inline-block h-3 w-3 rounded-sm ${l.swatch}`} />
            {l.label}
          </span>
        ))}
      </div>

      <LineageDiagram graph={graph} />

      <section className="grid gap-4 md:grid-cols-2">
        <div className="rounded-lg border p-4">
          <h2 className="mb-2 text-sm font-semibold">By the numbers</h2>
          <p className="text-sm text-muted-foreground">
            {graph.nodes.length} nodes and {graph.edges.length} edges across six layers:{" "}
            {counts[0]} source systems, {counts[1]} staging views, {(counts[2] ?? 0) + (counts[3] ?? 0)}{" "}
            vault objects, {counts[4]} marts, and {counts[5]} KPIs. Names are pulled from the
            anchor&rsquo;s YAML and the corresponding DDL files in{" "}
            <code className="rounded bg-muted px-1 py-0.5 text-xs">modeling/ddl/</code>.
          </p>
        </div>
        <div className="rounded-lg border p-4">
          <h2 className="mb-2 text-sm font-semibold">Where to next</h2>
          <ul className="ml-4 list-disc space-y-1 text-sm text-muted-foreground">
            <li>
              <Link
                href={`/d/${anchorSlugs[key]}`}
                className="hover:underline"
              >
                {graph.title} subdomain page
              </Link>{" "}
              — personas, KPIs, source systems, sample queries.
            </li>
            <li>
              <Link href="/lineage" className="hover:underline">
                All lineage diagrams
              </Link>{" "}
              — pick another anchor.
            </li>
            <li>
              <Link href="/catalog" className="hover:underline">
                Catalog
              </Link>{" "}
              — every entity from every subdomain&rsquo;s data model.
            </li>
          </ul>
        </div>
      </section>

      <div className="pt-2">
        <Link
          href="/lineage"
          className="inline-flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground"
        >
          <ArrowLeft className="h-3.5 w-3.5" />
          Back to lineage index
        </Link>
      </div>
    </div>
  );
}
