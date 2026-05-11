{{ config(materialized='view') }}

select
    cast(fatca_account_id            as varchar) as fatca_account_id,
    cast(taxpayer_id                 as varchar) as taxpayer_id,
    cast(account_holder_name         as varchar) as account_holder_name,
    upper(reporting_country)                     as reporting_country,
    upper(host_country)                          as host_country,
    cast(financial_institution_giin  as varchar) as financial_institution_giin,
    cast(account_balance_usd         as double)  as account_balance_usd,
    upper(currency)                              as currency,
    cast(report_year                 as integer) as report_year,
    cast(reportable_under            as varchar) as reportable_under,
    cast(is_recalcitrant             as boolean) as is_recalcitrant
from {{ source('tax_administration', 'fatca_account') }}
