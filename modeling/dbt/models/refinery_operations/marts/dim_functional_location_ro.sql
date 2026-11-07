-- Positions with their site. The B pump of a pair is the installed spare.
{{ config(materialized='table') }}

select
    f.functional_location_id              as functional_location_key,
    f.floc_code,
    f.tag,
    f.site_id,
    s.site_name,
    f.process_unit,
    f.service,
    f.api_610_type,
    f.train_letter,
    f.spare_of is not null                as is_installed_spare
from {{ ref('stg_refinery_operations__functional_location') }} f
join {{ ref('stg_refinery_operations__site') }} s using (site_id)
