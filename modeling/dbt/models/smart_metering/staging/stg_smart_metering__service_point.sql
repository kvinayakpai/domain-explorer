-- Staging: light typing on smart_metering.service_point.
{{ config(materialized='view') }}

select
    cast(service_point_id    as varchar) as service_point_id,
    cast(premise_id          as varchar) as premise_id,
    cast(address_line        as varchar) as address_line,
    cast(address_city        as varchar) as address_city,
    upper(address_state)                  as address_state,
    cast(service_class       as varchar) as service_class,
    cast(rate_schedule       as varchar) as rate_schedule,
    cast(feeder_id           as varchar) as feeder_id,
    cast(transformer_id      as varchar) as transformer_id,
    cast(latitude            as double)  as latitude,
    cast(longitude           as double)  as longitude,
    cast(active_since        as date)    as active_since
from {{ source('smart_metering', 'service_point') }}
