{{ config(materialized='view') }}

select
    cast(invoice_id                as varchar)    as invoice_id,
    cast(supplier_id               as varchar)    as supplier_id,
    cast(invoice_number            as varchar)    as invoice_number,
    cast(po_id                     as varchar)    as po_id,
    cast(invoice_date              as date)        as invoice_date,
    cast(due_date                  as date)        as due_date,
    cast(received_ts               as timestamp)  as received_ts,
    cast(total_amount              as double)     as total_amount,
    cast(total_currency            as varchar)    as total_currency,
    cast(total_amount_base_usd     as double)     as total_amount_base_usd,
    cast(tax_amount                as double)     as tax_amount,
    cast(match_type                as varchar)    as match_type,
    cast(matched                   as boolean)    as matched,
    cast(paid_ts                   as timestamp)  as paid_ts,
    cast(paid_amount               as double)     as paid_amount,
    cast(early_pay_discount_taken  as boolean)    as early_pay_discount_taken,
    cast(aging_days                as smallint)   as aging_days,
    cast(peppol_message_id         as varchar)    as peppol_message_id,
    cast(edi_810_doc_no            as varchar)    as edi_810_doc_no,
    cast(status                    as varchar)    as status,
    case when match_type = 'three_way' then true else false end as is_three_way_match,
    case when paid_ts is not null then true else false end as is_paid,
    case when aging_days > 60 then true else false end as is_aged_over_60
from {{ source('procurement_spend_analytics', 'invoice') }}
