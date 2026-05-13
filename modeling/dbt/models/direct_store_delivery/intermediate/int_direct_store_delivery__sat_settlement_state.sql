{{ config(materialized='ephemeral') }}

with src as (select * from {{ ref('stg_direct_store_delivery__settlement') }})

select
    md5(settlement_id)                                                                                                                  as h_settlement_hk,
    current_timestamp                                                                                                                    as load_ts,
    md5(coalesce(status,'') || '|' || cast(coalesce(variance_cents,0) as varchar) || '|' || cast(coalesce(total_invoiced_cents,0) as varchar)) as hashdiff,
    total_invoiced_cents,
    total_collected_cash_cents,
    total_collected_check_cents,
    total_collected_eft_cents,
    total_charge_account_cents,
    returns_credit_cents,
    spoilage_credit_cents,
    variance_cents,
    abs_variance_cents,
    variance_reason,
    status,
    is_balanced,
    closed_at,
    approved_by,
    'direct_store_delivery.settlement'                                                                                                   as record_source
from src
