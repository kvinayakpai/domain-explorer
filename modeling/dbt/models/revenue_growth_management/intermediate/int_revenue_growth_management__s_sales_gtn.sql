-- Vault satellite — gross-to-net waterfall snapshot per sales transaction.
{{ config(materialized='ephemeral') }}

select
    {{ dbt_utils.generate_surrogate_key(['transaction_id']) }}  as hk_sales_txn,
    cast(invoice_date as timestamp)                              as load_dts,
    transaction_id,
    account_id,
    pack_id,
    deal_id,
    invoice_date,
    units,
    gross_revenue_cents,
    off_invoice_cents,
    rebate_accrual_cents,
    scan_down_cents,
    bill_back_cents,
    mcb_cents,
    slotting_cents,
    marketing_dev_funds_cents,
    total_gtn_cents,
    net_revenue_cents,
    cogs_cents,
    currency,
    source_system,
    'revenue_growth_management.sales_transaction'                as record_source
from {{ ref('stg_revenue_growth_management__sales_transactions') }}
