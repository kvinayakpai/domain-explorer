{{ config(materialized='view') }}

select
    cast(audit_id                 as varchar)  as audit_id,
    cast(stop_id                  as varchar)  as stop_id,
    cast(outlet_id                as varchar)  as outlet_id,
    cast(audit_date               as date)     as audit_date,
    cast(auditor_id               as varchar)  as auditor_id,
    cast(distribution_score       as double)   as distribution_score,
    cast(share_of_cooler_pct      as double)   as share_of_cooler_pct,
    cast(planogram_compliance_pct as double)   as planogram_compliance_pct,
    cast(price_compliance_pct     as double)   as price_compliance_pct,
    cast(promo_compliance_pct     as double)   as promo_compliance_pct,
    cast(freshness_score          as double)   as freshness_score,
    cast(oos_count                as smallint) as oos_count,
    cast(perfect_store_score      as double)   as perfect_store_score,
    cast(photo_uri                as varchar)  as photo_uri,
    cast(notes                    as varchar)  as notes,
    case when perfect_store_score >= 75 then true else false end as is_above_threshold
from {{ source('direct_store_delivery', 'perfect_store_audit') }}
