-- Vault hub for the Liquidation Lot business key.
{{ config(materialized='ephemeral') }}

with src as (
    select lot_id
    from {{ ref('stg_returns_reverse_logistics__liquidation_lots') }}
    where lot_id is not null
)

select
    md5(lot_id)                                     as hk_lot,
    lot_id                                          as lot_bk,
    current_date                                    as load_dts,
    'returns_reverse_logistics.liquidation_lot'     as record_source
from src
group by lot_id
