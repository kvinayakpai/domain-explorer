{{ config(materialized='view') }}

select
    cast(withholding_id  as varchar) as withholding_id,
    cast(taxpayer_id     as varchar) as taxpayer_id,
    cast(year            as integer) as tax_year,
    cast(income_type     as varchar) as income_type,
    cast(gross_amount    as double)  as gross_amount,
    cast(withheld_amount as double)  as withheld_amount,
    cast(payer_ein       as varchar) as payer_ein,
    cast(form_received   as varchar) as form_received
from {{ source('tax_administration', 'withholding') }}
