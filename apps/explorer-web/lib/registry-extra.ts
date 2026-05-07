// Re-exports the registry plus the new KPI helpers from
// @domain-explorer/metadata. Kept separate so server-only callers can import
// without dragging unused server-side modules.
import "server-only";
export { registry, VERTICALS } from "./registry";
export { getKpiMaster, getKpiSql } from "@domain-explorer/metadata";
