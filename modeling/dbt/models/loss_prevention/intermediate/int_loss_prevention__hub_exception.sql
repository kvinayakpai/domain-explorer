-- Vault hub for POS exceptions.
{{ config(materialized='ephemeral') }}

with src as (
    select exception_id
    from {{ ref('stg_loss_prevention__pos_exception') }}
    where exception_id is not null
)

select
    md5(exception_id)                   as h_exception_hk,
    exception_id                        as exception_bk,
    current_date                        as load_date,
    'loss_prevention.pos_exception'     as record_source
from src
group by exception_id
