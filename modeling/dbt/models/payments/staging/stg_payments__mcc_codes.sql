-- Staging: ISO MCC reference list.
{{ config(materialized='view') }}

select
    cast(mcc         as varchar) as mcc,
    cast(description as varchar) as mcc_description,
    cast(category    as varchar) as mcc_category
from {{ source('payments', 'mcc_codes') }}
