import Link from "next/link";
import { ArrowRight } from "lucide-react";
import { Breadcrumb } from "@/components/ui/breadcrumb";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { LineageThumbnail } from "@/components/lineage-diagram";
import { ANCHOR_KEYS, anchorLineages, anchorSlugs } from "@/lib/lineage-data";

export const dynamic = "force-static";

export const metadata = {
  title: "Lineage · Domain Explorer",
  description:
    "Hand-curated column-level lineage diagrams for the seven anchor subdomains — sources to vault to dimensional KPIs.",
};

const LEGEND = [
  { kind: "source", label: "Source system", swatch: "bg-sky-200 dark:bg-sky-700" },
  { kind: "stage", label: "Staging view", swatch: "bg-violet-200 dark:bg-violet-700" },
  { kind: "vault", label: "Data Vault hub / link / sat", swatch: "bg-amber-200 dark:bg-amber-700" },
  { kind: "mart", label: "Star-schema mart", swatch: "bg-emerald-200 dark:bg-emerald-700" },
  { kind: "kpi", label: "KPI", swatch: "bg-rose-200 dark:bg-rose-700" },
];

export default function LineageIndexPage() {
  return (
    <div className="space-y-8">
      <Breadcrumb
        items={[
          { label: "Verticals", href: "/" },
          { label: "Governance", href: "/governance" },
          { label: "Lineage" },
        ]}
      />
      <header className="space-y-2">
        <h1 className="text-2xl font-bold tracking-tight md:text-3xl">Lineage diagrams</h1>
        <p className="max-w-3xl text-muted-foreground">
          Each anchor subdomain ships with a hand-curated, ~30-node column-level lineage
          diagram. Source systems flow through staging into Data Vault hubs / links / satellites,
          land in star-schema marts, and finally roll up to the KPIs that answer the decisions
          on each subdomain page. Pick an anchor to open its diagram.
        </p>
      </header>

      <div className="flex flex-wrap items-center gap-3 text-xs text-muted-foreground">
        {LEGEND.map((l) => (
          <span key={l.kind} className="inline-flex items-center gap-1.5">
            <span className={`inline-block h-3 w-3 rounded-sm ${l.swatch}`} />
            {l.label}
          </span>
        ))}
      </div>

      <section className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {ANCHOR_KEYS.map((key) => {
          const g = anchorLineages[key];
          return (
            <Link
              key={key}
              href={`/lineage/${anchorSlugs[key]}`}
              className="group focus-visible:outline-none"
            >
              <Card className="flex h-full flex-col transition-colors group-hover:bg-accent">
                <CardHeader className="pb-2">
                  <div className="flex items-center justify-between gap-2">
                    <CardTitle className="text-base">{g.title}</CardTitle>
                    <Badge className="text-[10px]">{g.vertical}</Badge>
                  </div>
                  <CardDescription className="line-clamp-3">{g.oneLiner}</CardDescription>
                </CardHeader>
                <CardContent className="flex flex-1 flex-col justify-end gap-3 pt-0">
                  <LineageThumbnail graph={g} />
                  <div className="flex items-center justify-between text-xs text-muted-foreground">
                    <span>
                      {g.nodes.length} nodes · {g.edges.length} edges
                    </span>
                    <span className="inline-flex items-center text-foreground">
                      View lineage <ArrowRight className="ml-1 h-3.5 w-3.5" />
                    </span>
                  </div>
                </CardContent>
              </Card>
            </Link>
          );
        })}
      </section>

      <section className="grid gap-4 md:grid-cols-2">
        <div className="rounded-lg border p-4">
          <h2 className="mb-2 text-sm font-semibold">What this is</h2>
          <p className="text-sm text-muted-foreground">
            Seven hand-curated lineage diagrams — one per anchor subdomain. Each follows the
            same six-column pattern (sources → staging → vault → marts → KPIs) and is backed
            by real source-system, DDL, and KPI names from the registry. Use the legend above
            to read any of them at a glance.
          </p>
        </div>
        <div className="rounded-lg border p-4">
          <h2 className="mb-2 text-sm font-semibold">Where to next</h2>
          <ul className="ml-4 list-disc space-y-1 text-sm text-muted-foreground">
            <li>
              <Link href="/catalog" className="hover:underline">
                Catalog
              </Link>{" "}
              — every entity from every subdomain&rsquo;s data model.
            </li>
            <li>
              <Link href="/glossary" className="hover:underline">
                Glossary
              </Link>{" "}
              — definitions for the KPIs and acronyms used in these diagrams.
            </li>
            <li>
              <Link href="/governance" className="hover:underline">
                Governance overview
              </Link>{" "}
              — DQ, KG, and the rest of the governance backbone.
            </li>
          </ul>
        </div>
      </section>
    </div>
  );
}
