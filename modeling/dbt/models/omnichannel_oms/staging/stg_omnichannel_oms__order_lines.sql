{{ config(materialized='view') }}

select
    cast(order_line_id              as varchar)    as order_line_id,
    cast(order_id                   as varchar)    as order_id,
    cast(product_id                 as varchar)    as product_id,
    cast(line_number                as smallint)   as line_number,
    cast(quantity                   as integer)    as quantity,
    cast(unit_price_minor           as bigint)     as unit_price_minor,
    cast(line_total_minor           as bigint)     as line_total_minor,
    cast(fulfillment_method         as varchar)    as fulfillment_method,
    cast(requested_location_id      as varchar)    as requested_location_id,
    cast(line_status                as varchar)    as line_status,
    cast(substitution_for_line_id   as varchar)    as substitution_for_line_id,
    case when fulfillment_method in ('bopis','curbside') then true else false end as is_bopis,
    case when fulfillment_method = 'sfs'                 then true else false end as is_sfs,
    case when line_status = 'substituted'                then true else false end as is_substituted,
    case when line_status = 'cancelled'                  then true else false end as is_cancelled,
    case when line_status in ('picked','packed','shipped','delivered','picked_up')
         then true else false end as is_first_pick_filled
from {{ source('omnichannel_oms', 'order_line') }}
