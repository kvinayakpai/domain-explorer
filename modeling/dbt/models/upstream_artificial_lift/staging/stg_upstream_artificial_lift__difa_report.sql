{{ config(materialized='view') }}

-- Teardown findings (API RP 11S1).
select
    cast(difa_report_id as varchar ) as difa_report_id,
    cast(well_id        as varchar ) as well_id,
    cast(esp_string_id  as varchar ) as esp_string_id,
    cast(reported_on    as date    ) as reported_on,
    cast(standard       as varchar ) as standard,
    cast(finding        as varchar ) as finding
from {{ source('upstream_artificial_lift', 'difa_report') }}
