import Link from "next/link";
import { ArrowRight, BookOpen, Database, GitBranch, ShieldCheck, Activity } from "lucide-react";
import { registry } from "@/lib/registry";
import { loadDqReport } from "@/lib/dq";
import { Breadcrumb } from "@/components/ui/breadcrumb";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

// Render at request time so DQ tile reflects live API or latest snapshot.
export const dynamic = "force-dynamic";
export const revalidate = 0;

export const metadata = {
  title: "Governance · Domain Explorer",
  description: "Catalog, glossary, and lineage — the governance backbone of the registry.",
};

interface CardLinkProps {
  href: string;
  title: string;
  description: string;
  icon: React.ReactNode;
  cta: string;
}

function CardLink({ href, title, description, icon, cta }: CardLinkProps) {
  return (
    <Link href={href} className="group">
      <Card className="h-full transition-colors group-hover:bg-accent">
        <CardHeader>
          <div className="flex items-center gap-3">
            <span className="rounded-md border bg-background p-2 text-muted-foreground">
              {icon}
            </span>
            <CardTitle className="text-base">{title}</CardTitle>
          </div>
          <CardDescription>{description}</CardDescription>
        </CardHeader>
        <CardContent className="flex items-center justify-end text-sm text-muted-foreground">
          {cta} <ArrowRight className="ml-1 h-4 w-4" />
        </CardContent>
      </Card>
    </Link>
  );
}

interface MetricProps {
  label: string;
  value: string | number;
  hint?: string;
}

function Metric({ label, value, hint }: MetricProps) {
  return (
    <div className="rounded-lg border bg-card p-4">
      <div className="text-xs uppercase tracking-wide text-muted-foreground">{label}</div>
      <div className="mt-1 text-2xl font-semibold">{value}</div>
      {hint && <div className="mt-0.5 text-xs text-muted-foreground">{hint}</div>}
    </div>
  );
}

export default async function GovernancePage() {
  const reg = registry();
  const totalEntities = reg.subdomains.reduce(
    (n, s) => n + (s.dataModel?.entities?.length ?? 0),
    0,
  );
  const verticals = new Set(reg.subdomains.map((s) => s.vertical)).size;
  const { report: dqReport, source: dqSource } = await loadDqReport();
  return (
    <div className="space-y-8">
      <Breadcrumb items={[{ label: "Verticals", href: "/" }, { label: "Governance" }]} />
      <header className="space-y-2">
        <Badge>Governance</Badge>
        <h1 className="text-2xl font-bold tracking-tight md:text-3xl">Governance</h1>
        <p className="max-w-3xl text-muted-foreground">
          Catalog, glossary, and lineage views over the registry. Everything renders from the
          same typed YAML files that drive the explorer.
        </p>
      </header>

      <section>
        <h2 className="mb-3 text-lg font-semibold">By the numbers</h2>
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
          <Metric label="Subdomains" value={reg.subdomains.length} />
          <Metric label="Verticals" value={verticals} />
          <Metric label="Entities" value={totalEntities} hint="Across data models" />
          <Metric label="KPIs" value={reg.kpis.length} hint="Standalone registry" />
          <Metric label="Source systems" value={reg.sourceSystems.length} />
          <Metric label="Glossary terms" value={reg.glossary.length} />
        </div>
      </section>

      <section>
        <h2 className="mb-3 text-lg font-semibold">Pillars</h2>
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-4">
          <CardLink
            href="/catalog"
            title="Catalog"
            description="Searchable, filterable list of every entity from every subdomain — with owning persona and source links."
            icon={<Database className="h-5 w-5" />}
            cta="Browse the catalog"
          />
          <CardLink
            href="/glossary"
            title="Glossary"
            description="A-Z terms for KPIs, regulatory acronyms, and shared business vocabulary, cross-linked to subdomains."
            icon={<BookOpen className="h-5 w-5" />}
            cta="Open glossary"
          />
          <CardLink
            href="/lineage"
            title="Lineage"
            description="Column-level lineage walkthrough for the Payments anchor — sources to vault to dimensional KPIs."
            icon={<GitBranch className="h-5 w-5" />}
            cta="View lineage"
          />
          <CardLink
            href="/dq"
            title="Data Quality"
            description="Real DQ rules executed against the populated DuckDB — pass/fail counts by severity, table, and subdomain."
            icon={<Activity className="h-5 w-5" />}
            cta="Open DQ dashboard"
          />
        </div>
      </section>

      <section>
        <div className="mb-3 flex items-baseline justify-between">
          <h2 className="text-lg font-semibold">Data quality</h2>
          <span className="text-xs text-muted-foreground">
            {dqReport
              ? `${dqSource === "live" ? "Live API" : "Snapshot"} · ran ${dqReport.ran_at}`
              : "Service unavailable — run scripts/dq_snapshot.py"}
          </span>
        </div>
      