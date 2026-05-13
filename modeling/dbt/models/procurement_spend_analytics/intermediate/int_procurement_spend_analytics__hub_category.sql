-- Vault hub for the UNSPSC category business key.
{{ config(materialized='ephemeral') }}

select
    md5(category_code)                                  as h_category_hk,
    category_code                                       as category_bk,
    current_date                                        as load_date,
    'procurement_spend_analytics.category_taxonomy'     as record_source
from {{ ref('stg_procurement_spend_analytics__category_taxonomy') }}
where category_code is not null
group by category_code
