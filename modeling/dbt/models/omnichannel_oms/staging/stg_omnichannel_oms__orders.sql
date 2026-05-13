{{ config(materialized='view') }}

select
    cast(order_id               as varchar)    as order_id,
    cast(customer_id            as varchar)    as customer_id,
    cast(capture_channel        as varchar)    as capture_channel,
    cast(capture_location_id    as varchar)    as capture_location_id,
    cast(order_total_minor      as bigint)     as order_total_minor,
    upper(currency)                              as currency,
    cast(tax_minor              as bigint)     as tax_minor,
    cast(shipping_minor         as bigint)     as shipping_minor,
    cast(discount_minor         as bigint)     as discount_minor,
    cast(payment_status         as varchar)    as payment_status,
    cast(order_status           as varchar)    as order_status,
    cast(promise_delivery_ts    as timestamp)  as promise_delivery_ts,
    cast(captured_at            as timestamp)  as captured_at,
    cast(closed_at              as timestamp)  as closed_at,
    case when capture_channel in ('store_pos','kiosk') then true else false end as is_store_captured,
    case when order_status = 'cancelled'  then true else false end as is_cancelled,
    case when order_status = 'returned'   then true else false end as is_returned,
    case
        when closed_at is not null and captured_at is not null
            then {{ dbt_utils.datediff('captured_at', 'closed_at', 'hour') }}
    end as cycle_time_hours
from {{ source('omnichannel_oms', 'oms_order') }}
