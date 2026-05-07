/**
 * Derive Vault and Dimensional ERDs from the canonical 3NF model declared in
 * the YAML (`subdomain.dataModel.entities`).
 *
 * The mapping is intentionally rule-based and deterministic so a single ERD
 * component can render all three styles without subdomain-specific code:
 *
 *   3NF        → as-is.
 *   Vault      → for every entity:
 *                  - one HUB (business key columns)
 *                  - one SAT (descriptive non-key columns)
 *                  - one LINK per outgoing FK (collapsed if multiple FKs to
 *                    the same target)
 *   Dimensional → entities containing measure-like attributes (numerics with
 *                 names ending in _amount/_qty/_count/_minor/etc.) become
 *                 fact_<entity>; everything else becomes dim_<entity>.
 */
import type { Entity, EntityAttribute, EntityRelationship } from "@domain-explorer/metadata";

export type ModelStyle = "3nf" | "vault" | "dim";

export interface ErdEntity {
  name: string;
  attributes: EntityAttribute[];
  description?: string;
}

export interface ErdRelationship {
  from: string;
  to: string;
  via?: string;
  kind: "one_to_one" | "one_to_many" | "many_to_many";
}

export interface ErdGraph {
  entities: ErdEntity[];
  relationships: ErdRelationship[];
}

const MEASURE_HINTS = [
  "_amount",
  "_amt",
  "_qty",
  "_quantity",
  "_count",
  "_minor",
  "_revenue",
  "_total",
  "amount_minor",
  "_units",
  "_sold",
  "_score",
  "_pct",
];

function isMeasureCol(name: string): boolean {
  const n = name.toLowerCase();
  return MEASURE_HINTS.some((h) => n.endsWith(h) || n.includes(h));
}

function isFactEntity(e: Entity): boolean {
  // Tables that look like transactions/snapshots become facts.
  const measureCount = (e.attributes ?? []).filter((a) => isMeasureCol(a.name)).length;
  return measureCount >= 1 && (e.attributes ?? []).some((a) => /_(at|ts|date)$/.test(a.name));
}

function buildRelationships(entities: Entity[]): ErdRelationship[] {
  const out: ErdRelationship[] = [];
  for (const e of entities) {
    // explicit relationships from YAML take precedence
    for (const r of e.relationships ?? []) {
      out.push({ from: e.name, to: r.to, via: r.via, kind: r.kind });
    }
    // also derive from FK attributes for entities that don't list relationships
    for (const a of e.attributes ?? []) {
      if (a.isForeignKey && a.references) {
        const target = a.references.split(".")[0];
        if (
          target &&
          !out.some((r) => r.from === e.name && r.to === target && r.via === a.name)
        ) {
          out.push({
            from: e.name,
            to: target,
            via: a.name,
            kind: "one_to_many",
          });
        }
      }
    }
  }
  // Deduplicate
  const seen = new Set<string>();
  return out.filter((r) => {
    const key = `${r.from}|${r.to}|${r.via ?? ""}|${r.kind}`;
    if (seen.has(key)) return false;
    seen.add(key);
    return true;
  });
}

export function buildThreeNfGraph(entities: Entity[]): ErdGraph {
  return {
    entities: entities.map((e) => ({
      name: e.name,
      description: e.description,
      attributes: e.attributes ?? [],
    })),
    relationships: buildRelationships(entities),
  };
}

export function buildVaultGraph(entities: Entity[]): ErdGraph {
  const erdEntities: ErdEntity[] = [];
  const rels: ErdRelationship[] = [];
  for (const e of entities) {
    const pks = (e.attributes ?? []).filter((a) => a.isPrimaryKey);
    const fks = (e.attributes ?? []).filter((a) => a.isForeignKey && a.references);
    const descCols = (e.attributes ?? []).filter(
      (a) => !a.isPrimaryKey && !a.isForeignKey,
    );
    const hub: ErdEntity = {
      name: `hub_${e.name}`,
      description: `Hub of ${e.name}`,
      attributes: [
        { name: `${e.name}_hk`, type: "bytea", isPrimaryKey: true },
        ...pks.map((a) => ({ ...a, isPrimaryKey: false, name: `${a.name}_bk`, type: a.type })),
        { name: "load_dts", type: "timestamp" },
        { name: "rec_src", type: "varchar" },
      ],
    };
    erdEntities.push(hub);
    if (descCols.length > 0) {
      const sat: ErdEntity = {
        name: `sat_${e.name}`,
        description: `Descriptive satellite for ${e.name}`,
        attributes: [
          {
            name: `${e.name}_hk`,
            type: "bytea",
            isPrimaryKey: true,
            isForeignKey: true,
            references: `hub_${e.name}.${e.name}_hk`,
          },
          { name: "load_dts", type: "timestamp", isPrimaryKey: true },
          { name: "load_end_dts", type: "timestamp" },
          { name: "hash_diff", type: "bytea" },
          ...descCols.slice(0, 12),
          { name: "rec_src", type: "varchar" },
        ],
      };
      erdEntities.push(sat);
      rels.push({
        from: `sat_${e.name}`,
        to: `hub_${e.name}`,
        via: `${e.name}_hk`,
        kind: "one_to_many",
      });
    }
    for (const fk of fks) {
      const target = fk.references!.split(".")[0]!;
      const linkName = `link_${e.name}_${target}`;
      if (!erdEntities.some((x) => x.name === linkName)) {
        erdEntities.push({
          name: linkName,
          description: `Link ${e.name} ↔ ${target}`,
          attributes: [
            { name: "link_hk", type: "bytea", isPrimaryKey: true },
            {
              name: `${e.name}_hk`,
              type: "bytea",
              isForeignKey: true,
              references: `hub_${e.name}.${e.name}_hk`,
            },
            {
              name: `${target}_hk`,
              type: "bytea",
              isForeignKey: true,
              references: `hub_${target}.${target}_hk`,
            },
            { name: "load_dts", type: "timestamp" },
            { name: "rec_src", type: "varchar" },
          ],
        });
        rels.push({
          from: linkName,
          to: `hub_${e.name}`,
          via: `${e.name}_hk`,
          kind: "one_to_many",
        });
        rels.push({
          from: linkName,
          to: `hub_${target}`,
          via: `${target}_hk`,
          kind: "one_to_many",
        });
      }
    }
  }
  return { entities: erdEntities, relationships: rels };
}

