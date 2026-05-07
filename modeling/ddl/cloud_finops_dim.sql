-- =============================================================================
-- Cloud FinOps — dimensional mart
-- Star schema. Facts: spend_daily (charge-line aggregate), commitment_use,
-- anomaly. Dim: provider, sub_account, service, sku, resource, region, date.
-- =============================================================================

create schema if not exists cloud_finops_dim;

create table if not exists cloud_finops_dim.dim_date (
    date_key      integer primary key,
    date_actual   date not null,
    day_of_week   smallint not null,
    iso_week      smallint not null,
    fiscal_period varchar(8)
);

create table if not exists cloud_finops_dim.dim_provider (
    provider_key   smallint primary key,
    provider_id    varchar not null,
    provider_name  varchar(64) not null
);

create table if not exists cloud_finops_dim.dim_sub_account (
    sub_account_key  bigint primary key,
    sub_account_id   varchar not null,
    sub_account_name varchar(255),
    sub_account_type varchar(32),
    parent_org_unit  varchar(255),
    valid_from       timestamp not null,
    valid_to         timestamp,
    is_current       boolean not null
);

create table if not exists cloud_finops_dim.dim_service (
    service_key       bigint primary key,
    service_id        varchar not null,
    service_name      varchar(128),
    service_category  varchar(64),
    valid_from        timestamp not null,
    valid_to          timestamp,
    is_current        boolean not null
);

create table if not exists cloud_finops_dim.dim_sku (
    sku_key           bigint primary key,
    sku_id            varchar not null,
    sku_meter         varchar(255),
    pricing_unit      varchar(32),
    valid_from        timestamp not null,
    valid_to          timestamp,
    is_current        boolean not null
);

create table if not exists cloud_finops_dim.dim_resource (
    resource_key   bigint primary key,
    resource_id    varchar not null,
    resource_name  varchar(255),
    resource_type  varchar(64),
    region_id      varchar(32),
    availability_zone varchar(32),
    valid_from     timestamp not null,
    valid_to       timestamp,
    is_current     boolean not null
);

create table if not exists cloud_finops_dim.dim_region (
    region_key smallint primary key,
    region_id  varchar(32) not null,
    region_name varchar(64),
    geography  varchar(32)
);

create table if not exists cloud_finops_dim.dim_cost_center (
    cost_center_key bigint primary key,
    cost_center_id  varchar not null,
    name            varchar(64),
    business_unit   varchar(64),
    gl_code         varchar(32),
    valid_from      timestamp not null,
    valid_to        timestamp,
    is_current      boolean not null
);

create table if not exists cloud_finops_dim.dim_charge_class (
    charge_class_key smallint primary key,
    charge_category  varchar(16) not null,
    charge_class     varchar(16),
    pricing_category varchar(16)
);

-- ---------------------------------------------------------------------------
-- Facts
-- ---------------------------------------------------------------------------

-- Grain: provider x sub_account x service x sku x resource x charge_class x date.
create table if not exists cloud_finops_dim.fact_spend_daily (
    provider_key       smallint not null references cloud_finops_dim.dim_provider(provider_key),
    sub_account_key    bigint not null references cloud_finops_dim.dim_sub_account(sub_account_key),
    service_key        bigint not null references cloud_finops_dim.dim_service(service_key),
    sku_key            bigint references cloud_finops_dim.dim_sku(sku_key),
    resource_key       bigint references cloud_finops_dim.dim_resource(resource_key),
    cost_center_key    bigint references cloud_finops_dim.dim_cost_center(cost_center_key),
    charge_class_key   smallint not null references cloud_finops_dim.dim_charge_class(charge_class_key),
    region_key         smallint references cloud_finops_dim.dim_region(region_key),
    date_key           integer not null references cloud_finops_dim.dim_date(date_key),
    consumed_quantity  numeric(20, 6),
    list_cost          numeric(18, 6),
    billed_cost        numeric(18, 6) not null,
    effective_cost     numeric(18, 6) not null,
    primary key (provider_key, sub_account_key, service_key, sku_key, resource_key, charge_class_key, date_key)
);

-- Grain: commitment x date.
create table if not exists cloud_finops_dim.fact_commitment_use_daily (
    commitment_id           varchar not null,
    sub_account_key         bigint references cloud_finops_dim.dim_sub_account(sub_account_key),
    date_key                integer not null references cloud_finops_dim.dim_date(date_key),
    purchased_hours         numeric(18, 4) not null,
    used_hours              numeric(18, 4) not null,
    unused_hours            numeric(18, 4) not null,
    amortized_cost          numeric(18, 6),
    savings_vs_list         numeric(18, 6),
    primary key (commitment_id, date_key)
);

-- Grain: anomaly event.
create table if not exists cloud_finops_dim.fact_anomaly (
    anomaly_id        varchar primary key,
    sub_account_key   bigint references cloud_finops_dim.dim_sub_account(sub_account_key),
    service_key       bigint references cloud_finops_dim.dim_service(service_key),
    detected_date_key integer not null references cloud_finops_dim.dim_date(date_key),
    resolved_date_key integer references cloud_finops_dim.dim_date(date_key),
    expected_spend    numeric(18, 2),
    observed_spend    numeric(18, 2),
    spend_delta       numeric(18, 2),
    anomaly_score     numeric(8, 4),
    is_resolved       boolean not null
);

-- Grain: budget x period x scope.
create table if not exists cloud_finops_dim.fact_budget_actual (
    budget_id        varchar not null,
    period_start_key integer not null references cloud_finops_dim.dim_date(date_key),
    period_end_key   integer not null references cloud_finops_dim.dim_date(date_key),
    cost_center_key  bigint references cloud_finops_dim.dim_cost_center(cost_center_key),
    budget_amount    numeric(18, 2) not null,
    actual_amount    numeric(18, 2) not null,
    variance_pct     numeric(10, 4),
    primary key (budget_id, period_start_key)
);
