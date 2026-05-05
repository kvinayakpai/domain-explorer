import Link from "next/link";
import { Breadcrumb } from "@/components/ui/breadcrumb";
import { LineageDiagram } from "@/components/lineage-diagram";

export const dynamic = "force-static";

export const metadata = {
  title: "Lineage · Domain Explorer",
  description: "Column-level lineage walkthrough for the Payments anchor.",
};

const LEGEND = [
  { kind: "source", label: "Source system", swatch: "bg-sky-200 dark:bg-sky-700" },
  { kind: "stage", label: "Staging view", swatch: "bg-violet-200 dark:bg-violet-700" },
  { kind: "vault", label: "Data Vault hub / link / sat", swatch: "bg-amber-200 dark:bg-amber-700" },
  { kind: "mart", label: "Star-schema mart", swatch: "bg-emerald-200 dark:bg-emerald-700" },
  { kind: "kpi", label: "KPI", swatch: "bg-rose-200 dark:bg-rose-700" },
];

export default function LineagePage() {
  return (
    <div className="space-y-6">
      <Breadcrumb
        items={[
          { label: "Verticals", href: "/" },
          { label: "Governance", href: "/governance" },
          { label: "Lineage" },
        ]}
      />
      <header className="space-y-2">
        <h1 className="text-2xl font-bold tracking-tight md:text-3xl">Payments lineage</h1>
        <p className="max-w-3xl text-muted-foreground">
          End-to-end view from acquirer/core-banking source systems through staging, Data Vault,
          and dimensional marts to the KPIs they roll up to. The diagram below is generated from
          a static node/edge list — easy to extend as the dbt project grows.
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

      <LineageDiagram />

      <section className="grid gap-4 md:grid-cols-2">
        <div className="rounded-lg border p-4">
          <h2 className="mb-2 text-sm font-semibold">What this is</h2>
          <p className="text-sm text-muted-foreground">
            A hand-curated lineage anchored on the Payments subdomain — five source systems, ten
            staging views, vault hubs/links/sats, three fact and two dim marts, and five KPIs.
            Roughly thirty nodes, designed to scan left-to-right at desktop and scroll
            horizontally on mobile.
          </p>
        </div>
        <div className="rounded-lg border p-4">
          <h2 className="mb-2 text-sm font-semibold">Where to next</h2>
          <ul className="ml-4 list-disc space-y-1 text-sm text-muted-foreground">
            <li>
              <Link href="/d/payments" className="hover:underline">
                Payments subdomain page
              </Link>{" "}
              — personas, KPIs, source systems, sample queries.
            </li>
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
              — definitions for the KPIs and acronyms used here.
            </li>
          </ul>
        </div>
      </section>
    </div>
  );
}
