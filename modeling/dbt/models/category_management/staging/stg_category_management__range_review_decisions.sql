{{ config(materialized='view') }}

select
    cast(decision_id        as varchar)   as decision_id,
    cast(range_review_id    as varchar)   as range_review_id,
    cast(sku_id             as varchar)   as sku_id,
    cast(decision_type      as varchar)   as decision_type,
    cast(cluster_scope      as varchar)   as cluster_scope,
    cast(rationale          as varchar)   as rationale,
    cast(confidence         as double)    as confidence,
    cast(decision_authority as varchar)   as decision_authority,
    cast(decided_at         as timestamp) as decided_at
from {{ source('category_management', 'range_review_decision') }}
