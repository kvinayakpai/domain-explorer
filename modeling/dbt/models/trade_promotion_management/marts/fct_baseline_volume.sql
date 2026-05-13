-- Fact: weekly baseline-volume snapshot per account × SKU × baseline model.
{{ config(materialized='table') }}

with b as (select * from {{ ref('stg_trade_promotion_management__baseline_forecast') }}),
     da as (select * from {{ ref('dim_account_tpm') }}),
     dpr as (select * from {{ ref('dim_product_tpm') }})

select
    b.baseline_id,
    da.account_sk,
    dpr.product_sk,
    cast({{ format_date('b.week_start_date', '%Y%m%d') }} as integer)   as week_date_key,
    b.baseline_units,
    b.baseline_dollars_cents,
    b.confidence_band_low,
    b.confidence_band_high,
    b.model_name,
    b.model_version
from b
left join da on da.account_id = b.account_id
left join dpr on dpr.sku_id   = b.sku_id
