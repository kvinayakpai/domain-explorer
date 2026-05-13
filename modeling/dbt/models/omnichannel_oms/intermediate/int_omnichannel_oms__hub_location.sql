{{ config(materialized='ephemeral') }}

select distinct
    {{ dbt_utils.generate_surrogate_key(['location_id']) }} as hk_location,
    location_id,
    current_timestamp                                       as load_dts,
    'omnichannel_oms.location'                              as record_source
from {{ ref('stg_omnichannel_oms__locations') }}
