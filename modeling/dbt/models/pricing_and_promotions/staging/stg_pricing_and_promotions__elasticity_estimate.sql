{{ config(materialized='view') }}

select
    cast(estimate_id                  as varchar)    as estimate_id,
    cast(product_id                   as varchar)    as product_id,
    cast(cluster_id                   as varchar)    as cluster_id,
    cast(own_price_elasticity         as double)     as own_price_elasticity,
    cast(cross_price_elasticity_top1  as double)     as cross_price_elasticity_top1,
    cast(cross_product_id_top1        as varchar)    as cross_product_id_top1,
    cast(confidence_interval_low      as double)     as confidence_interval_low,
    cast(confidence_interval_high     as double)     as confidence_interval_high,
    cast(model_version                as varchar)    as model_version,
    cast(fit_window_start             as date)       as fit_window_start,
    cast(fit_window_end               as date)       as fit_window_end,
    cast(estimated_at                 as timestamp)  as estimated_at
from {{ source('pricing_and_promotions', 'elasticity_estimate') }}
