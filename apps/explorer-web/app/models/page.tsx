import Link from "next/link";
import { registry, VERTICALS } from "@/lib/registry";
import { Breadcrumb } from "@/components/ui/breadcrumb";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ERDThumbnail } from "@/components/erd-diagram";

export const dynamic = "force-static";

const STYLES = [
  { slug: "3nf", label: "3NF" },
  { slug: "vault", label: "Vault" },
  { slug: "dim", label: "Dim" },
] as const;

export default function ModelsIndex() {
  const reg = registry();
  const subdomains = reg.subdomains;
  const grouped = new Map<string, typeof subdomains>();
  for (const v of VERTICALS) grouped.set(v.slug, [] as typeof subdomains);
  for (const s of subdomains) {
    grouped.get(s.vertical)?.push(s);
  }
  const totalEntities = subdomains.reduce(
    (n, s) => n + (s.dataModel?.entities?.length ?? 0),
    0,
  );
  const fullyAttributed = subdomains.filter((s) =>
    (s.dataModel?.entities ?? []).some((e) => (e.attributes ?? []).length > 0),
  );
  return (
    <div className="space-y-8">
      <Breadcrumb items={[{ label: "Verticals", href: "/" }, { label: "Models" }]} />
      <header className="space-y-2">
        <h1 className="text-2xl font-bold tracking-tight md:text-3xl">Data models</h1>
        <p className="max-w-3xl text-muted-foreground">
          Per-subdomain data models, viewable as 3NF (operational), Data Vault 2.0, or
          Dimensional star schemas. The 7 anchor subdomains have hand-authored, fully
          attributed entities and DDL artifacts; the remaining breadth subdomains have
          lightweight YAML-derived models.
        </p>
        <div className="flex flex-wrap gap-2 pt-2">
          <Badge>{subdomains.length} subdomains</Badge>
          <Badge>{totalEntities} entities</Badge>
          <Badge>{fullyAttributed.length} fully attributed</Badge>
          <Badge>{STYLES.length} styles each</Badge>
        </div>
      </header>
      {VERTICALS.filter((v) => (grouped.get(v.slug) ?? []).length > 0).map((v) => {
        const list = grouped.get(v.slug) ?? [];
        return (
          <section key={v.slug} className="space-y-3">
            <h2 className="text-lg font-semibold">{v.label}</h2>
            <div className="grid grid-cols-1 gap-3 md:grid-cols-2 lg:grid-cols-3">
              {list.map((s) => {
                const entCount = s.dataModel?.entities?.length ?? 0;
                const isFull = (s.dataModel?.entities ?? []).some(
                  (e) => (e.attributes ?? []).length > 0,
                );
                return (
                  <Card key={s.id}>
                    <CardHeader>
                      <div className="flex items-start justify-between gap-3">
                        <div>
                          <CardTitle className="text-sm">
                            <Link
                              href={`/models/${s.id}/3nf`}
                              className="hover:underline"
                            >
                              {s.name}
                            </Link>
                          </CardTitle>
                          <p className="text-xs text-muted-foreground">
                            {entCount} entit{entCount === 1 ? "y" : "ies"}
                          </p>
                        </div>
                        {isFull ? <Badge>full</Badge> : <Badge>lightweight</Badge>}
                      </div>
                    </CardHeader>
                    <CardContent className="space-y-2">
                      <ERDThumbnail entityCount={entCount} style="3nf" />
                      <div className="flex gap-2 text-xs">
                        {STYLES.map((st) => {
                          const enabled =
                            st.slug === "3nf" ||
                            isFull ||
                            !!s.dataModelArtifacts?.[
                              st.slug === "vault" ? "vault" : "dimensional"
                            ];
                          return enabled ? (
                            <Link
                              key={st.slug}
                              href={`/models/${s.id}/${st.slug}`}
                              className="rounded-md border px-2 py-1 hover:bg-accent"
                            >
                              {st.label}
                            </Link>
                          ) : (
                            <span
                              key={st.slug}
                              className="rounded-md border px-2 py-1 text-muted-foreground/60"
                            >
                              {st.label}
                            </span>
                          );
                        })}
                      </div>
                    </CardContent>
                  </Card>
                );
              })}
            </div>
          </section>
        );
      })}
    </div>
  );
}
