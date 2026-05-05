-- Superseded by models/payments/marts/dim_merchant.sql.
{{ config(materialized='table', enabled=false) }}
select 1 as merchant_id where 1 = 0
