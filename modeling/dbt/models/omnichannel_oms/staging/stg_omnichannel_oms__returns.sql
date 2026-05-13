{{ config(materialized='view') }}

select
    cast(rma_id                as varchar)    as rma_id,
    cast(order_id              as varchar)    as order_id,
    cast(customer_id           as varchar)    as customer_id,
    cast(return_reason         as varchar)    as return_reason,
    cast(return_method         as varchar)    as return_method,
    cast(return_location_id    as varchar)    as return_location_id,
    cast(refund_method         as varchar)    as refund_method,
    cast(refund_amount_minor   as bigint)     as refund_amount_minor,
    cast(restock_outcome       as varchar)    as restock_outcome,
    cast(initiated_at          as timestamp)  as initiated_at,
    cast(received_at           as timestamp)  as received_at,
    cast(refund_issued_at      as timestamp)  as refund_issued_at,
    cast(status                as varchar)    as status,
    case when status = 'refunded' then true else false end as is_refunded,
    case
        when refund_issued_at is not null and initiated_at is not null
            then {{ dbt_utils.datediff('initiated_at', 'refund_issued_at', 'day') }}
    end as return_cycle_days
from {{ source('omnichannel_oms', 'return_authorization') }}
