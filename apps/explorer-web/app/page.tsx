import Link from "next/link";
import {
  ArrowRight,
  Activity,
  BookOpen,
  Database,
  GitBranch,
  MessagesSquare,
  Network,
  PlayCircle,
} from "lucide-react";
import { registry, VERTICALS } from "@/lib/registry";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

const VERTICAL_TAGLINES: Record<string, string> = {
  BFSI: "Payments, cards, lending, capital markets, AML, treasury.",
  Insurance: "Underwriting, claims, policy admin, reinsurance, actuarial.",
  Retail: "Stores, ecommerce, pricing & promotions, returns, last-mile, dark stores.",
  RCG: "Pricing, supply chain, loyalty across consumer goods.",
  CPG: "Demand planning, trade promotion management, brand marketing, retail execution.",
  TTH: "Airlines, hotels, ride-share, rentals, ground ops.",
  Manufacturing: "Shop floor, MES, BOM, supply chain visibility.",
  LifeSciences: "Trials, pharmacovigilance, medical devices, supply chain.",
  Healthcare: "EHR, revenue cycle, telehealth, imaging, engagement.",
  Telecom: "Network ops, BSS/OSS, billing, churn, 5G slicing, QoE.",
  Media: "Ad tech, programmatic, content metadata, SaaS metrics.",
  Energy: "Grid, trading, EV charging, renewables, carbon accounting.",
  Utilities: "Smart metering, outages, gas, water, asset health.",
  PublicSector: "Benefits, court, tax, transit, emergency response.",
  HiTech: "FinOps, telemetry, marketplaces, EDA, DevRel, yield.",
  ProfessionalServices: "Time, billing, legal matters, audit, knowledge.",
  CrossCutting: "Agentic commerce and other horizontal patterns spanning verticals.",
};

export default function HomePage() {
  const reg = registry();
  const counts = new Map<string, number>();
  const kpiCounts = new Map<string, number>();
  for (const s of reg.subdomains) {
    counts.set(s.vertical, (counts.get(s.vertical) ?? 0) + 1);
    kpiCounts.set(s.vertical, (kpiCounts.get(s.vertical) ?? 0) + (s.kpis?.length ?? 0));
  }
  const totalKpis = reg.subdomains.reduce((n, s) => n + (s.kpis?.length ?? 0), 0);
  const totalEntities = reg.subdomains.reduce((n, s) => n + (s.dataModel?.entities?.length ?? 0), 0);

  return (
    <div className="space-y-10">
      {/* Hero band */}
      <section className="rounded-xl border bg-gradient-to-br from-accent/40 via-card to-card p-6 md:p-8">
        <div className="flex flex-wrap items-center gap-2">
          <Badge>Deep Domain Explorer</Badge>
          <Badge className="bg-emerald-100 text-emerald-900 dark:bg-emerald-900/30 dark:text-emerald-200">
            v0 preview
          </Badge>
        </div>
        <h1 className="mt-3 text-3xl font-bold tracking-tight md:text-4xl">
          {reg.subdomains.length}+ subdomains across {VERTICALS.length} industry verticals
        </h1>
        <p className="mt-2 max-w-3xl text-muted-foreground">
          KPIs to KGs to connectors — a typed YAML registry that powers personas, decisions,
          source systems, integration patterns, governance, and a real data-quality module
          executing rules against a populated DuckDB.
        </p>
        <div className="mt-4 grid grid-cols-2 gap-3 text-sm sm:grid-cols-4">
          <Stat label="Subdomains" value={reg.subdomains.length} />
          <Stat label="Verticals" value={VERTICALS.length} />
          <Stat label="KPIs" value={totalKpis} />
          <Stat label="Data entities" value={totalEntities} />
        </div>
      </section>

      {/* Verticals grid */}
      <section>
        <div className="mb-4 flex items-baseline justify-between">
          <h2 className="text-xl font-semibold">Verticals</h2>
          <span className="text-sm text-muted-foreground">
            {reg.subdomains.length} subdomains · {totalKpis} KPIs
          </span>
        </div>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {VERTICALS.map((v) => {
            const subCount = counts.get(v.slug) ?? 0;
            const kpiCount = kpiCounts.get(v.slug) ?? 0;
            const tagline = VERTICAL_TAGLINES[v.slug];
            return (
              <Link key={v.slug} href={`/v/${v.slug}`} className="group">
                <Card className="h-full transition-colors group-hover:bg-accent">
                  <CardHeader>
                    <div className="flex items-center justify-between">
                      <CardTitle className="text-base">{v.label}</CardTitle>
                      <Badge>{subCount}</Badge>
                    </div>
                    {tagline && (
                      <CardDescription className="line-clamp-2">{tagline}</CardDescription>
                    )}
                  </CardHeader>
                  <CardContent className="flex items-center justify-between text-sm text-muted-foreground">
                    <span className="tabular-nums">
                      {subCount} subdomain{subCount === 1 ? "" : "s"} · {kpiCount} KPIs
                    </span>
                    <ArrowRight className="ml-1 h-4 w-4 transition-transform group-hover:translate-x-0.5" />
                  </CardContent>
                </Card>
              </Link>
            );
          })}
        </div>
      </section>

      {/* Quick access */}
      <section>
        <div className="mb-4 flex items-baseline justify-between">
          <h2 className="text-xl font-semibold">Quick access</h2>
          <span className="text-sm text-muted-foreground">Jump straight into the explorer</span>
        </div>
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4">
          <QuickLink href="/assistant" icon={<MessagesSquare className="h-4 w-4" />} label="Assistant" hint="Conversational" />
          <QuickLink href="/catalog" icon={<Database className="h-4 w-4" />} label="Catalog" hint={`${totalEntities} entities`} />
          <QuickLink href="/glossary" icon={<BookOpen className="h-4 w-4" />} label="Glossary" hint="A–Z terms" />
          <QuickLink href="/lineage" icon={<GitBranch className="h-4 w-4" />} label="Lineage" hint="Payments anchor" />
          <QuickLink href="/dq" icon={<Activity className="h-4 w-4" />} label="Data Quality" hint="Live rules" />
          <QuickLink href="/kg" icon={<Network className="h-4 w-4" />} label="Knowledge Graph" hint="NetworkX-backed" />
          <QuickLink href="/demo" icon={<PlayCircle className="h-4 w-4" />} label="Demo flows" hint="12 verticals" />
        </div>
      </section>
    </div>
  );
}

function Stat({ label, value }: { label: string; value: number | string }) {
  return (
    <div className="rounded-lg border bg-background/60 p-3">
      <div className="text-xs uppercase tracking-wide text-muted-foreground">{label}</div>
      <div className="mt-0.5 text-xl font-semibold tabular-nums">{value}</div>
    </div>
  );
}

function QuickLink({
  href,
  icon,
  label,
  hint,
}: {
  href: string;
  icon: React.ReactNode;
  label: string;
  hint?: string;
}) {
  return (
    <Link
      href={href}
      className="group flex items-center gap-3 rounded-lg border bg-card px-3 py-2.5 transition-colors hover:bg-accent"
    >
      <span className="rounded-md border bg-background p-1.5 text-muted-foreground">{icon}</span>
      <span className="flex flex-col leading-tight">
        <span className="text-sm font-medium">{label}</span>
        {hint && <span className="text-xs text-muted-foreground">{hint}</span>}
      </span>
      <ArrowRight className="ml-auto h-4 w-4 text-muted-foreground transition-transform group-hover:translate-x-0.5" />
    </Link>
  );
}
