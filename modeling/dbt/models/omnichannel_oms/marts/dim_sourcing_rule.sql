{{ config(materialized='table') }}

select
    row_number() over (order by rule_id) as rule_sk,
    rule_id,
    rule_name,
    priority,
    cost_weight,
    speed_weight,
    capacity_weight,
    clearance_pull_weight,
    status
from {{ ref('stg_omnichannel_oms__sourcing_rules') }}
