{{ config(materialized='view') }}

select
    cast(reservation_id as varchar)   as reservation_id,
    cast(connector_id   as varchar)   as connector_id,
    cast(id_token       as varchar)   as id_token,
    cast(reserved_at    as timestamp) as reserved_at,
    cast(expires_at     as timestamp) as expires_at,
    cast(status         as varchar)   as status,
    cast({{ format_date('reserved_at', '%Y%m%d') }} as integer) as reserved_date_key
from {{ source('ev_charging', 'reservation') }}
