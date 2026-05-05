import Link from "next/link";
import { ArrowRight, PlayCircle, Database } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { listDemoFlows } from "@/lib/demo-flows";

export const metadata = {
  title: "Demo flows · Domain Explorer",
  description: "12 vertical-specific scripted tours an SE can click through during a customer pitch.",
};

export default function DemoIndexPage() {
  const flows = listDemoFlows();
  const fullCount = flows.filter((f) => f.hasFullStack).length;
  return (
    <div className="space-y-8">
      <header className="space-y-2">
        <Badge>Demo flows</Badge>
        <h1 className="text-2xl font-bold tracking-tight md:text-3xl">
          Vertical-specific demo flows
        </h1>
        <p className="max-w-3xl text-muted-foreground">
          Each tour is a 3-screen click-through tailored to a vertical: the persona pain it
          starts from, the answer (KPIs and lineage to source systems), and the platform
          stack underneath. {fullCount} of {flows.length} are anchored on a subdomain we have
          full DDL + populated DuckDB data for.
        </p>
      </header>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
        {flows.map((f) => (
          <Link key={f.verticalSlug} href={`/demo/${f.verticalSlug}`} className="group">
            <Card className="h-full transition-colors group-hover:bg-accent">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="text-base">{f.verticalLabel}</CardTitle>
                  {f.hasFullStack ? (
                    <Badge className="bg-emerald-100 text-emerald-900 dark:bg-emerald-900/30 dark:text-emerald-200">
                      Full stack
                    </Badge>
                  ) : (
                    <Badge variant="secondary">Anchor</Badge>
                  )}
                </div>
                <CardDescription className="line-clamp-2">
                  Anchored on{" "}
                  <span className="font-medium text-foreground">{f.hero.name}</span>
                  {" — "}
                  {f.hero.oneLiner}
                </CardDescription>
              </CardHeader>
              <CardContent className="flex items-center justify-between text-sm text-muted-foreground">
                <span className="inline-flex items-center gap-1">
                  {f.hasFullStack ? (
                    <Database className="h-3.5 w-3.5" />
                  ) : (
                    <PlayCircle className="h-3.5 w-3.5" />
                  )}
                  3-screen tour
                </span>
                <ArrowRight className="ml-1 h-4 w-4 transition-transform group-hover:translate-x-0.5" />
              </CardContent>
            </Card>
          </Link>
        ))}
      </div>
    </div>
  );
}
