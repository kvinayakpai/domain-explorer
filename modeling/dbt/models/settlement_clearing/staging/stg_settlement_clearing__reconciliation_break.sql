-- Staging: reconciliation break (position / cash / trade / FX-PvP).
{{ config(materialized='view') }}

select
    cast(break_id      as varchar)   as break_id,
    cast(recon_type    as varchar)   as recon_type,
    cast(side_a_system as varchar)   as side_a_system,
    cast(side_b_system as varchar)   as side_b_system,
    cast(instrument_id as varchar)   as instrument_id,
    cast(qty_diff      as double)    as qty_diff,
    cast(amount_diff   as double)    as amount_diff,
    upper(currency)                  as currency,
    cast(detected_at   as timestamp) as detected_at,
    cast(status        as varchar)   as status,
    cast(owner_team    as varchar)   as owner_team,
    cast(aged_days     as integer)   as aged_days
from {{ source('settlement_clearing', 'reconciliation_break') }}
