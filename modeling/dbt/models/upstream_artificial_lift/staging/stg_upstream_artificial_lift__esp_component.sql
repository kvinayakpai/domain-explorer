{{ config(materialized='view') }}

-- Components of each string with their material lots.
select
    cast(component_id   as varchar ) as component_id,
    cast(esp_string_id  as varchar ) as esp_string_id,
    cast(component_kind as varchar ) as component_kind,
    cast(built_on       as date    ) as built_on,
    cast(material_lots  as varchar ) as material_lots
from {{ source('upstream_artificial_lift', 'esp_component') }}
