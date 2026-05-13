{{ config(materialized='ephemeral') }}

select
    {{ dbt_utils.generate_surrogate_key(['location_id']) }}  as hk_location,
    {{ dbt_utils.generate_surrogate_key(['product_id']) }}   as hk_product,
    as_of_ts                                                  as load_dts,
    on_hand_units,
    allocated_units,
    in_transit_units,
    reserved_safety_units,
    atp_units,
    source_system,
    refresh_lag_seconds,
    'omnichannel_oms.inventory_position'                      as record_source
from {{ ref('stg_omnichannel_oms__inventory_positions') }}
