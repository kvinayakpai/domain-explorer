{{ config(materialized='view') }}

-- Allocated oil per well per day.
select
    cast(well_id   as varchar ) as well_id,
    cast(day       as date    ) as day,
    cast(oil_bbl_d as double  ) as oil_bbl_d
from {{ source('upstream_artificial_lift', 'production_daily') }}
