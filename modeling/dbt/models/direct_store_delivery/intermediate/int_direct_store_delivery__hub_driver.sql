{{ config(materialized='ephemeral') }}

with src as (
    select driver_id from {{ ref('stg_direct_store_delivery__driver') }}
    where driver_id is not null
)

select
    md5(driver_id)                      as h_driver_hk,
    driver_id                           as driver_bk,
    current_date                        as load_date,
    'direct_store_delivery.driver'      as record_source
from src
group by driver_id
