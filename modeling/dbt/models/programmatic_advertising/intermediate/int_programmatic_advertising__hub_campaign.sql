-- Vault hub for Campaign.
{{ config(materialized='ephemeral') }}

with src as (
    select campaign_id from {{ ref('stg_programmatic_advertising__campaign') }}
    where campaign_id is not null
)

select
    md5(campaign_id)                          as h_campaign_hk,
    campaign_id                               as campaign_bk,
    current_date                              as load_date,
    'programmatic_advertising.campaign'       as record_source
from src
group by campaign_id
