{{ config(materialized='view') }}

select
    cast(promo_plan_id              as varchar)   as promo_plan_id,
    cast(account_id                 as varchar)   as account_id,
    cast(name                       as varchar)   as name,
    cast(brand                      as varchar)   as brand,
    cast(fiscal_year                as smallint)  as fiscal_year,
    cast(fiscal_quarter             as smallint)  as fiscal_quarter,
    cast(planned_net_revenue_cents  as bigint)    as planned_net_revenue_cents,
    cast(planned_trade_spend_cents  as bigint)    as planned_trade_spend_cents,
    cast(planned_volume_units       as bigint)    as planned_volume_units,
    cast(forecast_roi               as double)    as forecast_roi,
    cast(status                     as varchar)   as status,
    cast(created_by                 as varchar)   as created_by,
    cast(created_at                 as timestamp) as created_at,
    cast(approved_at                as timestamp) as approved_at
from {{ source('revenue_growth_management', 'promo_plan') }}
