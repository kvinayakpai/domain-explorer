-- Vault hub for the Asset business key.
{{ config(materialized='ephemeral') }}

with src as (
    select asset_id, tag_id
    from {{ ref('stg_predictive_maintenance__asset') }}
    where asset_id is not null
)

select
    md5(asset_id)                       as h_asset_hk,
    asset_id                            as asset_bk,
    max(tag_id)                         as tag_id,
    current_date                        as load_date,
    'predictive_maintenance.asset'      as record_source
from src
group by asset_id
