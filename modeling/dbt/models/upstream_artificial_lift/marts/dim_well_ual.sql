-- Wells with their lift method and ESP setting depth.
{{ config(materialized='table') }}

select
    well_id                               as well_key,
    field_id,
    pad,
    lift_method,
    esp_setting_depth_m
from {{ ref('stg_upstream_artificial_lift__well') }}
