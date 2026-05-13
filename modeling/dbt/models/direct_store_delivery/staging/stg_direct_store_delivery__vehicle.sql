{{ config(materialized='view') }}

select
    cast(vehicle_id          as varchar)  as vehicle_id,
    cast(branch_id           as varchar)  as branch_id,
    cast(asset_tag           as varchar)  as asset_tag,
    cast(vin                 as varchar)  as vin,
    cast(make                as varchar)  as make,
    cast(model               as varchar)  as model,
    cast(year                as smallint) as year,
    cast(vehicle_class       as varchar)  as vehicle_class,
    cast(gvwr_lbs            as integer)  as gvwr_lbs,
    cast(payload_lbs         as integer)  as payload_lbs,
    cast(bay_count           as smallint) as bay_count,
    cast(refrigerated        as boolean)  as refrigerated,
    cast(telematics_provider as varchar)  as telematics_provider,
    cast(ifta_jurisdictions  as varchar)  as ifta_jurisdictions,
    cast(status              as varchar)  as status
from {{ source('direct_store_delivery', 'vehicle') }}
