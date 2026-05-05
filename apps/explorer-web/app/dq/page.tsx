import { ShieldCheck, AlertTriangle, CheckCircle2, XCircle, Clock } from "lucide-react";
import { Breadcrumb } from "@/components/ui/breadcrumb";
import { Badge } from "@/components/ui/badge";
import { loadDqReport } from "@/lib/dq";
import { DqRulesTable } from "@/components/dq-rules-table";

// Render at request time so live data is fetched when the API is available.
export const dynamic = "force-dynamic";
export const revalidate = 0;

export const metadata = {
  title: "Data Quality · Domain Explorer",
  description: "Real DQ rules executed against the populated DuckDB.",
};

function Metric({
  label,
  value,
  hint,
  tone = "neutral",
}: {
  label: string;
  value: string | number;
  hint?: string;
  tone?: "neutral" | "good" | "warn" | "bad";
}) {
  const toneClass =
    tone === "good"
      ? "text-emerald-600 dark:text-emerald-400"
      : tone === "warn"
      ? "text-amber-600 dark:text-amber-400"
      : tone === "bad"
      ? "text-red-600 dark:text-red-400"
      : "text-foreground";
  return (
    <div className="rounded-lg border bg-card p-4">
      <div className="text-xs uppercase tracking-wide text-muted-foreground">{label}</div>
      <div className={`mt-1 text-2xl font-semibold ${toneClass}`}>{value}</div>
      {hint && <div className="mt-0.5 text-xs text-muted-foreground">{hint}</div>}
    </div>
  );
}

export default async function DqPage() {
  const { report, source } = await loadDqReport();

  return (
    <div className="space-y-6">
      <Breadcrumb
        items={[
          { label: "Verticals", href: "/" },
          { label: "Governance", href: "/governance" },
          { label: "Data Quality" },
        ]}
      />
      <header className="space-y-2">
        <div className="flex items-center gap-2">
          <Badge>Governance</Badge>
          <Badge className="bg-emerald-100 text-emerald-900 dark:bg-emerald-900/30 dark:text-emerald-200">
            {source === "live" ? "Live API" : source === "snapshot" ? "Committed snapshot" : "Unavailable"}
          </Badge>
        </div>
        <h1 className="text-2xl font-bold tracking-tight md:text-3xl">Data Quality</h1>
        <p className="max-w-3xl text-muted-foreground">
          Rules from <code>data/quality/dq_rules.yaml</code> executed against the populated DuckDB.
          Each rule&rsquo;s SQL returns a count of failing rows — zero is a pass. The page tries the
          live FastAPI service at <code>/dq/run</code> first, then falls back to the committed
          snapshot in <code>data/quality/last_run.json</code>.
        </p>
      </header>

      {!report ? (
        <div className="rounded-lg border border-amber-300/50 bg-amber-50/40 p-6 text-sm dark:bg-amber-950/20">
          No DQ report is available. Run <code>python3 scripts/dq_snapshot.py</code> from the repo
          root to generate <code>data/quality/last_run.json</code>, or start the FastAPI service.
        </div>
      ) : (
        <>
          <section>
            <div className="mb-3 flex items-baseline justify-between">
              <h2 className="text-lg font-semibold">Run summary</h2>
              <span className="text-xs text-muted-foreground">
                <Clock className="-mt-0.5 mr-1 inline h-3.5 w-3.5" />
                Run at {report.ran_at}
              </span>
            </div>
            <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
              <Metric label="Total rules" value={report.total_rules} />
              <Metric label="Pass rate" value={`${(report.pass_rate * 100).toFixed(1)}%`} tone={report.pass_rate >= 0.9 ? "good" : report.pass_rate >= 0.75 ? "warn" : "bad"} />
              <Metric label="Passed" value={report.passed} tone="good" />
              <Metric label="Failed" value={report.failed} tone={report.failed ? "bad" : "neutral"} />
              <Metric label="Errored" value={report.errored} tone={report.errored ? "warn" : "neutral"} />
              <Metric label="DuckDB" value={report.duckdb_available ? "available" : "missing"} tone={report.duckdb_available ? "good" : "warn"} />
            </div>
          </section>

          <section className="grid grid-cols-1 gap-4 md:grid-cols-2">
            <div className="rounded-lg border bg-card p-4">
              <h3 className="mb-3 text-sm font-semibold uppercase tracking-wide text-muted-foreground">
                By severity
              </h3>
              <table className="w-full text-sm">
                <thead className="text-left text-xs text-muted-foreground">
                  <tr>
                    <th className="py-1 pr-2">Severity</th>
                    <th className="py-1 pr-2">Passed</th>
                    <th className="py-1 pr-2">Failed</th>
                    <th className="py-1 pr-2">Errored</th>
                  </tr>
                </thead>
                <tbody>
                  {Object.entries(report.by_severity).map(([sev, c]) => (
                    <tr key={sev} className="border-t">
                      <td className="py-1.5 pr-2 font-medium capitalize">{sev}</td>
                      <td className="py-1.5 pr-2">{c.passed}</td>
                      <td className="py-1.5 pr-2 text-red-600 dark:text-red-400">{c.failed}</td>
                      <td className="py-1.5 pr-2 text-amber-600 dark:text-amber-400">{c.errored}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div className="rounded-lg border bg-card p-4">
              <h3 className="mb-3 text-sm font-semibold uppercase tracking-wide text-muted-foreground">
                By subdomain
              </h3>
              <table className="w-full text-sm">
                <thead className="text-left text-xs text-muted-foreground">
                  <tr>
                    <th className="py-1 pr-2">Subdomain</th>
                    <th className="py-1 pr-2">Passed</th>
                    <th className="py-1 pr-2">Failed</th>
                    <th className="py-1 pr-2">Errored</th>
                  </tr>
                </thead>
                <tbody>
                  {Object.entries(report.by_subdomain).map(([sub, c]) => (
                    <tr key={sub} className="border-t">
                      <td className="py-1.5 pr-2 font-medium">{sub}</td>
                      <td className="py-1.5 pr-2">{c.passed}</td>
                      <td className="py-1.5 pr-2 text-red-600 dark:text-red-400">{c.failed}</td>
                      <td className="py-1.5 pr-2 text-amber-600 dark:text-amber-400">{c.errored}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>

          <section>
            <h2 className="mb-3 text-lg font-semibold">Rules</h2>
            <DqRulesTable results={report.results} />
          </section>

          <p className="inline-flex items-center gap-2 text-xs text-muted-foreground">
            <ShieldCheck className="h-3.5 w-3.5" />
            Rules live in <code>data/quality/dq_rules.yaml</code>. Snapshot regenerated by{" "}
            <code>python3 scripts/dq_snapshot.py</code>.
          </p>
        </>
      )}
    </div>
  );
}
