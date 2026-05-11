-- Vault hub for Creative.
{{ config(materialized='ephemeral') }}

with src as (
    select creative_id from {{ ref('stg_programmatic_advertising__creative') }}
    where creative_id is not null
)

select
    md5(creative_id)                          as h_creative_hk,
    creative_id                               as creative_bk,
    current_date                              as load_date,
    'programmatic_advertising.creative'       as record_source
from src
group by creative_id
