-- ref.kpi.bad_actor_count: positions with two or more failures in the 365 days
-- before the as-of date, whichever pump was installed at the time.
{{ config(materialized='table') }}

select
    f.functional_location_key,
    d.tag,
    d.site_name,
    d.service,
    count(*)                                   as failures_last_365d,
    count(distinct f.equipment_key)            as distinct_pumps,
    string_agg(distinct f.iso14224_failure_mode, ', ') as failure_modes
from {{ ref('fct_failure_ro') }} f
join {{ ref('dim_functional_location_ro') }} d using (functional_location_key)
where f.failed_on > cast('{{ var("ftf_as_of") }}' as date) - interval 365 day
group by 1, 2, 3, 4
having count(*) >= 2
