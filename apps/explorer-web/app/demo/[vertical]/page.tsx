import Link from "next/link";
import { notFound } from "next/navigation";
import {
  ArrowRight,
  ArrowLeft,
  Database,
  GitBranch,
  Layers,
  ListTree,
  Target,
  User,
  Cable,
} from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { LineageDiagram } from "@/components/lineage-diagram";
import {
  getDemoFlow,
  kpisWithLineage,
  listDemoFlows,
  painForHero,
  platformStack,
} from "@/lib/demo-flows";

interface PageProps {
  params: { vertical: string };
  searchParams: { screen?: string };
}

export function generateStaticParams() {
  return listDemoFlows().map((f) => ({ vertical: f.verticalSlug }));
}

export function generateMetadata({ params }: PageProps) {
  const flow = getDemoFlow(params.vertical);
  return {
    title: flow ? `Demo · ${flow.verticalLabel}` : "Demo",
    description: flow
      ? `${flow.verticalLabel} demo flow anchored on ${flow.hero.name}.`
      : undefined,
  };
}

export default function DemoFlowPage({ params, searchParams }: PageProps) {
  const flow = getDemoFlow(params.vertical);
  if (!flow) notFound();
  const screen = parseInt(searchParams.screen ?? "1", 10);
  const safeScreen = screen >= 1 && screen <= 3 ? screen : 1;

  const baseHref = `/demo/${flow.verticalSlug}`;
  const prevHref = safeScreen > 1 ? `${baseHref}?screen=${safeScreen - 1}` : "/demo";
  const nextHref =
    safeScreen < 3 ? `${baseHref}?screen=${safeScreen + 1}` : "/demo";
  const nextLabel = safeScreen < 3 ? "Continue" : "Back to all demos";

  return (
    <div className="space-y-6">
      <header className="space-y-2">
        <Link
          href="/demo"
          className="inline-flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground"
        >
          <ArrowLeft className="h-3 w-3" /> All demos
        </Link>
        <div className="flex flex-wrap items-baseline gap-2">
          <h1 className="text-2xl font-bold tracking-tight">
            {flow.verticalLabel} demo
          </h1>
          <Badge variant="secondary">Anchored on {flow.hero.name}</Badge>
          {flow.hasFullStack && (
            <Badge className="bg-emerald-100 text-emerald-900 dark:bg-emerald-900/30 dark:text-emerald-200">
              Full DDL + DuckDB
            </Badge>
          )}
        </div>
        <ProgressDots active={safeScreen} />
      </header>

      {safeScreen === 1 && <ScreenPersonaPain flow={flow} />}
      {safeScreen === 2 && <ScreenKpiAnswer flow={flow} />}
      {safeScreen === 3 && <ScreenPlatform flow={flow} />}

      <div className="flex items-center justify-between border-t pt-4">
        <Link
          href={prevHref}
          className="inline-flex items-center gap-1 rounded-md border bg-card px-3 py-1.5 text-sm hover:bg-accent"
        >
          <ArrowLeft className="h-4 w-4" />
          {safeScreen === 1 ? "Index" : "Back"}
        </Link>
        <Link
          href={nextHref}
          className="inline-flex items-center gap-1 rounded-md bg-primary px-3 py-1.5 text-sm font-medium text-primary-foreground hover:opacity-90"
        >
          {nextLabel} <ArrowRight className="h-4 w-4" />
        </Link>
      </div>
    </div>
  );
}

function ProgressDots({ active }: { active: number }) {
  return (
    <ol className="flex items-center gap-2 text-xs text-muted-foreground">
      {[
        { n: 1, label: "Persona pain" },
        { n: 2, label: "The answer" },
        { n: 3, label: "Platform stack" },
      ].map((s) => (
        <li
          key={s.n}
          className={
            "flex items-center gap-1 rounded-full border px-2 py-0.5 " +
            (active === s.n ? "border-foreground bg-accent text-foreground" : "")
          }
        >
          <span className="font-mono">{s.n}</span> {s.label}
        </li>
      ))}
    </ol>
  );
}

