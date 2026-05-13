{{ config(materialized='view') }}

select
    cast(planogram_id     as varchar)    as planogram_id,
    cast(category_id      as varchar)    as category_id,
    cast(cluster_id       as varchar)    as cluster_id,
    cast(version          as varchar)    as version,
    cast(effective_from   as date)       as effective_from,
    cast(effective_to     as date)       as effective_to,
    cast(total_linear_ft  as double)     as total_linear_ft,
    cast(total_facings    as integer)    as total_facings,
    cast(total_sku_count  as integer)    as total_sku_count,
    cast(authoring_system as varchar)    as authoring_system,
    cast(created_by       as varchar)    as created_by,
    cast(created_at       as timestamp)  as created_at,
    cast(approved_at      as timestamp)  as approved_at,
    cast(status           as varchar)    as status
from {{ source('category_management', 'planogram') }}
