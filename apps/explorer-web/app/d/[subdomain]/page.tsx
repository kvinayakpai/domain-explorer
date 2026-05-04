import Link from "next/link";
import { notFound } from "next/navigation";
import { registry, VERTICALS } from "@/lib/registry";
import { Breadcrumb } from "@/components/ui/breadcrumb";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Table, THead, TBody, TR, TH, TD } from "@/components/ui/table";

export function generateStaticParams() {
  return registry().subdomains.map((s) => ({ subdomain: s.id }));
}

interface SectionProps {
  title: string;
  children: React.ReactNode;
}
function Section({ title, children }: SectionProps) {
  return (
    <section className="space-y-3">
      <h2 className="text-lg font-semibold">{title}</h2>
      {children}
    </section>
  );
}

export default function SubdomainPage({ params }: { params: { subdomain: string } }) {
  const s = registry().subdomains.find((x) => x.id === params.subdomain);
  if (!s) notFound();
  const vert = VERTICALS.find((v) => v.slug === s.vertical);
  return (
    <div className="space-y-8">
      <Breadcrumb
        items={[
          { label: "Verticals", href: "/" },
          { label: vert?.label ?? s.vertical, href: `/v/${s.vertical}` },
          { label: s.name },
        ]}
      />
      <header className="space-y-2">
        <Badge>{vert?.label ?? s.vertical}</Badge>
        <h1 className="text-2xl font-bold tracking-tight md:text-3xl">{s.name}</h1>
        <p className="max-w-3xl text-muted-foreground">{s.oneLiner}</p>
      </header>

      {/* 1. Personas */}
      <Section title="Personas">
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
          {s.personas.map((p) => (
            <Card key={p.name}>
              <CardHeader>
                <CardTitle className="text-sm">{p.title}</CardTitle>
                <p className="text-xs text-muted-foreground">{p.level}</p>
              </CardHeader>
            </Card>
          ))}
        </div>
      </Section>

      {/* 2. Decisions */}
      <Section title="Decisions supported">
        <ul className="list-disc space-y-2 pl-6 text-sm">
          {s.decisions.map((d) => (
            <li key={d.id}>
              <span className="font-mono text-xs text-muted-foreground">{d.id}</span> — {d.statement}
            </li>
          ))}
        </ul>
      </Section>

      {/* 3. KPIs */}
      <Section title="KPIs">
        <Card>
          <CardContent className="p-0">
            <Table>
              <THead>
                <TR>
                  <TH>Name</TH>
                  <TH>Formula</TH>
                  <TH>Unit</TH>
                  <TH>Direction</TH>
                </TR>
              </THead>
              <TBody>
                {s.kpis.map((k) => (
                  <TR key={k.id}>
                    <TD>
                      <Link className="font-medium hover:underline" href={`/kpi/${k.id}`}>
                        {k.name}
                      </Link>
                    </TD>
                    <TD className="font-mono text-xs">{k.formula}</TD>
                    <TD>{k.unit}</TD>
                    <TD>{k.direction.replace(/_/g, " ")}</TD>
                  </TR>
                ))}
              </TBody>
            </Table>
          </CardContent>
        </Card>
      </Section>

      {/* 4. Data model */}
      <Section title="Data model — entities">
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {s.dataModel.entities.map((e) => (
            <Card key={e.name}>
              <CardHeader>
                <CardTitle className="text-sm">{e.name}</CardTitle>
                {e.description ? (
                  <p className="text-xs text-muted-foreground">{e.description}</p>
                ) : null}
              </CardHeader>
              <CardContent className="text-xs">
                <span className="text-muted-foreground">keys:</span>{" "}
                <code>{e.keys.join(", ")}</code>
              </CardContent>
            </Card>
          ))}
        </div>
      </Section>

      {/* 5. Source systems */}
      <Section title="Source systems">
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {s.sourceSystems.map((src) => (
            <Card key={`${src.vendor}-${src.product}`}>
              <CardHeader>
                <CardTitle className="text-sm">
                  {src.vendor} — {src.product}
                </CardTitle>
                <p className="text-xs text-muted-foreground">{src.category}</p>
              </CardHeader>
            </Card>
          ))}
        </div>
      </Section>

      {/* 6. Connectors */}
      <Section title="Connectors">
        <Card>
          <CardContent className="p-0">
            <Table>
              <THead>
                <TR>
                  <TH>Type</TH>
                  <TH>Protocol</TH>
                  <TH>Auth</TH>
                </TR>
              </THead>
              <TBody>
                {s.connectors.map((c, i) => (
                  <TR key={`${c.type}-${i}`}>
                    <TD>{c.type}</TD>
                    <TD>{c.protocol}</TD>
                    <TD>{c.auth}</TD>
                  </TR>
                ))}
              </TBody>
            </Table>
          </CardContent>
        </Card>
      </Section>

      {/* 7. Ingestion challenges */}
      <Section title="Ingestion challenges">
        <ul className="list-disc space-y-1 pl-6 text-sm">
          {s.ingestionChallenges.map((c, i) => (
            <li key={i}>{c}</li>
          ))}
        </ul>
      </Section>

      {/* 8. Integration challenges */}
      <Section title="Integration challenges">
        <ul className="list-disc space-y-1 pl-6 text-sm">
          {s.integrationChallenges.map((c, i) => (
            <li key={i}>{c}</li>
          ))}
        </ul>
      </Section>

      {/* 9. Vertical context */}
      <Section title="Vertical context">
        <p className="text-sm text-muted-foreground">
          Part of <Link className="underline" href={`/v/${s.vertical}`}>{vert?.label ?? s.vertical}</Link>.
        </p>
      </Section>
    </div>
  );
}
