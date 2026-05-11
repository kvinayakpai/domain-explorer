-- Vault hub for Advertiser.
{{ config(materialized='ephemeral') }}

with src as (
    select advertiser_id from {{ ref('stg_programmatic_advertising__advertiser') }}
    where advertiser_id is not null
)

select
    md5(advertiser_id)                          as h_advertiser_hk,
    advertiser_id                               as advertiser_bk,
    current_date                                as load_date,
    'programmatic_advertising.advertiser'       as record_source
from src
group by advertiser_id
