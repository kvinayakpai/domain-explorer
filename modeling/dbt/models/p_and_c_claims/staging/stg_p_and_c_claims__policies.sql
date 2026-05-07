-- Staging: issued P&C policies.
{{ config(materialized='view') }}

select
    cast(policy_id        as varchar) as policy_id,
    cast(policyholder_id  as varchar) as policyholder_id,
    cast(line_of_business as varchar) as line_of_business,
    cast(premium_annual   as double)  as premium_annual,
    cast(deductible       as double)  as deductible,
    cast(effective_date   as date)    as effective_date,
    cast(expires_date     as date)    as expires_date,
    cast(carrier          as varchar) as carrier,
    case
        when cast(expires_date as date) < current_date then 'expired'
        when cast(effective_date as date) > current_date then 'pending'
        else 'in_force'
    end                              as policy_state
from {{ source('p_and_c_claims', 'policies') }}
