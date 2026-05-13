-- Vault satellite carrying mutable Promotion state.
{{ config(materialized='ephemeral') }}

with src as (select * from {{ ref('stg_trade_promotion_management__promotion') }})

select
    md5(promotion_id)                                                            as h_promotion_hk,
    coalesce(approved_at, created_at, current_timestamp)                         as load_ts,
    md5(coalesce(status,'') || '|' || cast(coalesce(planned_spend_cents,0) as varchar) || '|' ||
        cast(coalesce(planned_volume_units,0) as varchar) || '|' ||
        cast(coalesce(planned_lift_pct,0) as varchar) || '|' ||
        cast(coalesce(forecast_roi,0) as varchar))                               as hashdiff,
    fiscal_year,
    fiscal_quarter,
    start_date,
    end_date,
    ship_start_date,
    ship_end_date,
    status,
    planned_spend_cents,
    planned_volume_units,
    planned_lift_pct,
    forecast_roi,
    'trade_promotion_management.promotion'                                        as record_source
from src
