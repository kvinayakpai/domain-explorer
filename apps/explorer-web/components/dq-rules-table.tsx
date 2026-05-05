"use client";
import * as React from "react";
import { CheckCircle2, XCircle, AlertTriangle } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import type { DqResult } from "@/lib/dq";

const SEVERITY_ORDER = ["critical", "high", "medium", "low"] as const;

function StatusBadge({ r }: { r: DqResult }) {
  if (r.error) {
    return (
      <span className="inline-flex items-center gap-1 rounded-md border border-amber-300 bg-amber-100 px-2 py-0.5 text-xs font-semibold text-amber-900 dark:bg-amber-900/30 dark:text-amber-200">
        <AlertTriangle className="h-3 w-3" /> errored
      </span>
    );
  }
  if (r.passed) {
    return (
      <span className="inline-flex items-center gap-1 rounded-md border border-emerald-300 bg-emerald-100 px-2 py-0.5 text-xs font-semibold text-emerald-900 dark:bg-emerald-900/30 dark:text-emerald-200">
        <CheckCircle2 className="h-3 w-3" /> pass
      </span>
    );
  }
  return (
    <span className="inline-flex items-center gap-1 rounded-md border border-red-300 bg-red-100 px-2 py-0.5 text-xs font-semibold text-red-900 dark:bg-red-900/30 dark:text-red-200">
      <XCircle className="h-3 w-3" /> fail
    </span>
  );
}

function SeverityPill({ sev }: { sev: DqResult["severity"] }) {
  const tone =
    sev === "critical"
      ? "bg-red-100 text-red-900 dark:bg-red-900/40 dark:text-red-200"
      : sev === "high"
      ? "bg-orange-100 text-orange-900 dark:bg-orange-900/40 dark:text-orange-200"
      : sev === "medium"
      ? "bg-amber-100 text-amber-900 dark:bg-amber-900/40 dark:text-amber-200"
      : "bg-slate-100 text-slate-900 dark:bg-slate-900/40 dark:text-slate-200";
  return (
    <span className={`inline-flex items-center rounded-md px-2 py-0.5 text-xs font-medium capitalize ${tone}`}>
      {sev}
    </span>
  );
}

export function DqRulesTable({ results }: { results: DqResult[] }) {
  const [q, setQ] = React.useState("");
  const [statusFilter, setStatusFilter] = React.useState<"all" | "passed" | "failed" | "errored">("all");
  const [sevFilter, setSevFilter] = React.useState<string>("all");
  const [subFilter, setSubFilter] = React.useState<string>("all");

  const subdomains = React.useMemo(() => {
    return Array.from(new Set(results.map((r) => r.subdomain))).sort();
  }, [results]);

  const filtered = React.useMemo(() => {
    const needle = q.trim().toLowerCase();
    return results
      .filter((r) => {
        if (statusFilter === "passed" && !r.passed) return false;
        if (statusFilter === "failed" && (r.passed || r.error)) return false;
        if (statusFilter === "errored" && !r.error) return false;
        if (sevFilter !== "all" && r.severity !== sevFilter) return false;
        if (subFilter !== "all" && r.subdomain !== subFilter) return false;
        if (!needle) return true;
        return (
          r.id.toLowerCase().includes(needle) ||
          r.expectation.toLowerCase().includes(needle) ||
          r.table.toLowerCase().includes(needle)
        );
      })
      .sort((a, b) => {
        const sa = SEVERITY_ORDER.indexOf(a.severity);
        const sb = SEVERITY_ORDER.indexOf(b.severity);
        if (sa !== sb) return sa - sb;
        return a.id.localeCompare(b.id);
      });
  }, [results, q, statusFilter, sevFilter, subFilter]);

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap items-center gap-2">
        <input
          type="search"
          placeholder="Search rule id, expectation, or table…"
          value={q}
          onChange={(e) => setQ(e.target.value)}
          className="min-w-[14rem] flex-1 rounded-md border bg-background px-3 py-1.5 text-sm"
        />
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value as typeof statusFilter)}
          className="rounded-md border bg-background px-2 py-1.5 text-sm"
        >
          <option value="all">All status</option>
          <option value="passed">Passed</option>
          <option value="failed">Failed</option>
          <option value="errored">Errored</option>
        </select>
        <select
          value={sevFilter}
          onChange={(e) => setSevFilter(e.target.value)}
          className="rounded-md border bg-background px-2 py-1.5 text-sm"
        >
          <option value="all">All severity</option>
          {SEVERITY_ORDER.map((s) => (
            <option key={s} value={s}>
              {s}
            </option>
          ))}
        </select>
        <select
          value={subFilter}
          onChange={(e) => setSubFilter(e.target.value)}
          className="rounded-md border bg-background px-2 py-1.5 text-sm"
        >
          <option value="all">All subdomains</option>
          {subdomains.map((s) => (
            <option key={s} value={s}>
              {s}
            </option>
          ))}
        </select>
        <span className="ml-auto text-xs text-muted-foreground">
          {filtered.length} of {results.length} rules
        </span>
      </div>
      <div className="overflow-x-auto rounded-lg border">
        <table className="w-full text-sm">
          <thead className="bg-muted/40 text-left text-xs uppercase tracking-wide text-muted-foreground">
            <tr>
              <th className="px-3 py-2">Rule</th>
              <th className="px-3 py-2">Status</th>
              <th className="px-3 py-2">Severity</th>
              <th className="px-3 py-2">Subdomain</th>
              <th className="px-3 py-2">Table</th>
              <th className="px-3 py-2">Type</th>
              <th className="px-3 py-2">Expectation</th>
              <th className="px-3 py-2 text-right">Failing</th>
              <th className="px-3 py-2 text-right">ms</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((r) => (
              <tr key={r.id} className="border-t hover:bg-accent/30">
                <td className="px-3 py-2 font-mono text-xs">{r.id}</td>
                <td className="px-3 py-2"><StatusBadge r={r} /></td>
                <td className="px-3 py-2"><SeverityPill sev={r.severity} /></td>
                <td className="px-3 py-2">{r.subdomain}</td>
                <td className="px-3 py-2 font-mono text-xs">{r.table}{r.column ? `.${r.column}` : ""}</td>
                <td className="px-3 py-2">{r.rule_type}</td>
                <td className="px-3 py-2 text-xs text-muted-foreground">{r.expectation}</td>
                <td className="px-3 py-2 text-right tabular-nums">
                  {r.error ? "—" : r.failing_rows.toLocaleString()}
                </td>
                <td className="px-3 py-2 text-right tabular-nums text-muted-foreground">{r.duration_ms}</td>
              </tr>
            ))}
            {filtered.length === 0 && (
              <tr>
                <td colSpan={9} className="px-3 py-6 text-center text-sm text-muted-foreground">
                  No rules match the filters.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
