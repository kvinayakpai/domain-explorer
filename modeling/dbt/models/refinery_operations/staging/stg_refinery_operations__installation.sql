{{ config(materialized='view') }}

-- Dated installation of a pump in a position.
select
    cast(installation_id        as varchar ) as installation_id,
    cast(functional_location_id as varchar ) as functional_location_id,
    cast(equipment_id           as varchar ) as equipment_id,
    cast(installed_from         as date    ) as installed_from,
    cast(installed_to           as date    ) as installed_to
from {{ source('refinery_operations', 'installation') }}
