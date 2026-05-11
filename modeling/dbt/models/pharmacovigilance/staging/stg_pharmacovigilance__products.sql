-- Staging: PV product master.
{{ config(materialized='view') }}

select
    cast(product_id   as varchar) as product_id,
    cast(tradename    as varchar) as tradename,
    cast(inn          as varchar) as inn,
    cast(atc_code     as varchar) as atc_code,
    cast(form         as varchar) as form,
    upper(marketing_authorization_country) as ma_country,
    cast(approval_year as integer) as approval_year
from {{ source('pharmacovigilance', 'products') }}
