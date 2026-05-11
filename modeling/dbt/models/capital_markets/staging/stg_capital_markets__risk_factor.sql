-- Staging: risk factor curves / surfaces (FX, IR, EQ, Commodity).
{{ config(materialized='view') }}

select
    cast(risk_factor_id as varchar) as risk_factor_id,
    cast(factor_name    as varchar) as factor_name,
    cast(factor_class   as varchar) as factor_class,
    cast(as_of_date     as date)    as as_of_date,
    cast(level          as double)  as level,
    cast(vol_1d         as double)  as vol_1d,
    cast(vol_30d        as double)  as vol_30d
from {{ source('capital_markets', 'risk_factor') }}
