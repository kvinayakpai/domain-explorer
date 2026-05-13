{{ config(materialized='ephemeral') }}

with stops as (select * from {{ ref('stg_direct_store_delivery__stop') }})

select
    md5(coalesce(stop_id,'') || '|' || coalesce(outlet_id,'')) as h_link_hk,
    md5(stop_id)                                               as h_stop_hk,
    md5(outlet_id)                                             as h_outlet_hk,
    current_date                                               as load_date,
    'direct_store_delivery.stop'                               as record_source
from stops
where stop_id is not null and outlet_id is not null
