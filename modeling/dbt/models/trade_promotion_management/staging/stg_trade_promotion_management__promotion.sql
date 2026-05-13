{{ config(materialized='view') }}

select
    cast(promotion_id         as varchar)   as promotion_id,
    cast(account_id           as varchar)   as account_id,
    cast(name                 as varchar)   as name,
    cast(fiscal_year          as smallint)  as fiscal_year,
    cast(fiscal_quarter       as smallint)  as fiscal_quarter,
    cast(start_date           as date)      as start_date,
    cast(end_date             as date)      as end_date,
    cast(ship_start_date      as date)      as ship_start_date,
    cast(ship_end_date        as date)      as ship_end_date,
    cast(status               as varchar)   as status,
    cast(planned_spend_cents  as bigint)    as planned_spend_cents,
    cast(planned_volume_units as bigint)    as planned_volume_units,
    cast(planned_lift_pct     as double)    as planned_lift_pct,
    cast(forecast_roi         as double)    as forecast_roi,
    cast(created_by           as varchar)   as created_by,
    cast(created_at           as timestamp) as created_at,
    cast(approved_at          as timestamp) as approved_at
from {{ source('trade_promotion_management', 'promotion') }}
