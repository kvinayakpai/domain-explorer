-- CSD (Central Securities Depository) dimension distilled from trades + confirmations.
{{ config(materialized='table') }}

with ids as (
    select distinct csd_id from {{ ref('stg_settlement_clearing__trade') }}                 where csd_id is not null
    union
    select distinct csd_id from {{ ref('stg_settlement_clearing__settlement_confirmation') }} where csd_id is not null
)

select
    md5(csd_id)                                       as csd_key,
    csd_id,
    'CSD '  || csd_id                                 as name,
    case when csd_id like 'CSD001' then 'US'
         when csd_id like 'CSD002' then 'GB'
         when csd_id like 'CSD003' then 'DE'
         when csd_id like 'CSD004' then 'JP'
         when csd_id like 'CSD005' then 'FR'
         else null
    end                                                as country_iso,
    true                                               as is_current
from ids
