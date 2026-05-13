-- Fact — forecast vs actual reconciliation at item-location-customer-period.
-- Powers Forecast Accuracy (MAPE/WAPE) and Bias. Forecasts are matched to
-- their corresponding shipped_units rolled up to the same grain.
{{ config(materialized='table') }}

with f as (
    select item_id, location_id, customer_id, cycle_id, forecast_version,
           period_start, sum(forecast_units) as forecast_units,
           max(published_at) as published_at,
           max(period_grain) as period_grain
    from {{ ref('stg_sop_supply_chain_planning__forecasts') }}
    group by item_id, location_id, customer_id, cycle_id, forecast_version, period_start
),
a as (
    select item_id, location_id, customer_id, period_start,
           sum(shipped_units) as actual_units,
           max(ingested_at)   as actual_ingested_at
    from {{ ref('stg_sop_supply_chain_planning__sales_history') }}
    group by item_id, location_id, customer_id, period_start
),
joined as (
    select
        f.*,
        coalesce(a.actual_units, 0)             as actual_units,
        a.actual_ingested_at
    from f
    left join a
      on a.item_id     = f.item_id
     and a.location_id = f.location_id
     and a.customer_id = f.customer_id
     and a.period_start = f.period_start
),
keyed as (
    select
        joined.*,
        row_number() over (
            order by item_id, location_id, customer_id, cycle_id,
                     forecast_version, period_start
        )                                                                as accuracy_id
    from joined
),
items as (select * from {{ ref('dim_item_sop') }}),
locs  as (select * from {{ ref('dim_location_sop') }}),
custs as (select * from {{ ref('dim_customer_sop') }}),
cycs  as (select * from {{ ref('dim_sop_cycle') }})

select
    k.accuracy_id,
    cast({{ format_date('k.period_start', '%Y%m%d') }} as integer)          as date_key,
    items.item_sk,
    locs.location_sk,
    custs.customer_sk,
    cycs.cycle_sk,
    k.forecast_version,
    k.period_grain,
    k.forecast_units,
    k.actual_units,
    abs(k.forecast_units - k.actual_units)                                   as abs_error_units,
    case when k.actual_units > 0
         then (k.forecast_units - k.actual_units) / k.actual_units
    end                                                                      as pct_error,
    (k.forecast_units - k.actual_units)                                      as bias_units,
    case when k.actual_ingested_at is not null
         then {{ dbt_utils.datediff('k.published_at', 'k.actual_ingested_at', 'day') }}
    end                                                                      as lag_days,
    -- Simplified, single-row MAPE proxy (true MAPE aggregates upstream of this fact).
    case when k.actual_units > 0
         then abs(k.forecast_units - k.actual_units) / k.actual_units
    end                                                                      as mape_lag1,
    case when k.actual_units > 0
         then abs(k.forecast_units - k.actual_units) / k.actual_units
    end                                                                      as wape_lag1
from keyed k
left join items on items.item_id     = k.item_id
left join locs  on locs.location_id  = k.location_id
left join custs on custs.customer_id = k.customer_id
left join cycs  on cycs.cycle_id     = k.cycle_id
