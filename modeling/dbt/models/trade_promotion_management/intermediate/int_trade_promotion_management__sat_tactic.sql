-- Vault satellite carrying Tactic descriptive + actuals.
{{ config(materialized='ephemeral') }}

with src as (select * from {{ ref('stg_trade_promotion_management__promo_tactic') }})

select
    md5(tactic_id)                                                               as h_tactic_hk,
    current_timestamp                                                            as load_ts,
    md5(coalesce(tactic_type,'') || '|' || cast(coalesce(discount_per_unit_cents,0) as varchar) || '|' ||
        cast(coalesce(planned_units,0) as varchar) || '|' || cast(coalesce(actual_units,0) as varchar))  as hashdiff,
    tactic_type,
    discount_per_unit_cents,
    consumer_price_cents,
    srp_cents,
    planned_units,
    planned_spend_cents,
    actual_units,
    actual_spend_cents,
    lift_expected_pct,
    feature_type,
    display_type,
    tpr_only,
    settlement_method,
    'trade_promotion_management.promo_tactic'                                     as record_source
from src
