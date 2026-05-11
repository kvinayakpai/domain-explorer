-- CCP dimension distilled from trades.
{{ config(materialized='table') }}

with ids as (
    select distinct ccp_id from {{ ref('stg_settlement_clearing__trade') }} where ccp_id is not null
)

select
    md5(ccp_id)                  as ccp_key,
    ccp_id,
    'CCP ' || ccp_id             as name,
    true                         as is_current
from ids
