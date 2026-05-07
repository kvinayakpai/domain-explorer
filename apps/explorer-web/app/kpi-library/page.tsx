import Link from "next/link";
import { registry, VERTICALS } from "@/lib/registry";
import { Breadcrumb } from "@/components/ui/breadcrumb";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Table, THead, TBody, TR, TH, TD } from "@/components/ui/table";

export const dynamic = "force-static";

interface MergedKpi {
  id: string;
  name: string;
  formula: string;
  unit: string;
  direction: string;
  vertical?: string;
  subdomains: string[];
  hasMaster: boolean;
  hasSql: boolean;
  definition?: string;
}

export default function KpiLibrary() {
  const reg = registry();
  // Merge: master entries are canonical; subdomain.kpis fill in the long tail.
  const byId = new Map<string, MergedKpi>();
  for (const k of reg.kpiMaster) {
    byId.set(k.id, {
      id: k.id,
      name: k.name,
      formula: k.formula,
      unit: k.unit,
      direction: k.direction,
      vertical: k.vertical,
      subdomains: k.subdomains ?? [],
      hasMaster: true,
      hasSql: false,
      definition: k.definition,
    });
  }
  for (const s of reg.subdomains) {
    for (const k of s.kpis) {
      const existing = byId.get(k.id);
      if (existing) {
        if (!existing.subdomains.includes(s.id)) existing.subdomains.push(s.id);
        if (!existing.vertical) existing.vertical = s.vertical;
      } else {
        byId.set(k.id, {
          id: k.id,
          name: k.name,
          formula: k.formula,
          unit: k.unit,
          direction: k.direction,
          vertical: s.vertical,
          subdomains: [s.id],
          hasMaster: false,
          hasSql: false,
        });
      }
    }
  }
  const sqlIds = new Set(
    reg.kpiSql
      .filter((s) => {
        const real = (q?: string) => q && !q.trim().startsWith("--") && !/TODO/i.test(q);
        return real(s.threeNF) || real(s.vault) || real(s.dimensional);
      })
      .map((s) => s.kpi_id),
  );
  for (const m of byId.values()) m.hasSql = sqlIds.has(m.id);
  const all = Array.from(byId.values()).sort((a, b) =>
    a.name.localeCompare(b.name),
  );
  const byVertical = new Map<string, MergedKpi[]>();
  for (const v of VERTICALS) byVertical.set(v.slug, []);
  for (const k of all) {
    if (!k.vertical) continue;
    byVertical.get(k.vertical)?.push(k);
  }
  return (
    <div className="space-y-6">
      <Breadcrumb items={[{ label: "Verticals", href: "/" }, { label: "KPI library" }]} />
      <header className="space-y-2">
        <h1 className="text-2xl font-bold tracking-tight md:text-3xl">KPI library</h1>
        <p className="max-w-3xl text-muted-foreground">
          Canonical, deduplicated catalog of every KPI surfaced across the
          taxonomy. Master entries carry definitions, related personas, and
          per-style SQL implementations; subdomain-only KPIs are still listed
          here so the long tail is searchable.
        </p>
        <div className="flex flex-wrap gap-2 pt-2">
          <Badge>{all.length} total KPIs</Badge>
          <Badge>{reg.kpiMaster.length} curated</Badge>
          <Badge>{sqlIds.size} runnable</Badge>
        </div>
      </header>
      {VERTICALS.filter((v) => (byVertical.get(v.slug) ?? []).length > 0).map(
        (v) => {
          const list = byVertical.get(v.slug) ?? [];
          return (
            <section key={v.slug} className="space-y-3">
              <h2 className="text-lg font-semibold">
                {v.label}{" "}
                <span className="text-sm font-normal text-muted-foreground">
                  ({list.length})
                </span>
              </h2>
              <Card>
                <CardContent className="p-0">
                  <Table>
                    <THead>
                      <TR>
                        <TH>Name</TH>
                        <TH>Formula</TH>
                        <TH>Unit</TH>
                        <TH>Direction</TH>
                        <TH>Subdomains</TH>
                        <TH>Status</TH>
                      </TR>
                    </THead>
                    <TBody>
                      {list.map((k) => (
                        <TR key={k.id}>
                          <TD>
                            <Link
                              className="font-medium hover:underline"
                              href={`/kpi/${k.id}`}
                            >
                              {k.name}
                            </Link>
                            <div className="font-mono text-[10px] text-muted-foreground">
                              {k.id}
                            </div>
                          </TD>
                          <TD className="font-mono text-xs">{k.formula}</TD>
                          <TD>{k.unit}</TD>
                          <TD>{k.direction.replace(/_/g, " ")}</TD>
                          <TD className="text-xs">
                            {k.subdomains.slice(0, 3).map((sid, i) => (
                              <span key={sid}>
                                {i > 0 ? ", " : ""}
                                <Link className="underline" href={`/d/${sid}`}>
                                  {sid}
                                </Link>
                              </span>
                            ))}
                            {k.subdomains.length > 3
                              ? ` +${k.subdomains.length - 3}`
                              : null}
                          </TD>
                          <TD className="text-xs">
                            <span className="space-x-1">
                              {k.hasMaster ? <Badge>master</Badge> : null}
                              {k.hasSql ? <Badge>runnable</Badge> : null}
                            </span>
                          </TD>
                        </TR>
                      ))}
                    </TBody>
                  </Table>
                </CardContent>
              </Card>
            </section>
          );
        },
      )}
    </div>
  );
}
