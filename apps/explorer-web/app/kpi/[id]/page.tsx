import { notFound } from "next/navigation";
import { registry } from "@/lib/registry";
import { Breadcrumb } from "@/components/ui/breadcrumb";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

export function generateStaticParams() {
  const ids = new Set<string>();
  const reg = registry();
  reg.kpis.forEach((k) => ids.add(k.id));
  reg.subdomains.forEach((s) => s.kpis.forEach((k) => ids.add(k.id)));
  return Array.from(ids).map((id) => ({ id }));
}

export default function KpiPage({ params }: { params: { id: string } }) {
  const reg = registry();
  const fromRegistry = reg.kpis.find((k) => k.id === params.id);
  const fromSubdomain = reg.subdomains.flatMap((s) => s.kpis).find((k) => k.id === params.id);
  const k = fromRegistry ?? fromSubdomain;
  if (!k) notFound();
  const owningSub = reg.subdomains.find((s) => s.kpis.some((x) => x.id === k.id));
  return (
    <div className="space-y-6">
      <Breadcrumb
        items={[
          { label: "Verticals", href: "/" },
          { label: "KPI" },
          { label: k.name },
        ]}
      />
      <header className="space-y-2">
        <h1 className="text-2xl font-bold tracking-tight md:text-3xl">{k.name}</h1>
        <div className="flex flex-wrap gap-2">
          <Badge>{k.unit}</Badge>
          <Badge>{k.direction.replace(/_/g, " ")}</Badge>
          {"vertical" in k && k.vertical ? <Badge>{k.vertical}</Badge> : null}
          {owningSub ? <Badge>{owningSub.name}</Badge> : null}
        </div>
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
    </div>
  );
}
