-- Vault link tying range-review outcomes to SKUs.
{{ config(materialized='ephemeral') }}

with src as (
    select decision_id, range_review_id, sku_id, decision_type, rationale
    from {{ ref('stg_category_management__range_review_decisions') }}
    where range_review_id is not null and sku_id is not null
)

select
    md5(decision_id)                                              as l_range_decision_hk,
    md5(range_review_id)                                          as h_range_review_hk,
    md5(sku_id)                                                   as h_sku_hk,
    decision_id,
    decision_type,
    rationale,
    current_date                                                   as load_date,
    'category_management.range_review_decision'                    as record_source
from src
