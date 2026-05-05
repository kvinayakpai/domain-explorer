-- Superseded by models/payments/marts/fct_payments.sql (grain-level, not pre-aggregated).
{{ config(materialized='table', enabled=false) }}
select 1 as day where 1 = 0
