-- Vault link: Creative → Campaign + Advertiser.
{{ config(materialized='ephemeral') }}

with src as (
    select creative_id, campaign_id, advertiser_id
    from {{ ref('stg_programmatic_advertising__creative') }}
    where creative_id is not null
)

select
    md5(creative_id || '|' || coalesce(campaign_id,'') || '|' || coalesce(advertiser_id,'')) as l_creative_campaign_hk,
    md5(creative_id)                            as h_creative_hk,
    case when campaign_id   is null then null else md5(campaign_id)   end as h_campaign_hk,
    case when advertiser_id is null then null else md5(advertiser_id) end as h_advertiser_hk,
    current_date                                as load_date,
    'programmatic_advertising.creative'         as record_source
from src
group by creative_id, campaign_id, advertiser_id
