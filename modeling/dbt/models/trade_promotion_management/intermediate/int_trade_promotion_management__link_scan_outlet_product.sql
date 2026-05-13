-- Vault link: Scan-week -> Outlet -> Product.
{{ config(materialized='ephemeral') }}

with src as (
    select outlet_id, sku_id, week_start_date
    from {{ ref('stg_trade_promotion_management__retailer_scan_data') }}
)

select
    md5(coalesce(outlet_id,'')||'|'||coalesce(sku_id,'')||'|'||cast(week_start_date as varchar)) as l_link_hk,
    md5(outlet_id)                                                  as h_outlet_hk,
    md5(sku_id)                                                     as h_product_hk,
    week_start_date,
    current_date                                                    as load_date,
    'trade_promotion_management.retailer_scan_data'                 as record_source
from src
where outlet_id is not null and sku_id is not null
group by outlet_id, sku_id, week_start_date