export function buildDimGraph(entities: Entity[]): ErdGraph {
  const erdEntities: ErdEntity[] = [];
  const rels: ErdRelationship[] = [];
  // Always provide a date dimension.
  erdEntities.push({
    name: "dim_date",
    description: "Conformed date dimension",
    attributes: [
      { name: "date_key", type: "integer", isPrimaryKey: true },
      { name: "date_actual", type: "date" },
      { name: "day_of_week", type: "smallint" },
      { name: "month", type: "smallint" },
      { name: "year", type: "smallint" },
      { name: "fiscal_quarter", type: "varchar(8)" },
    ],
  });
  for (const e of entities) {
    if (isFactEntity(e)) {
      const fact: ErdEntity = {
        name: `fact_${e.name}`,
        description: `Fact derived from ${e.name}`,
        attributes: [
          { name: "date_key", type: "integer", isForeignKey: true, references: "dim_date.date_key" },
          ...(e.attributes ?? [])
            .filter((a) => a.isForeignKey)
            .map((a) => ({
              name: `${a.references!.split(".")[0]}_key`,
              type: "bigint",
              isForeignKey: true,
              references: `dim_${a.references!.split(".")[0]}.${a.references!.split(".")[0]}_key`,
            })),
          ...(e.attributes ?? [])
            .filter((a) => isMeasureCol(a.name))
            .map((a) => ({ name: a.name, type: a.type })),
          { name: "row_count", type: "bigint" },
        ],
      };
      erdEntities.push(fact);
      rels.push({ from: fact.name, to: "dim_date", via: "date_key", kind: "one_to_many" });
      for (const a of (e.attributes ?? []).filter((a) => a.isForeignKey)) {
        const target = a.references!.split(".")[0]!;
        const dimName = `dim_${target}`;
        rels.push({
          from: fact.name,
          to: dimName,
          via: `${target}_key`,
          kind: "one_to_many",
        });
      }
    } else {
      const descCols = (e.attributes ?? []).filter((a) => !a.isPrimaryKey);
      erdEntities.push({
        name: `dim_${e.name}`,
        description: `SCD2 dimension for ${e.name}`,
        attributes: [
          { name: `${e.name}_key`, type: "bigint", isPrimaryKey: true },
          ...(e.attributes ?? [])
            .filter((a) => a.isPrimaryKey)
            .map((a) => ({ ...a, isPrimaryKey: false, name: `${a.name}` })),
          ...descCols.slice(0, 12),
          { name: "valid_from", type: "timestamp" },
          { name: "valid_to", type: "timestamp" },
          { name: "is_current", type: "boolean" },
        ],
      });
    }
  }
  // Drop dim entries that have no inbound fact reference and aren't dim_date — keeps the diagram readable.
  const referenced = new Set<string>(rels.map((r) => r.to));
  return {
    entities: erdEntities.filter(
      (e) =>
        e.name === "dim_date" ||
        e.name.startsWith("fact_") ||
        referenced.has(e.name),
    ),
    relationships: rels,
  };
}

export function buildErd(style: ModelStyle, entities: Entity[]): ErdGraph {
  if (style === "vault") return buildVaultGraph(entities);
  if (style === "dim") return buildDimGraph(entities);
  return buildThreeNfGraph(entities);
}

export function styleLabel(style: ModelStyle): string {
  if (style === "vault") return "Data Vault 2.0";
  if (style === "dim") return "Dimensional (Star)";
  return "3NF (Operational)";
}
