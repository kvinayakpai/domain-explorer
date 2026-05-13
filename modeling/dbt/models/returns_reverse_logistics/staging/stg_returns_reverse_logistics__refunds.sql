{{ config(materialized='view') }}

select
    cast(refund_id                       as varchar)    as refund_id,
    cast(rma_id                          as varchar)    as rma_id,
    cast(order_id                        as varchar)    as order_id,
    cast(customer_id                     as varchar)    as customer_id,
    cast(refund_type                     as varchar)    as refund_type,
    cast(refund_amount_minor             as bigint)     as refund_amount_minor,
    upper(currency)                                       as currency,
    cast(restocking_fee_collected_minor  as bigint)     as restocking_fee_collected_minor,
    cast(issued_ts                       as timestamp)  as issued_ts,
    cast(psp_refund_id                   as varchar)    as psp_refund_id,
    cast(payment_rail                    as varchar)    as payment_rail,
    cast(status                          as varchar)    as status,
    case when refund_type = 'returnless' then true else false end as is_returnless,
    case when status = 'issued' then true else false end as is_issued
from {{ source('returns_reverse_logistics', 'refund') }}
