import Link from "next/link";
import { ArrowRight } from "lucide-react";
import { registry, VERTICALS } from "@/lib/registry";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

export default function HomePage() {
  const reg = registry();
  const counts = new Map<string, number>();
  for (const s of reg.subdomains) {
    counts.set(s.vertical, (counts.get(s.vertical) ?? 0) + 1);
  }
  return (
    <div className="space-y-8">
      <section className="space-y-3">
        <h1 className="text-3xl font-bold tracking-tight md:text-4xl">Domain Explorer</h1>
        <p className="max-w-2xl text-muted-foreground">
          Browse industry verticals, drill into business subdomains, and see the personas, KPIs,
          source systems, and integration patterns that drive each one. Everything on this site is
          rendered from a typed YAML registry.
        </p>
      </section>
      <section>
        <div className="mb-4 flex items-baseline justify-between">
          <h2 className="text-xl font-semibold">Verticals</h2>
          <span className="text-sm text-muted-foreground">{reg.subdomains.length} subdomains seeded</span>
        </div>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {VERTICALS.map((v) => {
            const count = counts.get(v.slug) ?? 0;
            return (
              <Link key={v.slug} href={`/v/${v.slug}`} className="group">
                <Card className="h-full transition-colors group-hover:bg-accent">
                  <CardHeader>
                    <div className="flex items-center justify-between">
                      <CardTitle className="text-base">{v.label}</CardTitle>
                      <Badge>{count}</Badge>
                    </div>
                    <CardDescription>{v.slug}</CardDescription>
                  </CardHeader>
                  <CardContent className="flex items-center justify-end text-sm text-muted-foreground">
                    Explore <ArrowRight className="ml-1 h-4 w-4" />
                  </CardContent>
                </Card>
              </Link>
            );
          })}
        </div>
      </section>
    </div>
  );
}
