{{ config(materialized='view') }}

select
    cast(audit_id            as varchar) as audit_id,
    cast(store_id            as varchar) as store_id,
    cast(planogram_id        as varchar) as planogram_id,
    cast(audit_date          as date)    as audit_date,
    cast(positions_audited   as integer) as positions_audited,
    cast(positions_compliant as integer) as positions_compliant,
    cast(missing_facings     as integer) as missing_facings,
    cast(out_of_stock_count  as integer) as out_of_stock_count,
    cast(misplaced_sku_count as integer) as misplaced_sku_count,
    cast(extra_sku_count     as integer) as extra_sku_count,
    cast(compliance_score    as double)  as compliance_score,
    cast(source              as varchar) as source,
    cast(photo_evidence_uri  as varchar) as photo_evidence_uri
from {{ source('category_management', 'planogram_compliance_audit') }}
