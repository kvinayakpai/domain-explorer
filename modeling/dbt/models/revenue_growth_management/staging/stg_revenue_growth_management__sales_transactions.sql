{{ config(materialized='view') }}

select
    cast(transaction_id              as varchar) as transaction_id,
    cast(account_id                  as varchar) as account_id,
    cast(pack_id                     as varchar) as pack_id,
    cast(deal_id                     as varchar) as deal_id,
    cast(invoice_date                as date)    as invoice_date,
    cast(units                       as bigint)  as units,
    cast(gross_revenue_cents         as bigint)  as gross_revenue_cents,
    cast(off_invoice_cents           as bigint)  as off_invoice_cents,
    cast(rebate_accrual_cents        as bigint)  as rebate_accrual_cents,
    cast(scan_down_cents             as bigint)  as scan_down_cents,
    cast(bill_back_cents             as bigint)  as bill_back_cents,
    cast(mcb_cents                   as bigint)  as mcb_cents,
    cast(slotting_cents              as bigint)  as slotting_cents,
    cast(marketing_dev_funds_cents   as bigint)  as marketing_dev_funds_cents,
    cast(net_revenue_cents           as bigint)  as net_revenue_cents,
    cast(cogs_cents                  as bigint)  as cogs_cents,
    upper(currency)                              as currency,
    cast(source_system               as varchar) as source_system,
    cast(off_invoice_cents + rebate_accrual_cents + scan_down_cents
       + bill_back_cents + mcb_cents + slotting_cents + marketing_dev_funds_cents
         as bigint)                              as total_gtn_cents,
    case
        when gross_revenue_cents > 0
            then cast(net_revenue_cents as double) / gross_revenue_cents
    end as price_realization
from {{ source('revenue_growth_management', 'sales_transaction') }}
