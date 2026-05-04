-- Stub merchant dimension — wire to source after MDM is in place.
{{ config(materialized='table') }}

select distinct
    merchant_id,
    cast(null as varchar) as merchant_name,
    cast(null as varchar) as mcc,
    cast(null as varchar) as country
from {{ ref('stg_payments__authorizations') }}
