import { existsSync } from "node:fs";
import { resolve } from "node:path";
import { registry, VERTICALS } from "@/lib/registry";
import { Breadcrumb } from "@/components/ui/breadcrumb";
import { CatalogTable, type CatalogRow } from "@/components/catalog-table";

export const dynamic = "force-static";

export const metadata = {
  title: "Catalog · Domain Explorer",
  description: "Searchable catalog of every entity in every subdomain.",
};

const REPO_GITHUB = "https://github.com/kvinayakpai/domain-explorer/blob/main/modeling/ddl";

function findRepoRoot(): string {
  let dir = resolve(process.cwd());
  for (let i = 0; i < 8; i++) {
    if (existsSync(resolve(dir, "modeling", "ddl"))) return dir;
    const parent = resolve(dir, "..");
    if (parent === dir) break;
    dir = parent;
  }
  return process.cwd();
}

function classify(name: string): CatalogRow["type"] {
  const n = name.toLowerCase();
  if (n.startsWith("fct_") || n.startsWith("fact_") || /transaction|event|order|claim|payment/.test(n)) {
    return "fact";
  }
  if (n.startsWith("dim_") || /customer|merchant|product|account|date/.test(n)) {
    return "dimension";
  }
  if (n.startsWith("stg_")) return "staging";
  return "raw";
}

export default function CatalogPage() {
  const reg = registry();
  const repoRoot = findRepoRoot();
  const verticalLabel = new Map<string, string>(
    VERTICALS.map((v) => [v.slug, v.label] as const),
  );

  const rows: CatalogRow[] = [];
  for (const sd of reg.subdomains) {
    const ownerPersona = sd.personas[0]?.title;
    const ddlLinks: { label: string; href: string }[] = [];
    for (const flavor of ["3nf", "vault", "dim"] as const) {
      const fname = `${sd.id}_${flavor}.sql`;
      if (existsSync(resolve(repoRoot, "modeling/ddl", fname))) {
        ddlLinks.push({ label: flavor.toUpperCase(), href: `${REPO_GITHUB}/${fname}` });
      }
    }
    for (const ent of sd.dataModel?.entities ?? []) {
      rows.push({
        entity: ent.name,
        type: classify(ent.name),
        description: ent.description ?? undefined,
        keys: ent.keys ?? [],
        subdomain: sd.id,
        subdomainName: sd.name,
        vertical: verticalLabel.get(sd.vertical) ?? sd.vertical,
        ownerPersona,
        ddlLinks,
      });
    }
  }

  return (
    <div className="space-y-6">
      <Breadcrumb
        items={[
          { label: "Verticals", href: "/" },
          { label: "Governance", href: "/governance" },
          { label: "Catalog" },
        ]}
      />
      <header className="space-y-2">
        <h1 className="text-2xl font-bold tracking-tight md:text-3xl">Catalog</h1>
        <p className="max-w-3xl text-muted-foreground">
          Every entity declared in a subdomain&rsquo;s data model, grouped by source subdomain.
          Use search and filters to find facts, dimensions, and staging tables — links go to the
          DDL files when modeling artefacts exist.
        </p>
      </header>
      {rows.length === 0 ? (
        <div className="rounded-lg border bg-muted/20 p-6 text-sm text-muted-foreground">
          No data-model entities declared yet. Add <code>dataModel.entities</code> to subdomain
          YAMLs to populate this view.
        </div>
      ) : (
        <CatalogTable rows={rows} />
      )}
    </div>
  );
}
