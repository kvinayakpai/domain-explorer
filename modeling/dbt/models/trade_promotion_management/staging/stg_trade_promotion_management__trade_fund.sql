{{ config(materialized='view') }}

select
    cast(fund_id                as varchar) as fund_id,
    cast(account_id             as varchar) as account_id,
    cast(brand                  as varchar) as brand,
    cast(fiscal_year            as smallint) as fiscal_year,
    cast(fund_type              as varchar) as fund_type,
    cast(planned_amount_cents   as bigint)  as planned_amount_cents,
    cast(committed_amount_cents as bigint)  as committed_amount_cents,
    cast(spent_amount_cents     as bigint)  as spent_amount_cents,
    cast(balance_cents          as bigint)  as balance_cents,
    cast(status                 as varchar) as status
from {{ source('trade_promotion_management', 'trade_fund') }}
