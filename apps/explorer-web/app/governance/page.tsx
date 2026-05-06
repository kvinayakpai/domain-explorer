import Link from "next/link";
import { ArrowRight, BookOpen, Database, GitBranch, ShieldCheck, Activity, Network } from "lucide-react";
import { registry } from "@/lib/registry";
import { loadDqReport } from "@/lib/dq";
import { loadKgSnapshot } from "@/lib/kg";
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
  description: "Catalog, glossary, lineage, KG, and DQ — the governance backbone of the registry.",
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
  const kg = loadKgSnapshot();
  return (
    <div className="space-y-8">
      <Breadcrumb items={[{ label: "Verticals", href: "/" }, { label: "Governance" }]} />
      <header className="space-y-2">
        <Badge>Governance</Badge>
        <h1 className="text-2xl font-bold tracking-tight md:text-3xl">Governance</h1>
        <p className="max-w-3xl text-muted-foreground">
          Catalog, glossary, lineage, knowledge graph, and DQ. Everything renders from the
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
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-5">
          <CardLink
            href="/catalog"
            title="Catalog"
            description="Searchable, filterable list of every entity from every subdomain - with owning persona and source links."
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
            description="Column-level lineage diagrams for all seven anchor subdomains - sources to vault to dimensional KPIs."
            icon={<GitBranch className="h-5 w-5" />}
            cta="View lineage"
          />
          <CardLink
            href="/dq"
            title="Data Quality"
            description="Real DQ rules executed against the populated DuckDB - pass/fail counts by severity, table, and subdomain."
            icon={<Activity className="h-5 w-5" />}
            cta="Open DQ dashboard"
          />
          <CardLink
            href="/kg"
            title="Knowledge Graph"
            description="The NetworkX-backed graph that grounds the assistant. Same shape powers /catalog, /lineage, and /assistant."
            icon={<Network className="h-5 w-5" />}
            cta="Explore the graph"
          />
        </div>
      </section>

      <section>
        <div className="mb-3 flex items-baseline justify-between">
          <h2 className="text-lg font-semibold">Data quality</h2>
          <span className="text-xs text-muted-foreground">
            {dqReport
              ? `${dqSource === "live" ? "Live API" : "Snapshot"} - ran ${dqReport.ran_at}`
              : "Service unavailable - run scripts/dq_snapshot.py"}
          </span>
        </div>
        {dqReport ? (
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
            <Metric label="Total rules" value={dqReport.total_rules} />
            <Metric
              label="Pass rate"
              value={`${(dqReport.pass_rate * 100).toFixed(1)}%`}
              hint={`${dqReport.passed} pass / ${dqReport.failed} fail`}
            />
            <Metric label="Failed" value={dqReport.failed} />
            <Metric label="Errored" value={dqReport.errored} />
            <Metric
              label="Critical fails"
              value={dqReport.by_severity?.critical?.failed ?? 0}
            />
            <Metric
              label="High fails"
              value={dqReport.by_severity?.high?.failed ?? 0}
            />
          </div>
        ) : (
          <div className="rounded-lg border border-amber-300/50 bg-amber-50/40 p-4 text-sm dark:bg-amber-950/20">
            FastAPI service is not reachable and no snapshot is committed yet. Run
            <code className="mx-1">python3 scripts/dq_snapshot.py</code> from the repo root to
            generate <code>data/quality/last_run.json</code>.
          </div>
        )}
        <p className="mt-3 inline-flex items-center gap-2 text-xs text-muted-foreground">
          <ShieldCheck className="h-3.5 w-3.5" />
          Rules from <code>data/quality/dq_rules.yaml</code>; runs against the populated DuckDB.
          {" "}
          <Link href="/dq" className="underline hover:text-foreground">
            Open the full DQ dashboard
          </Link>
        </p>
      </section>

      {kg && (
        <section>
          <h2 className="mb-3 text-lg font-semibold">Knowledge graph</h2>
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
            <Metric label="Total nodes" value={kg.stats.nodes.toLocaleString()} />
            <Metric label="Total edges" value={kg.stats.edges.toLocaleString()} />
            <Metric label="Subdomains" value={kg.stats.byKind.subdomain ?? 0} />
            <Metric label="Personas" value={kg.stats.byKind.persona ?? 0} />
            <Metric label="KPIs" value={kg.stats.byKind.kpi ?? 0} />
            <Metric label="Entities" value={kg.stats.byKind.entity ?? 0} />
          </div>
          <p className="mt-3 inline-flex items-center gap-2 text-xs text-muted-foreground">
            <Network className="h-3.5 w-3.5" />
            NetworkX-backed; rebuilt by <code>npm run kg:build</code> from the YAML registry.
            {" "}
            <Link href="/kg" className="underline hover:text-foreground">
              Open the graph
            </Link>
          </p>
        </section>
      )}
    </div>
  );
}
