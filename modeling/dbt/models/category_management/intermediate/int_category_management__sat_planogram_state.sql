-- Vault satellite carrying mutable Planogram state (version, status, totals).
{{ config(materialized='ephemeral') }}

with src as (select * from {{ ref('stg_category_management__planograms') }})

select
    md5(planogram_id)                                                                 as h_planogram_hk,
    coalesce(created_at, current_timestamp)                                            as load_ts,
    md5(coalesce(version,'') || '|' || coalesce(status,'') || '|' ||
        cast(coalesce(total_facings,0) as varchar) || '|' ||
        cast(coalesce(total_sku_count,0) as varchar))                                  as hashdiff,
    category_id,
    cluster_id,
    version,
    effective_from,
    effective_to,
    total_linear_ft,
    total_facings,
    total_sku_count,
    authoring_system,
    status,
    'category_management.planogram'                                                    as record_source
from src
