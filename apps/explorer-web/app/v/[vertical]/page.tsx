import Link from "next/link";
import { notFound } from "next/navigation";
import { registry, VERTICALS } from "@/lib/registry";
import { Breadcrumb } from "@/components/ui/breadcrumb";
import { Card, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

export function generateStaticParams() {
  return VERTICALS.map((v) => ({ vertical: v.slug }));
}

export default function VerticalPage({ params }: { params: { vertical: string } }) {
  const vertical = VERTICALS.find((v) => v.slug === params.vertical);
  if (!vertical) notFound();
  const reg = registry();
  const subs = reg.subdomains.filter((s) => s.vertical === params.vertical);
  return (
    <div className="space-y-6">
      <Breadcrumb items={[{ label: "Verticals", href: "/" }, { label: vertical.label }]} />
      <header className="space-y-2">
        <h1 className="text-2xl font-bold tracking-tight md:text-3xl">{vertical.label}</h1>
        <p className="text-sm text-muted-foreground">
          {subs.length} subdomain{subs.length === 1 ? "" : "s"} seeded.
        </p>
      </header>
      {subs.length === 0 ? (
        <p className="text-sm text-muted-foreground">No subdomains seeded yet for this vertical.</p>
      ) : (
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
          {subs.map((s) => (
            <Link key={s.id} href={`/d/${s.id}`} className="group">
              <Card className="h-full transition-colors group-hover:bg-accent">
                <CardHeader>
                  <CardTitle className="text-base">{s.name}</CardTitle>
                  <CardDescription>{s.oneLiner}</CardDescription>
                </CardHeader>
              </Card>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
