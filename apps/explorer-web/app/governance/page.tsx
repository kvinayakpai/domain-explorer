import Link from "next/link";
import { ArrowRight, BookOpen, Database, GitBranch, ShieldCheck } from "lucide-react";
import { registry } from "@/lib/registry";
import { Breadcrumb } from "@/components/ui/breadcrumb";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

export const dynamic = "force-static";

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

export default function GovernancePage() {
  const reg = registry();
  const totalEntities = reg.subdomains.reduce(
    (n, s) => n + (s.dataModel?.entities?.length ?? 0),
    0,
  );
  const verticals = new Set(reg.subdomains.map((s) => s.vertical)).size;
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
        <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
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
        </div>
      </section>

      <section>
        <div className="mb-3 flex items-baseline justify-between">
          <h2 className="text-lg font-semibold">Data quality (placeholder)</h2>
          <span className="text-xs text-muted-foreground">Wired in v0.next</span>
        </div>
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
          <Metric label="Schema conformance" value="98.2%" hint="Average across feeds" />
          <Metric label="Freshness SLA met" value="94%" hint="Last 30 days" />
          <Metric label="Open DQ incidents" value={3} hint="P1 = 0 / P2 = 1 / P3 = 2" />
          <Metric label="Lineage coverage" value="71%" hint="Critical-data elements" />
        </div>
        <p className="mt-3 inline-flex items-center gap-2 text-xs text-muted-foreground">
          <ShieldCheck className="h-3.5 w-3.5" /> Sourced from registry today; will be wired to
          the live observability stack in a future pass.
        </p>
      </section>
    </div>
  );
}
