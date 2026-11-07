-- One row per well per day: allocated oil and whether the well produced.
{{ config(materialized='table') }}

select
    p.well_id                              as well_key,
    p.day,
    p.oil_bbl_d,
    coalesce(p.oil_bbl_d, 0) > 0           as producing
from {{ ref('stg_upstream_artificial_lift__production_daily') }} p
