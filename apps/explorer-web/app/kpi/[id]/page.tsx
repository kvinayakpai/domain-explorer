import Link from "next/link";
import { notFound } from "next/navigation";
import { registry } from "@/lib/registry";
import { getKpiMaster, getKpiSql } from "@domain-explorer/metadata";
import { Breadcrumb } from "@/components/ui/breadcrumb";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { KpiRunner } from "@/components/kpi-runner";

export function generateStaticParams() {
  const ids = new Set<string>();
  const reg = registry();
  reg.kpis.forEach((k) => ids.add(k.id));
  reg.subdomains.forEach((s) => s.kpis.forEach((k) => ids.add(k.id)));
  reg.kpiMaster.forEach((k) => ids.add(k.id));
  return Array.from(ids).map((id) => ({ id }));
}

export default function KpiPage({ params }: { params: { id: string } }) {
  const reg = registry();
  const fromMaster = getKpiMaster(reg, params.id);
  const fromRegistry = reg.kpis.find((k) => k.id === params.id);
  const fromSubdomain = reg.subdomains
    .flatMap((s) => s.kpis)
    .find((k) => k.id === params.id);
  const k = fromMaster ?? fromRegistry ?? fromSubdomain;
  if (!k) notFound();
  const owningSubs = reg.subdomains.filter((s) =>
    s.kpis.some((x) => x.id === k.id),
  );
  const sql = getKpiSql(reg, params.id);
  const hasReal = (s?: string) =>
    !!s && !s.trim().startsWith("--") && !/TODO/i.test(s);
  const runnable =
    sql && (hasReal(sql.threeNF) || hasReal(sql.vault) || hasReal(sql.dimensional));
  return (
    <div className="space-y-6">
      <Breadcrumb
        items={[
          { label: "Verticals", href: "/" },
          { label: "KPI library", href: "/kpi-library" },
          { label: k.name },
        ]}
      />
      <header className="space-y-2">
        <h1 className="text-2xl font-bold tracking-tight md:text-3xl">{k.name}</h1>
        <p className="font-mono text-xs text-muted-foreground">{k.id}</p>
        <div className="flex flex-wrap gap-2">
          <Badge>{k.unit}</Badge>
          <Badge>{k.direction.replace(/_/g, " ")}</Badge>
          {"vertical" in k && k.vertical ? (
            <Badge>{String((k as { vertical?: string }).vertical)}</Badge>
          ) : null}
          {owningSubs.map((s) => (
            <Badge key={s.id}>{s.name}</Badge>
          ))}
        </div>
        {fromMaster?.definition ? (
          <p className="max-w-3xl text-sm text-muted-foreground">
            {fromMaster.definition}
          </p>
        ) : null}
      </header>
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Formula</CardTitle>
        </CardHeader>
        <CardContent>
          <pre className="overflow-x-auto rounded-md bg-muted p-3 text-sm">
            <code>{k.formula}</code>
          </pre>
        </CardContent>
      </Card>
      {sql ? (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">SQL implementations</CardTitle>
            <p className="text-xs text-muted-foreground">
              Same KPI, computed three ways depending on the modeling style of
              the warehouse.
            </p>
          </CardHeader>
          <CardContent className="space-y-4">
            {(
              [
                ["3NF (operational)", sql.threeNF, "3nf"],
                ["Data Vault 2.0", sql.vault, "vault"],
                ["Dimensional (star)", sql.dimensional, "dim"],
              ] as const
            ).map(([label, body, style]) => (
              <div key={label} className="space-y-1.5">
                <div className="flex items-center justify-between">
                  <h3 className="text-sm font-semibold">{label}</h3>
                  {body && hasReal(body) ? (
                    <Badge>real</Badge>
                  ) : body ? (
                    <Badge>stub</Badge>
                  ) : (
                    <Badge>—</Badge>
                  )}
                </div>
                <pre className="max-h-72 overflow-auto rounded-md bg-muted p-3 text-xs">
                  <code>{body?.trim() || "-- no SQL provided"}</code>
                </pre>
              </div>
            ))}
            {runnable ? (
              <KpiRunner kpiId={k.id} />
            ) : (
              <p className="text-xs text-muted-foreground">
                No live runner — only the 7 anchor subdomain KPIs have
                executable SQL against the populated DuckDB.
              </p>
            )}
          </CardContent>
        </Card>
      ) : null}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Decisions supported</CardTitle>
        </CardHeader>
        <CardContent className="text-sm">
          {k.decisionsSupported && k.decisionsSupported.length > 0 ? (
            <ul className="list-disc space-y-1 pl-6">
              {k.decisionsSupported.map((d) => (
                <li key={d}>
                  <code className="font-mono text-xs">{d}</code>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-muted-foreground">None mapped yet.</p>
          )}
        </CardContent>
      </Card>
      {owningSubs.length > 0 ? (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Used in subdomains</CardTitle>
          </CardHeader>
          <CardContent className="text-sm">
            <ul className="space-y-1">
              {owningSubs.map((s) => (
                <li key={s.id}>
                  <Link className="underline" href={`/d/${s.id}`}>
                    {s.name}
                  </Link>{" "}
                  <span className="text-xs text-muted-foreground">
                    · <Link className="underline" href={`/models/${s.id}/3nf`}>
                      view ERD
                    </Link>
                  </span>
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>
      ) : null}
      {fromMaster?.related_personas?.length ? (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Related personas</CardTitle>
          </CardHeader>
          <CardContent className="text-sm">
            <ul className="list-disc space-y-1 pl-6">
              {fromMaster.related_personas.map((p) => (
                <li key={p}>{p}</li>
              ))}
            </ul>
          </CardContent>
        </Card>
      ) : null}
    </div>
  );
}
