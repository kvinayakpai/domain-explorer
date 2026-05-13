{{ config(materialized='view') }}

select
    cast(transaction_id         as varchar)    as transaction_id,
    cast(store_id               as varchar)    as store_id,
    cast(register_id            as varchar)    as register_id,
    cast(employee_id            as varchar)    as employee_id,
    cast(customer_ref_hash      as varchar)    as customer_ref_hash,
    cast(txn_ts                 as timestamp)  as txn_ts,
    cast(tender_type            as varchar)    as tender_type,
    cast(gross_amount_minor     as bigint)     as gross_amount_minor,
    cast(discount_amount_minor  as bigint)     as discount_amount_minor,
    cast(refund_amount_minor    as bigint)     as refund_amount_minor,
    cast(net_amount_minor       as bigint)     as net_amount_minor,
    cast(item_count             as integer)    as item_count,
    cast(void_flag              as boolean)    as void_flag,
    cast(no_sale_flag           as boolean)    as no_sale_flag
from {{ source('loss_prevention', 'pos_transaction') }}
