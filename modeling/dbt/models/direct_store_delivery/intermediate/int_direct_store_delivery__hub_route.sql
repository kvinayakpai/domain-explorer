-- Vault hub for the Route business key.
{{ config(materialized='ephemeral') }}

with src as (
    select route_id from {{ ref('stg_direct_store_delivery__route') }}
    where route_id is not null
)

select
    md5(route_id)                       as h_route_hk,
    route_id                            as route_bk,
    current_date                        as load_date,
    'direct_store_delivery.route'       as record_source
from src
group by route_id
