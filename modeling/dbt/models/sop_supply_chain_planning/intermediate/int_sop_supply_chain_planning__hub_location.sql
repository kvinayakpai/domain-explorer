-- Vault hub for the Location business key (GS1 GLN where assigned).
{{ config(materialized='ephemeral') }}

with src as (
    select location_id, gln
    from {{ ref('stg_sop_supply_chain_planning__locations') }}
    where location_id is not null
)

select
    md5(location_id)                          as h_location_hk,
    location_id                                as location_bk,
    max(gln)                                   as gln,
    current_date                               as load_date,
    'sop_supply_chain_planning.location'       as record_source
from src
group by location_id
