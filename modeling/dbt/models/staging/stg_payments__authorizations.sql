-- Superseded by models/payments/staging/stg_payments__payments.sql against
-- the real `payments` schema in domain-explorer.duckdb. Disabled so dbt does
-- not try to compile it against the no-longer-defined `payments_raw` source.
{{ config(materialized='view', enabled=false) }}
select 1 as auth_id where 1 = 0
