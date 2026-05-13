{{ config(materialized='view') }}

select
    cast(promo_line_id          as varchar)  as promo_line_id,
    cast(promo_id               as varchar)  as promo_id,
    cast(product_id             as varchar)  as product_id,
    cast(store_id               as varchar)  as store_id,
    cast(planned_baseline_units as integer)  as planned_baseline_units,
    cast(planned_lift_pct       as double)   as planned_lift_pct,
    cast(planned_funding_minor  as bigint)   as planned_funding_minor,
    cast(actual_units           as integer)  as actual_units,
    cast(actual_funding_minor   as bigint)   as actual_funding_minor,
    cast(cannibalization_flag   as boolean)  as cannibalization_flag,
    case
        when planned_baseline_units > 0
        then cast((actual_units - planned_baseline_units) as double) / planned_baseline_units
        else null
    end                                       as actual_lift_pct
from {{ source('pricing_and_promotions', 'promo_line') }}
