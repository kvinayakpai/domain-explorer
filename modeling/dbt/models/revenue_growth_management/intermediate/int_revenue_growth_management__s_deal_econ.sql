-- Vault satellite — deal economic state. Snapshot at deal record time.
{{ config(materialized='ephemeral') }}

select
    {{ dbt_utils.generate_surrogate_key(['deal_id']) }}        as hk_deal,
    cast(start_date as timestamp)                                as load_dts,
    deal_id,
    promo_plan_id,
    account_id,
    pack_id,
    tactic_type,
    mechanic,
    discount_per_unit_cents,
    rebate_pct,
    deal_floor_cents,
    planned_units,
    planned_spend_cents,
    actual_units,
    actual_spend_cents,
    forward_buy_cost_cents,
    start_date,
    end_date,
    settlement_method,
    status,
    'revenue_growth_management.deal'                              as record_source
from {{ ref('stg_revenue_growth_management__deals') }}
