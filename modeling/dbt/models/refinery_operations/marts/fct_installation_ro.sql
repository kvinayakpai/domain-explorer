-- One row per pump installed in a position for a period. Installed days run to the
-- as-of date while the pump is still in place; failures are counted per installation.
{{ config(materialized='table') }}

with i as (select * from {{ ref('int_refinery_operations__link_installation') }}),
     f as (
        select installation_id, count(*) as failure_count
        from {{ ref('stg_refinery_operations__failure_event') }}
        group by 1
     )

select
    i.installation_id,
    l.functional_location_id              as functional_location_key,
    l.equipment_id                        as equipment_key,
    i.installed_from,
    i.installed_to,
    date_diff('day', i.installed_from,
              coalesce(i.installed_to, cast('{{ var("ftf_as_of") }}' as date)))  as installed_days,
    coalesce(f.failure_count, 0)          as failure_count
from i
join {{ ref('stg_refinery_operations__installation') }} l using (installation_id)
left join f using (installation_id)
