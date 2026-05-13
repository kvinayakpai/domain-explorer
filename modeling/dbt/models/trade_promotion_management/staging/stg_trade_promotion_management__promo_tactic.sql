{{ config(materialized='view') }}

select
    cast(tactic_id                as varchar) as tactic_id,
    cast(promotion_id             as varchar) as promotion_id,
    cast(sku_id                   as varchar) as sku_id,
    cast(tactic_type              as varchar) as tactic_type,
    cast(discount_per_unit_cents  as bigint)  as discount_per_unit_cents,
    cast(consumer_price_cents     as bigint)  as consumer_price_cents,
    cast(srp_cents                as bigint)  as srp_cents,
    cast(planned_units            as bigint)  as planned_units,
    cast(planned_spend_cents      as bigint)  as planned_spend_cents,
    cast(actual_units             as bigint)  as actual_units,
    cast(actual_spend_cents       as bigint)  as actual_spend_cents,
    cast(lift_expected_pct        as double)  as lift_expected_pct,
    cast(feature_type             as varchar) as feature_type,
    cast(display_type             as varchar) as display_type,
    cast(tpr_only                 as boolean) as tpr_only,
    cast(settlement_method        as varchar) as settlement_method
from {{ source('trade_promotion_management', 'promo_tactic') }}
