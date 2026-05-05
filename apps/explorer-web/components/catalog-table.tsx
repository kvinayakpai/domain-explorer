"use client";
import * as React from "react";
import Link from "next/link";
import { Badge } from "@/components/ui/badge";

export interface CatalogRow {
  entity: string;
  type: "fact" | "dimension" | "staging" | "raw";
  description?: string;
  keys: string[];
  subdomain: string;
  subdomainName: string;
  vertical: string;
  ownerPersona?: string;
  ddlLinks: { label: string; href: string }[];
}

const TYPE_ORDER = ["fact", "dimension", "staging", "raw"] as const;

export function CatalogTable({ rows }: { rows: CatalogRow[] }) {
  const [q, setQ] = React.useState("");
  const [vertical, setVertical] = React.useState<string>("all");
  const [type, setType] = React.useState<string>("all");

  const verticals = React.useMemo(() => {
    return Array.from(new Set(rows.map((r) => r.vertical))).sort();
  }, [rows]);

  const filtered = React.useMemo(() => {
    const needle = q.trim().toLowerCase();
    return rows.filter((r) => {
      if (vertical !== "all" && r.vertical !== vertical) return false;
      if (type !== "all" && r.type !== type) return false;
      if (!needle) return true;
      const hay =
        `${r.entity} ${r.subdomainName} ${r.description ?? ""} ${r.keys.join(" ")}`.toLowerCase();
      return hay.includes(needle);
    });
  }, [rows, q, vertical, type]);

  const grouped = React.useMemo(() => {
    const out = new Map<string, CatalogRow[]>();
    for (const r of filtered) {
      if (!out.has(r.subdomain)) out.set(r.subdomain, []);
      out.get(r.subdomain)!.push(r);
    }
    for (const list of out.values()) {
      list.sort((a, b) => {
        const ai = TYPE_ORDER.indexOf(a.type as never);
        const bi = TYPE_ORDER.indexOf(b.type as never);
        if (ai !== bi) return ai - bi;
        return a.entity.localeCompare(b.entity);
      });
    }
    return [...out.entries()].sort((a, b) =>
      a[1][0].subdomainName.localeCompare(b[1][0].subdomainName),
    );
  }, [filtered]);

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-3">
        <input
          type="search"
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder="Search entities, keys, or descriptions…"
          className="w-full max-w-md rounded-md border bg-background px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-ring"
        />
        <select
          value={vertical}
          onChange={(e) => setVertical(e.target.value)}
          className="rounded-md border bg-background px-2 py-2 text-sm"
          aria-label="Filter by vertical"
        >
          <option value="all">All verticals</option>
          {verticals.map((v) => (
            <option key={v} value={v}>
              {v}
            </option>
          ))}
        </select>
        <select
          value={type}
          onChange={(e) => setType(e.target.value)}
          className="rounded-md border bg-background px-2 py-2 text-sm"
          aria-label="Filter by type"
        >
          <option value="all">All types</option>
          {TYPE_ORDER.map((t) => (
            <option key={t} value={t}>
              {t}
            </option>
          ))}
        </select>
        <span className="ml-auto text-sm text-muted-foreground">
          {filtered.length} of {rows.length} entities
        </span>
      </div>

      <div className="space-y-6">
        {grouped.map(([sd, list]) => (
          <section key={sd} className="rounded-lg border">
            <header className="flex items-center justify-between border-b bg-muted/40 px-4 py-2">
              <Link href={`/d/${sd}`} className="text-sm font-semibold hover:underline">
                {list[0].subdomainName}
              </Link>
              <span className="text-xs text-muted-foreground">
                {list[0].vertical} · {list.length} entit{list.length === 1 ? "y" : "ies"}
              </span>
            </header>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-muted/20 text-left text-xs uppercase tracking-wide text-muted-foreground">
                  <tr>
                    <th className="px-4 py-2">Entity</th>
                    <th className="px-4 py-2">Type</th>
                    <th className="px-4 py-2">Keys</th>
                    <th className="px-4 py-2">Owner</th>
                    <th className="px-4 py-2">DDL</th>
                  </tr>
                </thead>
                <tbody>
                  {list.map((r) => (
                    <tr key={`${sd}.${r.entity}`} className="border-t">
                      <td className="px-4 py-2 align-top">
                        <div className="font-medium">{r.entity}</div>
                        {r.description && (
                          <div className="mt-0.5 text-xs text-muted-foreground">
                            {r.description}
                          </div>
                        )}
                      </td>
                      <td className="px-4 py-2 align-top">
                        <Badge className="text-[10px] uppercase">{r.type}</Badge>
                      </td>
                      <td className="px-4 py-2 align-top font-mono text-xs">
                        {r.keys.join(", ") || <span className="text-muted-foreground">—</span>}
                      </td>
                      <td className="px-4 py-2 align-top text-xs">
                        {r.ownerPersona ?? <span className="text-muted-foreground">—</span>}
                      </td>
                      <td className="px-4 py-2 align-top">
                        <div className="flex flex-wrap gap-1 text-xs">
                          {r.ddlLinks.length === 0 && (
                            <span className="text-muted-foreground">—</span>
                          )}
                          {r.ddlLinks.map((l) => (
                            <a
                              key={l.label}
                              href={l.href}
                              target="_blank"
                              rel="noreferrer"
                              className="rounded border bg-background px-1.5 py-0.5 hover:bg-accent"
                            >
                              {l.label}
                            </a>
                          ))}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        ))}
        {grouped.length === 0 && (
          <div className="rounded-lg border bg-muted/20 p-6 text-center text-sm text-muted-foreground">
            No entities match your filters.
          </div>
        )}
      </div>
    </div>
  );
}
