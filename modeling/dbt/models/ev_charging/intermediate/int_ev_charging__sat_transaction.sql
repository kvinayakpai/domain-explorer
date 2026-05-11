-- Vault-style satellite carrying descriptive Transaction attributes.
{{ config(materialized='ephemeral') }}

with src as (
    select * from {{ ref('stg_ev_charging__transaction') }}
)

select
    md5(transaction_id)                                 as h_transaction_hk,
    started_at                                          as load_ts,
    md5(coalesce(status,'') || '|' || coalesce(stop_reason,'') || '|'
        || coalesce(currency,'') || '|' || cast(energy_kwh as varchar))
                                                        as hashdiff,
    status,
    stop_reason,
    started_at,
    stopped_at,
    duration_minutes,
    energy_kwh,
    soc_start_pct,
    soc_end_pct,
    total_cost,
    currency,
    tariff_id,
    'ev_charging.transaction'                           as record_source
from src
