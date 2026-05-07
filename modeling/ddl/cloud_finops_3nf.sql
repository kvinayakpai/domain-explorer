-- =============================================================================
-- Cloud FinOps — 3NF schema
-- Source standard: FOCUS 1.2 / 1.3 (FinOps Open Cost & Usage Specification).
-- Column names mirror the FOCUS spec — see column descriptions for mapping.
-- =============================================================================

create schema if not exists cloud_finops_3nf;

create table if not exists cloud_finops_3nf.provider (
    provider_id              varchar primary key,
    provider_name            varchar(64) not null,
    publisher_name           varchar(64),
    invoice_currency_default varchar(3),
    connector_status         varchar(16) not null
);

create table if not exists cloud_finops_3nf.billing_account (
    billing_account_id   varchar primary key,
    provider_id          varchar not null references cloud_finops_3nf.provider(provider_id),
    billing_account_name varchar(255) not null,
    billing_currency     varchar(3) not null,
    agreement_id         varchar(64),
    payer_account_id     varchar,
    status               varchar(16) not null
);

create table if not exists cloud_finops_3nf.sub_account (
    sub_account_id       varchar primary key,
    billing_account_id   varchar not null references cloud_finops_3nf.billing_account(billing_account_id),
    sub_account_name     varchar(255) not null,
    sub_account_type     varchar(32) not null,
    parent_org_unit      varchar(255),
    status               varchar(16) not null
);

create table if not exists cloud_finops_3nf.service (
    service_id            varchar primary key,
    provider_id           varchar not null references cloud_finops_3nf.provider(provider_id),
    service_name          varchar(128) not null,
    service_category      varchar(64) not null,
    service_subcategory   varchar(64),
    product_name          varchar(128)
);

create table if not exists cloud_finops_3nf.sku (
    sku_id                  varchar primary key,
    service_id              varchar not null references cloud_finops_3nf.service(service_id),
    sku_price_id            varchar(128),
    sku_meter               varchar(255),
    pricing_unit            varchar(32),
    list_unit_price         numeric(18, 8),
    contracted_unit_price   numeric(18, 8)
);

create table if not exists cloud_finops_3nf.resource (
    resource_id        varchar primary key,
    sub_account_id     varchar not null references cloud_finops_3nf.sub_account(sub_account_id),
    resource_name      varchar(255),
    resource_type      varchar(64),
    region_id          varchar(32),
    region_name        varchar(64),
    availability_zone  varchar(32),
    tagging_status     varchar(16) not null,
    created_ts         timestamp,
    terminated_ts      timestamp
);

create table if not exists cloud_finops_3nf.tag (
    resource_id      varchar not null references cloud_finops_3nf.resource(resource_id),
    tag_key          varchar(128) not null,
    tag_value        varchar(255),
    tag_source       varchar(16) not null,
    imputation_rule  varchar(64),
    applied_at       timestamp,
    primary key (resource_id, tag_key)
);

create table if not exists cloud_finops_3nf.commitment (
    commitment_id        varchar primary key,
    provider_id          varchar not null references cloud_finops_3nf.provider(provider_id),
    billing_account_id   varchar references cloud_finops_3nf.billing_account(billing_account_id),
    name                 varchar(255),
    type                 varchar(32) not null,
    category             varchar(32) not null,
    term                 varchar(8),
    payment_option       varchar(16),
    hourly_commitment    numeric(12, 4),
    total_commitment     numeric(18, 4),
    currency             varchar(3),
    scope                varchar(32),
    start_date           date,
    end_date             date,
    status               varchar(16) not null
);

create table if not exists cloud_finops_3nf.charge_line (
    charge_line_id              varchar primary key,
    provider_id                 varchar not null references cloud_finops_3nf.provider(provider_id),
    billing_account_id          varchar not null references cloud_finops_3nf.billing_account(billing_account_id),
    sub_account_id              varchar references cloud_finops_3nf.sub_account(sub_account_id),
    service_id                  varchar references cloud_finops_3nf.service(service_id),
    sku_id                      varchar references cloud_finops_3nf.sku(sku_id),
    resource_id                 varchar references cloud_finops_3nf.resource(resource_id),
    charge_period_start         timestamp not null,
    charge_period_end           timestamp not null,
    billing_period_start        timestamp not null,
    billing_period_end          timestamp not null,
    charge_category             varchar(16) not null,
    charge_class                varchar(16),
    charge_frequency            varchar(16),
    charge_description          varchar(255),
    pricing_category            varchar(16),
    pricing_quantity            numeric(20, 6),
    pricing_unit                varchar(32),
    consumed_quantity           numeric(20, 6),
    consumed_unit               varchar(32),
    list_unit_price             numeric(18, 8),
    contracted_unit_price       numeric(18, 8),
    list_cost                   numeric(18, 6),
    contracted_cost             numeric(18, 6),
    billed_cost                 numeric(18, 6) not null,
    effective_cost              numeric(18, 6) not null,
    invoice_id                  varchar(64),
    invoice_issuer_name         varchar(128),
    billing_currency            varchar(3) not null,
    capacity_reservation_id     varchar,
    commitment_discount_id      varchar references cloud_finops_3nf.commitment(commitment_id),
    commitment_discount_status  varchar(16)
);

create table if not exists cloud_finops_3nf.cost_center (
    cost_center_id          varchar primary key,
    name                    varchar(64) not null,
    parent_cost_center_id   varchar,
    owner_email             varchar(255),
    business_unit           varchar(64),
    gl_code                 varchar(32)
);

create table if not exists cloud_finops_3nf.allocation_rule (
    rule_id              varchar primary key,
    name                 varchar(64) not null,
    priority             smallint not null,
    condition_json       text,
    split_method         varchar(16) not null,
    target_cost_centers  text,
    enabled              boolean not null default true,
    effective_from       date not null,
    effective_to         date
);

create table if not exists cloud_finops_3nf.budget (
    budget_id            varchar primary key,
    scope_type           varchar(16) not null,
    scope_value          varchar(255) not null,
    period_grain         varchar(8) not null,
    period_start         date not null,
    period_end           date not null,
    amount               numeric(18, 2) not null,
    currency             varchar(3) not null,
    alert_threshold_pct  smallint,
    owner_email          varchar(255)
);

create table if not exists cloud_finops_3nf.anomaly (
    anomaly_id          varchar primary key,
    detected_at         timestamp not null,
    scope_type          varchar(16) not null,
    scope_value         varchar(255) not null,
    detection_method    varchar(32),
    anomaly_score       numeric(8, 4),
    expected_spend      numeric(18, 2),
    observed_spend      numeric(18, 2),
    status              varchar(16) not null,
    resolution_notes    text
);

create table if not exists cloud_finops_3nf.forecast (
    forecast_id        varchar primary key,
    scope_type         varchar(16) not null,
    scope_value        varchar(255) not null,
    forecast_method    varchar(32),
    forecast_horizon   smallint,
    granularity        varchar(8) not null,
    generated_at       timestamp not null,
    forecast_json      text,
    mape               numeric(8, 4)
);

create table if not exists cloud_finops_3nf.utilization_metric (
    resource_id   varchar not null references cloud_finops_3nf.resource(resource_id),
    metric_name   varchar(64) not null,
    sample_ts     timestamp not null,
    avg_value     numeric(18, 6),
    max_value     numeric(18, 6),
    unit          varchar(16),
    idle_flag     boolean not null default false,
    primary key (resource_id, metric_name, sample_ts)
);
