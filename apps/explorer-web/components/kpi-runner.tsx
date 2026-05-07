"use client";
import * as React from "react";
import { Button } from "@/components/ui/button";

const STYLES = [
  { slug: "3nf", label: "3NF" },
  { slug: "vault", label: "Vault" },
  { slug: "dim", label: "Dimensional" },
] as const;

type StyleSlug = (typeof STYLES)[number]["slug"];

interface RunResult {
  rows?: unknown[];
  sql?: string;
  error?: string;
}

export function KpiRunner({ kpiId }: { kpiId: string }) {
  const [style, setStyle] = React.useState<StyleSlug>("3nf");
  const [since, setSince] = React.useState<string>("");
  const [busy, setBusy] = React.useState(false);
  const [result, setResult] = React.useState<RunResult | null>(null);
  const run = async () => {
    setBusy(true);
    setResult(null);
    try {
      const res = await fetch(`/api/kpi/${encodeURIComponent(kpiId)}/run`, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ style, since: since || undefined }),
      });
      const json = (await res.json()) as RunResult;
      setResult(json);
    } catch (e) {
      setResult({ error: (e as Error).message });
    } finally {
      setBusy(false);
    }
  };
  return (
    <div className="space-y-3 rounded-md border p-3">
      <div className="flex flex-wrap items-end gap-2">
        <div className="space-y-1">
          <label className="text-xs font-medium text-muted-foreground" htmlFor="kpi-style">
            Style
          </label>
          <select
            id="kpi-style"
            className="rounded-md border bg-background px-2 py-1 text-sm"
            value={style}
            onChange={(e) => setStyle(e.target.value as StyleSlug)}
          >
            {STYLES.map((s) => (
              <option key={s.slug} value={s.slug}>
                {s.label}
              </option>
            ))}
          </select>
        </div>
        <div className="space-y-1">
          <label className="text-xs font-medium text-muted-foreground" htmlFor="kpi-since">
            Since (YYYY-MM-DD)
          </label>
          <input
            id="kpi-since"
            type="date"
            className="rounded-md border bg-background px-2 py-1 text-sm"
            value={since}
            onChange={(e) => setSince(e.target.value)}
          />
        </div>
        <Button onClick={run} disabled={busy}>
          {busy ? "Running…" : "Run this query"}
        </Button>
      </div>
      {result ? (
        <div className="space-y-2">
          {result.error ? (
            <p className="text-sm text-destructive">{result.error}</p>
          ) : null}
          {result.sql ? (
            <details className="text-xs">
              <summary className="cursor-pointer text-muted-foreground">
                Query executed
              </summary>
              <pre className="mt-1 max-h-40 overflow-auto rounded bg-muted p-2">
                <code>{result.sql}</code>
              </pre>
            </details>
          ) : null}
          {Array.isArray(result.rows) && result.rows.length > 0 ? (
            <div className="overflow-auto rounded border">
              <table className="w-full text-xs">
                <thead className="bg-muted">
                  <tr>
                    {Object.keys(result.rows[0] as object).map((col) => (
                      <th key={col} className="px-2 py-1 text-left font-medium">
                        {col}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {result.rows.slice(0, 50).map((row, i) => (
                    <tr key={i} className="border-t">
                      {Object.values(row as object).map((v, j) => (
                        <td key={j} className="px-2 py-1 font-mono">
                          {v === null ? "—" : String(v)}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : Array.isArray(result.rows) ? (
            <p className="text-xs text-muted-foreground">No rows returned.</p>
          ) : null}
        </div>
      ) : null}
    </div>
  );
}
