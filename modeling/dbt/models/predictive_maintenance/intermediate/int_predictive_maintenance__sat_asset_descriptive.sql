-- Vault satellite carrying descriptive Asset attributes.
{{ config(materialized='ephemeral') }}

with src as (select * from {{ ref('stg_predictive_maintenance__asset') }})

select
    md5(asset_id)                                                              as h_asset_hk,
    cast(install_date as timestamp)                                            as load_ts,
    md5(coalesce(asset_class,'') || '|' || coalesce(manufacturer,'') || '|'
        || coalesce(model_number,'') || '|' || coalesce(criticality,'')
        || '|' || cast(coalesce(design_life_hours, 0) as varchar)
        || '|' || coalesce(status,''))                                          as hashdiff,
    asset_class,
    manufacturer,
    model_number,
    site_id,
    area_id,
    line_id,
    criticality,
    design_life_hours,
    rated_kw,
    status,
    'predictive_maintenance.asset'                                              as record_source
from src
