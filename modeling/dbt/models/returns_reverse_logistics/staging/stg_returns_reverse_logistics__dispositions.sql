{{ config(materialized='view') }}

select
    cast(disposition_id       as varchar)  as disposition_id,
    cast(disposition_code     as varchar)  as disposition_code,
    cast(disposition_name     as varchar)  as disposition_name,
    cast(target_channel       as varchar)  as target_channel,
    cast(typical_recovery_pct as double)   as typical_recovery_pct,
    cast(lane_owner           as varchar)  as lane_owner
from {{ source('returns_reverse_logistics', 'disposition') }}
