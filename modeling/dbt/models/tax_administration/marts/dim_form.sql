-- Form dimension distinct on form_code (deduped from form attachments).
{{ config(materialized='table') }}

with f as (
    select form_code, form_description, form_revision
    from {{ ref('stg_tax_administration__form') }}
)

select
    md5(form_code)                                  as form_key,
    form_code,
    any_value(form_description)                     as form_description,
    max(form_revision)                              as latest_revision,
    count(*)                                        as attachment_count
from f
group by form_code
