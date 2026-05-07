import Link from "next/link";
import { notFound } from "next/navigation";
import { existsSync, readFileSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { registry, VERTICALS } from "@/lib/registry";
import { Breadcrumb } from "@/components/ui/breadcrumb";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ERDDiagram } from "@/components/erd-diagram";
import { buildErd, styleLabel, type ModelStyle } from "@/lib/erd-derive";

const STYLES: ModelStyle[] = ["3nf", "vault", "dim"];
const STYLE_LINK_LABELS: Record<ModelStyle, string> = {
  "3nf": "3NF",
  vault: "Vault",
  dim: "Dimensional",
};

function findRepoRoot(): string {
  let dir = resolve(process.cwd());
  for (let i = 0; i < 8; i++) {
    if (existsSync(resolve(dir, "data", "taxonomy"))) return dir;
    const parent = dirname(dir);
    if (parent === dir) break;
    dir = parent;
  }
  return process.cwd();
}

export function generateStaticParams() {
  const reg = registry();
  const out: { subdomain: string; style: string }[] = [];
  for (const s of reg.subdomains) {
    for (const st of STYLES) out.push({ subdomain: s.id, style: st });
  }
  return out;
}

export const dynamic = "force-static";

interface Props {
  params: { subdomain: string; style: string };
}

export default function ModelStylePage({ params }: Props) {
  const reg = registry();
  const sub = reg.subdomains.find((x) => x.id === params.subdomain);
  if (!sub) notFound();
  const style = STYLES.find((s) => s === params.style) as ModelStyle | undefined;
  if (!style) notFound();
  const vert = VERTICALS.find((v) => v.slug === sub.vertical);
  const entities = sub.dataModel?.entities ?? [];
  const isFull = entities.some((e) => (e.attributes ?? []).length > 0);
  const graph = buildErd(style, entities);
  const ddlKey =
    style === "3nf"
      ? "threeNF"
      : style === "vault"
        ? "vault"
        : "dimensional";
  const ddlRel = sub.dataModelArtifacts?.[ddlKey];
  let ddlText: string | null = null;
  if (ddlRel) {
    const repoRoot = findRepoRoot();
    const ddlPath = join(repoRoot, ddlRel);
    if (existsSync(ddlPath)) {
      try {
        ddlText = readFileSync(ddlPath, "utf8");
      } catch {
        ddlText = null;
      }
    }
  }
  return (
    <div className="space-y-6">
      <Breadcrumb
        items={[
          { label: "Verticals", href: "/" },
          { label: vert?.label ?? sub.vertical, href: `/v/${sub.vertical}` },
          { label: sub.name, href: `/d/${sub.id}` },
          { label: "Models", href: "/models" },
          { label: styleLabel(style) },
        ]}
      />
      <header className="space-y-2">
        <Badge>{vert?.label ?? sub.vertical}</Badge>
        <h1 className="text-2xl font-bold tracking-tight md:text-3xl">
          {sub.name} — {styleLabel(style)}
        </h1>
        <p className="max-w-3xl text-sm text-muted-foreground">
          {style === "3nf"
            ? "Operational, normalized model — primary keys, foreign keys, and entity relationships as the system records them."
            : style === "vault"
              ? "Data Vault 2.0 derivation — hubs (business keys), links (relationships), and satellites (descriptive attributes)."
              : "Dimensional star schema derivation — facts for transactional/measurement entities, conformed dimensions for everything else."}
        </p>
      </header>
      <nav className="flex flex-wrap gap-2 text-sm">
        {STYLES.map((s) => (
          <Link
            key={s}
            href={`/models/${sub.id}/${s}`}
            className={
              s === style
                ? "rounded-md border bg-accent px-3 py-1.5"
                : "rounded-md border px-3 py-1.5 hover:bg-accent"
            }
          >
            {STYLE_LINK_LABELS[s]}
          </Link>
        ))}
      </nav>
      {!isFull ? (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Lightweight model</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-sm text-muted-foreground">
            <p>
              This subdomain has a name-only entity list in YAML — no per-column
              attributes yet. Add <code>dataModel.entities[].attributes[]</code> to
              the YAML to see a fully attributed ERD here.
            </p>
            <p>
              The 7 anchor subdomains (Payments, P&C Claims, Merchandising, Demand
              Planning, Hotel Revenue Management, MES &amp; Quality, Pharmacovigilance)
              ship full attributes plus DDL artifacts for all three styles.
            </p>
          </CardContent>
        </Card>
      ) : null}
      {graph.entities.length === 0 ? (
        <Card>
          <CardContent className="p-6 text-sm text-muted-foreground">
            No entities to render in this view.
          </CardContent>
        </Card>
      ) : (
        <ERDDiagram graph={graph} style={style} />
      )}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Entities ({graph.entities.length})</CardTitle>
        </CardHeader>
        <CardContent className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3 text-xs">
          {graph.entities.map((e) => (
            <div key={e.name} className="rounded border p-3">
              <div className="font-mono text-[12px] font-semibold">{e.name}</div>
              {e.description ? (
                <p className="text-muted-foreground">{e.description}</p>
              ) : null}
              <ul className="mt-2 space-y-0.5">
                {e.attributes.slice(0, 8).map((a) => (
                  <li key={a.name}>
                    <span
                      className={
                        a.isPrimaryKey
                          ? "font-bold"
                          : a.isForeignKey
                            ? "italic"
                            : ""
                      }
                    >
                      {a.name}
                    </span>
                    <span className="text-muted-foreground"> — {a.type}</span>
                  </li>
                ))}
                {e.attributes.length > 8 ? (
                  <li className="text-muted-foreground">
                    + {e.attributes.length - 8} more
                  </li>
                ) : null}
              </ul>
            </div>
          ))}
        </CardContent>
      </Card>
      {ddlText ? (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">DDL — {ddlRel}</CardTitle>
          </CardHeader>
          <CardContent>
            <pre className="max-h-[480px] overflow-auto rounded-md bg-muted p-3 text-xs">
              <code>{ddlText}</code>
            </pre>
          </CardContent>
        </Card>
      ) : null}
    </div>
  );
}
