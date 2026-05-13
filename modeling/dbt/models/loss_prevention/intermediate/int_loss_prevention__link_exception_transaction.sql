-- Vault link: exception <-> transaction <-> store <-> employee.
{{ config(materialized='ephemeral') }}

with e as (select * from {{ ref('stg_loss_prevention__pos_exception') }})

select
    md5(coalesce(exception_id, '') || '|' ||
        coalesce(transaction_id, '') || '|' ||
        coalesce(store_id, '') || '|' ||
        coalesce(employee_id, ''))         as l_exception_txn_hk,
    md5(exception_id)                       as h_exception_hk,
    md5(transaction_id)                     as h_transaction_hk,
    md5(store_id)                           as h_store_hk,
    md5(employee_id)                        as h_employee_hk,
    current_date                            as load_date,
    'loss_prevention.pos_exception'         as record_source
from e
where exception_id is not null
