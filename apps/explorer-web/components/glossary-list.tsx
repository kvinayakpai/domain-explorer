"use client";
import * as React from "react";
import Link from "next/link";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export interface GlossaryItem {
  name: string;
  aliases: string[];
  definition: string;
  related_subdomains: string[];
  related_kpis: string[];
  steward?: string;
}

const ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ#".split("");

function bucketKey(name: string): string {
  const c = name[0]?.toUpperCase();
  if (!c) return "#";
  return /[A-Z]/.test(c) ? c : "#";
}

export function GlossaryList({ items }: { items: GlossaryItem[] }) {
  const [q, setQ] = React.useState("");
  const sorted = React.useMemo(
    () => [...items].sort((a, b) => a.name.localeCompare(b.name)),
    [items],
  );
  const filtered = React.useMemo(() => {
    const needle = q.trim().toLowerCase();
    if (!needle) return sorted;
    return sorted.filter((t) => {
      const haystack = [t.name, ...t.aliases, t.definition].join(" ").toLowerCase();
      return haystack.includes(needle);
    });
  }, [sorted, q]);
  const buckets = React.useMemo(() => {
    const out = new Map<string, GlossaryItem[]>();
    for (const t of filtered) {
      const k = bucketKey(t.name);
      if (!out.has(k)) out.set(k, []);
      out.get(k)!.push(t);
    }
    return out;
  }, [filtered]);

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <input
          type="search"
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder="Search terms, aliases, definitions…"
          className="w-full max-w-md rounded-md border bg-background px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-ring"
        />
        <span className="text-sm text-muted-foreground">
          {filtered.length} of {items.length} terms
        </span>
      </div>
      <nav className="flex flex-wrap gap-1 text-xs">
        {ALPHABET.map((letter) => {
          const has = buckets.has(letter);
          return (
            <a
              key={letter}
              href={has ? `#letter-${letter}` : undefined}
              aria-disabled={!has}
              className={
                "rounded-md border px-2 py-1 " +
                (has
                  ? "hover:bg-accent"
                  : "cursor-not-allowed text-muted-foreground/40")
              }
            >
              {letter}
            </a>
          );
        })}
      </nav>
      <div className="space-y-8">
        {ALPHABET.filter((l) => buckets.has(l)).map((letter) => (
          <section key={letter} id={`letter-${letter}`} className="space-y-3 scroll-mt-20">
            <h2 className="text-xl font-semibold">{letter}</h2>
            <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
              {buckets.get(letter)!.map((t) => (
                <Card key={t.name}>
                  <CardHeader className="space-y-1.5 p-4">
                    <div className="flex flex-wrap items-baseline justify-between gap-2">
                      <CardTitle className="text-base">{t.name}</CardTitle>
                      {t.steward && (
                        <span className="text-xs text-muted-foreground">{t.steward}</span>
                      )}
                    </div>
                    {t.aliases.length > 0 && (
                      <div className="flex flex-wrap gap-1">
                        {t.aliases.map((a) => (
                          <Badge key={a} className="text-[10px]">
                            {a}
                          </Badge>
                        ))}
                      </div>
                    )}
                  </CardHeader>
                  <CardContent className="space-y-2 p-4 pt-0 text-sm">
                    <p>{t.definition}</p>
                    {(t.related_subdomains.length > 0 || t.related_kpis.length > 0) && (
                      <div className="flex flex-wrap gap-x-3 gap-y-1 text-xs">
                        {t.related_subdomains.map((sd) => (
                          <Link
                            key={sd}
                            href={`/d/${sd}`}
                            className="text-muted-foreground hover:underline"
                          >
                            #{sd}
                          </Link>
                        ))}
                        {t.related_kpis.map((kid) => (
                          <Link
                            key={kid}
                            href={`/kpi/${kid}`}
                            className="text-muted-foreground hover:underline"
                          >
                            kpi:{kid}
                          </Link>
                        ))}
                      </div>
                    )}
                  </CardContent>
                </Card>
              ))}
            </div>
          </section>
        ))}
      </div>
    </div>
  );
}
