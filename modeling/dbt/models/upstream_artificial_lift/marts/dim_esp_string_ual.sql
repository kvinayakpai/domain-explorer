-- ESP strings with the seal section and its elastomer lot (the E- lot), the part
-- the Field A story turns on.
{{ config(materialized='table') }}

with seal as (
        select
            esp_string_id,
            component_id                                         as seal_component_id,
            nullif(regexp_extract(material_lots, 'E-[0-9]+-[0-9]+'), '') as seal_elastomer_lot
        from {{ ref('stg_upstream_artificial_lift__esp_component') }}
        where component_kind = 'seal'
     )

select
    s.esp_string_id                        as esp_string_key,
    s.model,
    s.built_on,
    seal.seal_component_id,
    seal.seal_elastomer_lot
from {{ ref('stg_upstream_artificial_lift__esp_string') }} s
left join seal using (esp_string_id)
