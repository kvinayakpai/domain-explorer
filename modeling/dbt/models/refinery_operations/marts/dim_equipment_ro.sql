-- Pumps with the bearing and seal lots they were built with, and whether the
-- engineering change behind the bearing lot waived the qualification test.
{{ config(materialized='table') }}

with g as (select * from {{ ref('stg_refinery_operations__component_genealogy') }}),
     lots as (select * from {{ ref('stg_refinery_operations__material_lot') }}),
     eco as (select * from {{ ref('stg_refinery_operations__engineering_change') }}),
     bearing as (
        select g.equipment_id, g.lot_id, l.engineering_change_id
        from g join lots l using (lot_id)
        where g.component_kind = 'bearing set'
     ),
     seal as (select equipment_id, lot_id from g where g.component_kind = 'mechanical seal faces')

select
    e.equipment_id                        as equipment_key,
    e.model,
    e.maker_id,
    e.built_on,
    b.lot_id                              as bearing_lot_id,
    b.engineering_change_id               as bearing_lot_change_id,
    coalesce(c.qualification_waived, false) as bearing_lot_waived,
    s.lot_id                              as seal_lot_id
from {{ ref('stg_refinery_operations__equipment') }} e
left join bearing b using (equipment_id)
left join eco c on c.engineering_change_id = b.engineering_change_id
left join seal s using (equipment_id)
