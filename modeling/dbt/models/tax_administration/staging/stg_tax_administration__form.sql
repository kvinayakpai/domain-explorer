{{ config(materialized='view') }}

select
    cast(form_id          as varchar) as form_id,
    cast(return_id        as varchar) as return_id,
    cast(form_code        as varchar) as form_code,
    cast(form_description as varchar) as form_description,
    cast(form_revision    as varchar) as form_revision,
    cast(is_primary       as boolean) as is_primary,
    cast(page_count       as integer) as page_count
from {{ source('tax_administration', 'form') }}
