-- Vault link: Campaign → Advertiser.
{{ config(materialized='ephemeral') }}

with src as (
    select campaign_id, advertiser_id from {{ ref('stg_programmatic_advertising__campaign') }}
    where campaign_id is not null and advertiser_id is not null
)

select
    md5(campaign_id || '|' || advertiser_id)  as l_campaign_advertiser_hk,
    md5(campaign_id)                          as h_campaign_hk,
    md5(advertiser_id)                        as h_advertiser_hk,
    current_date                              as load_date,
    'programmatic_advertising.campaign'       as record_source
from src
group by campaign_id, advertiser_id
