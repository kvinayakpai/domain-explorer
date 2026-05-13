{{ config(materialized='table') }}

with o as (select * from {{ ref('stg_omnichannel_oms__orders') }}),
     c as (select * from {{ ref('dim_customer_oms') }}),
     l as (select * from {{ ref('dim_location') }}),
     -- Aggregate per-order line counts and split / bopis / sfs flags
     line_agg as (
         select
             order_id,
             count(*)                                       as line_count,
             max(case when is_bopis then 1 else 0 end)::boolean as is_bopis,
             max(case when is_sfs   then 1 else 0 end)::boolean as is_sfs
         from {{ ref('stg_omnichannel_oms__order_lines') }}
         group by order_id
     ),
     -- Split-shipment detection: more than one distinct location per order
     alloc_locs as (
         select
             ol.order_id,
             count(distinct a.location_id) as distinct_locations
         from {{ ref('stg_omnichannel_oms__allocations') }} a
         join {{ ref('stg_omnichannel_oms__order_lines') }} ol on a.order_line_id = ol.order_line_id
         group by ol.order_id
     )

select
    o.order_id,
    cast({{ format_date('o.captured_at', '%Y%m%d') }} as integer) as date_key,
    c.customer_sk,
    l.location_sk                                                  as capture_location_sk,
    o.capture_channel,
    o.order_total_minor,
    o.currency,
    case o.currency
        when 'USD' then o.order_total_minor / 100.0
        when 'EUR' then o.order_total_minor / 100.0 * 1.08
        when 'GBP' then o.order_total_minor / 100.0 * 1.27
        when 'JPY' then o.order_total_minor / 100.0 * 0.0067
        when 'CAD' then o.order_total_minor / 100.0 * 0.74
        when 'AUD' then o.order_total_minor / 100.0 * 0.66
        else o.order_total_minor / 100.0
    end as order_total_usd,
    coalesce(la.line_count, 0)                                     as line_count,
    coalesce(la.is_bopis, false)                                   as is_bopis,
    coalesce(la.is_sfs, false)                                     as is_sfs,
    case when coalesce(al.distinct_locations, 1) > 1 then true else false end as is_split_shipment,
    o.is_cancelled,
    o.is_returned,
    o.promise_delivery_ts,
    o.captured_at,
    o.closed_at,
    o.cycle_time_hours
from o
left join c          on c.customer_id = o.customer_id
left join l          on l.location_id = o.capture_location_id
left join line_agg la on la.order_id  = o.order_id
left join alloc_locs al on al.order_id = o.order_id
