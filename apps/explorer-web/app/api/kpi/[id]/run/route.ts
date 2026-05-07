import { NextResponse } from "next/server";
import { registry, getKpiSql } from "@/lib/registry-extra";
import { queryRows } from "@/lib/db";

export const dynamic = "force-dynamic";

/**
 * POST /api/kpi/[id]/run
 * Body: { style: '3nf' | 'vault' | 'dim', since?: string }
 *
 * Returns the SQL it executed plus the resulting rows (JSON-serialised).
 * Only KPIs that have a non-stub implementation in data/kpis/sql.yaml will
 * actually run — stubs return a 400 so the UI can show a "no real SQL yet"
 * hint without misleading the user.
 */
export async function POST(
  req: Request,
  { params }: { params: { id: string } },
) {
  const body = (await req.json().catch(() => ({}))) as {
    style?: string;
    since?: string;
  };
  const style = body.style ?? "3nf";
  const since = body.since;
  const reg = registry();
  const spec = getKpiSql(reg, params.id);
  if (!spec) {
    return NextResponse.json({ error: "no SQL spec for KPI" }, { status: 404 });
  }
  const sqlKey: "threeNF" | "vault" | "dimensional" =
    style === "vault" ? "vault" : style === "dim" ? "dimensional" : "threeNF";
  const sqlRaw = (spec as Record<string, string | undefined>)[sqlKey];
  if (!sqlRaw || sqlRaw.trim().startsWith("--") || /TODO/i.test(sqlRaw)) {
    return NextResponse.json(
      {
        error:
          "no executable SQL for this KPI/style yet — only the 17 anchor subdomain KPIs ship real implementations",
      },
      { status: 400 },
    );
  }
  // Naive :since parameter substitution. We don't use prepared params because
  // DuckDB driver here is read-only and the value is server-side only — but
  // we still validate the shape.
  let sql = sqlRaw;
  if (sql.includes(":since")) {
    const safe =
      since && /^\d{4}-\d{2}-\d{2}/.test(since)
        ? since.slice(0, 19)
        : "1900-01-01T00:00:00";
    sql = sql.replaceAll(":since", `'${safe}'`);
  }
  try {
    const rows = await queryRows(sql);
    return NextResponse.json({ sql, rows });
  } catch (e) {
    return NextResponse.json(
      { error: (e as Error).message, sql },
      { status: 500 },
    );
  }
}
