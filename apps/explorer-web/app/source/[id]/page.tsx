import { notFound } from "next/navigation";
import { registry } from "@/lib/registry";
import { Breadcrumb } from "@/components/ui/breadcrumb";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

export function generateStaticParams() {
  return registry().sourceSystems.map((s) => ({ id: s.id }));
}

export default function SourcePage({ params }: { params: { id: string } }) {
  const reg = registry();
  const s = reg.sourceSystems.find((x) => x.id === params.id);
  if (!s) notFound();
  const connectors = reg.connectors.filter((c) =>
    s.primaryConnectors.includes(c.id),
  );
  const usedIn = reg.subdomains.filter((sd) =>
    sd.sourceSystems.some(
      (src) => src.vendor === s.vendor && src.product === s.product,
    ),
  );
  return (
    <div className="space-y-6">
      <Breadcrumb
        items={[
          { label: "Verticals", href: "/" },
          { label: "Source system" },
          { label: `${s.vendor} ${s.product}` },
        ]}
      />
      <header className="space-y-2">
        <Badge>{s.category}</Badge>
        <h1 className="text-2xl font-bold tracking-tight md:text-3xl">
          {s.vendor} — {s.product}
        </h1>
      </header>
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Primary connectors</CardTitle>
        </CardHeader>
        <CardContent className="text-sm">
          {connectors.length === 0 ? (
            <p className="text-muted-foreground">None configured.</p>
          ) : (
            <ul className="space-y-1">
              {connectors.map((c) => (
                <li key={c.id}>
                  <span className="font-medium">{c.type}</span>{" "}
                  <span className="text-muted-foreground">
                    · {c.protocol} · {c.auth} · {c.latency}
                  </span>
                </li>
              ))}
            </ul>
          )}
        </CardContent>
      </Card>
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Used in subdomains</CardTitle>
        </CardHeader>
        <CardContent className="text-sm">
          {usedIn.length === 0 ? (
            <p className="text-muted-foreground">Not yet referenced.</p>
          ) : (
            <ul className="list-disc space-y-1 pl-6">
              {usedIn.map((sd) => (
                <li key={sd.id}>{sd.name}</li>
              ))}
            </ul>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