function ScreenPersonaPain({ flow }: { flow: ReturnType<typeof getDemoFlow> & object }) {
  const pain = painForHero(flow.hero);
  return (
    <section className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <User className="h-4 w-4" /> {`"I need to know X but my data is in 12 places."`}
          </CardTitle>
          <CardDescription>
            Anchor subdomain: <span className="font-medium text-foreground">{flow.hero.name}</span>
            {" — "}
            {flow.hero.oneLiner}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-2">
            {pain.map((row) => (
              <div key={row.persona.name} className="rounded-md border bg-card p-4">
                <div className="text-[10px] uppercase tracking-wide text-muted-foreground">
                  {row.persona.level}
                </div>
                <div className="text-base font-semibold">{row.persona.name}</div>
                <div className="text-xs text-muted-foreground">{row.persona.title}</div>
                <ul className="mt-3 space-y-1.5 text-sm">
                  {row.decisions.map((d) => (
                    <li key={d.id} className="flex gap-2">
                      <Target className="mt-0.5 h-3.5 w-3.5 flex-shrink-0 text-muted-foreground" />
                      <span>{d.statement}</span>
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </section>
  );
}

function ScreenKpiAnswer({ flow }: { flow: ReturnType<typeof getDemoFlow> & object }) {
  const rows = kpisWithLineage(flow.hero);
  const useLineageDiagram = flow.hero.id === "payments";
  return (
    <section className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <Target className="h-4 w-4" /> The answer: KPIs with traceable lineage
          </CardTitle>
          <CardDescription>
            Each KPI ties back to source systems through a known integration path. The
            registry stores the formula, unit, and direction; the KG ties it to entities and
            decisions.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-3 md:grid-cols-2">
            {rows.map(({ kpi, sources }) => (
              <div key={kpi.id} className="rounded-md border bg-card p-3">
                <div className="flex items-baseline justify-between">
                  <div className="font-semibold">{kpi.name}</div>
                  <code className="text-[10px] text-muted-foreground">{kpi.id}</code>
                </div>
                <div className="mt-1 text-xs text-muted-foreground">
                  <span className="font-mono">{kpi.formula}</span>
                  {" "}
                  <span>
                    [{kpi.unit}, {kpi.direction.replaceAll("_", " ")}]
                  </span>
                </div>
                <div className="mt-2 flex flex-wrap gap-1">
                  {sources.map((s) => (
                    <span
                      key={`${kpi.id}-${s.vendor}-${s.product}`}
                      className="rounded border bg-muted px-1.5 py-0.5 text-[10px]"
                    >
                      {s.vendor} {s.product}
                    </span>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
      {useLineageDiagram && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <GitBranch className="h-4 w-4" /> Column-level lineage (Payments anchor)
            </CardTitle>
            <CardDescription>
              The same lineage backbone you&apos;d see on <code>/lineage</code> — sources to
              dimensional model to KPIs.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <LineageDiagram />
          </CardContent>
        </Card>
      )}
    </section>
  );
}

function ScreenPlatform({ flow }: { flow: ReturnType<typeof getDemoFlow> & object }) {
  const stack = platformStack(flow.hero);
  return (
    <section className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <Layers className="h-4 w-4" /> The platform under it
          </CardTitle>
          <CardDescription>
            Sources to ingest, integrate, model, consume — with the connectors named for {flow.verticalLabel}.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-3 md:grid-cols-5">
            <Tier
              icon={<Database className="h-4 w-4" />}
              title="Sources"
              items={stack.sources.map((s) => `${s.vendor} ${s.product}`)}
            />
            <Tier
              icon={<Cable className="h-4 w-4" />}
              title="Ingest"
              items={stack.ingest}
            />
            <Tier
              icon={<ListTree className="h-4 w-4" />}
              title="Integrate"
              items={stack.integrate}
            />
            <Tier
              icon={<Layers className="h-4 w-4" />}
              title="Model"
              items={stack.model}
            />
            <Tier
              icon={<Target className="h-4 w-4" />}
              title="Consume"
              items={stack.consume}
            />
          </div>
        </CardContent>
      </Card>
    </section>
  );
}

function Tier({
  icon,
  title,
  items,
}: {
  icon: React.ReactNode;
  title: string;
  items: string[];
}) {
  return (
    <div className="rounded-md border bg-card p-3">
      <div className="mb-2 flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
        {icon} {title}
      </div>
      <ul className="space-y-1 text-xs">
        {items.length === 0 && <li className="text-muted-foreground">—</li>}
        {items.map((it) => (
          <li
            key={it}
            className="rounded border bg-muted/50 px-1.5 py-1 leading-snug"
          >
            {it}
          </li>
        ))}
      </ul>
    </div>
  );
}
