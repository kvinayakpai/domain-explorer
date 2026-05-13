-- Vault link: RMA ↔ Order ↔ Customer.
{{ config(materialized='ephemeral') }}

select
    md5(concat_ws('|', rma_id, order_id, customer_id))  as hk_link,
    md5(rma_id)                                          as hk_rma,
    md5(order_id)                                        as hk_order,
    md5(customer_id)                                     as hk_customer,
    issued_ts                                            as load_dts,
    'returns_reverse_logistics.return_authorization'     as record_source
from {{ ref('stg_returns_reverse_logistics__return_authorizations') }}
