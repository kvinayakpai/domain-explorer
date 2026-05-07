-- =============================================================================
-- Cloud FinOps — Data Vault 2.0
-- Hubs: provider, billing_account, sub_account, service, sku, resource,
-- commitment. Bitemporal sat for charge_line so retro-corrections are auditable.
-- =============================================================================

create schema if not exists cloud_finops_vault;

create table if not exists cloud_finops_vault.hub_provider (
    provider_hk bytea primary key,
    provider_bk varchar not null,
    load_dts    timestamp not null,
    rec_src     varchar not null
);

create table if not exists cloud_finops_vault.hub_billing_account (
    billing_account_hk bytea primary key,
    billing_account_bk varchar not null,
    load_dts           timestamp not null,
    rec_src            varchar not null
);

create table if not exists cloud_finops_vault.hub_sub_account (
    sub_account_hk bytea primary key,
    sub_account_bk varchar not null,
    load_dts       timestamp not null,
    rec_src        varchar not null
);

create table if not exists cloud_finops_vault.hub_service (
    service_hk bytea primary key,
    service_bk varchar not null,
    load_dts   timestamp not null,
    rec_src    varchar not null
);

create table if not exists cloud_finops_vault.hub_sku (
    sku_hk     bytea primary key,
    sku_bk     varchar not null,
    load_dts   timestamp not null,
    rec_src    varchar not null
);

create table if not exists cloud_finops_vault.hub_resource (
    resource_hk bytea primary key,
    resource_bk varchar not null,
    load_dts    timestamp not null,
    rec_src     varchar not null
);

create table if not exists cloud_finops_vault.hub_commitment (
    commitment_hk bytea primary key,
    commitment_bk varchar not null,
    load_dts      timestamp not null,
    rec_src       varchar not null
);

-- ---------------------------------------------------------------------------
-- Links
-- ---------------------------------------------------------------------------
create table if not exists cloud_finops_vault.link_account_hierarchy (
    link_hk            bytea primary key,
    provider_hk        bytea not null references cloud_finops_vault.hub_provider(provider_hk),
    billing_account_hk bytea not null references cloud_finops_vault.hub_billing_account(billing_account_hk),
    sub_account_hk     bytea not null references cloud_finops_vault.hub_sub_account(sub_account_hk),
    load_dts           timestamp not null,
    rec_src            varchar not null
);

create table if not exists cloud_finops_vault.link_resource_account (
    link_hk        bytea primary key,
    resource_hk    bytea not null references cloud_finops_vault.hub_resource(resource_hk),
    sub_account_hk bytea not null references cloud_finops_vault.hub_sub_account(sub_account_hk),
    load_dts       timestamp not null,
    rec_src        varchar not null
);

create table if not exists cloud_finops_vault.link_charge_line (
    link_hk        bytea primary key,
    charge_line_bk varchar not null,
    sub_account_hk bytea not null references cloud_finops_vault.hub_sub_account(sub_account_hk),
    service_hk     bytea references cloud_finops_vault.hub_service(service_hk),
    sku_hk         bytea references cloud_finops_vault.hub_sku(sku_hk),
    resource_hk    bytea references cloud_finops_vault.hub_resource(resource_hk),
    commitment_hk  bytea references cloud_finops_vault.hub_commitment(commitment_hk),
    load_dts       timestamp not null,
    rec_src        varchar not null
);

-- ---------------------------------------------------------------------------
-- Satellites (bitemporal)
-- ---------------------------------------------------------------------------
create table if not exists cloud_finops_vault.sat_billing_account (
    billing_account_hk    bytea not null references cloud_finops_vault.hub_billing_account(billing_account_hk),
    load_dts              timestamp not null,
    load_end_dts          timestamp,
    hash_diff             bytea not null,
    billing_account_name  varchar(255) not null,
    billing_currency      varchar(3) not null,
    agreement_id          varchar(64),
    payer_account_id      varchar,
    status                varchar(16) not null,
    rec_src               varchar not null,
    primary key (billing_account_hk, load_dts)
);

create table if not exists cloud_finops_vault.sat_sub_account (
    sub_account_hk    bytea not null references cloud_finops_vault.hub_sub_account(sub_account_hk),
    load_dts          timestamp not null,
    load_end_dts      timestamp,
    hash_diff         bytea not null,
    sub_account_name  varchar(255) not null,
    sub_account_type  varchar(32) not null,
    parent_org_unit   varchar(255),
    status            varchar(16) not null,
    rec_src           varchar not null,
    primary key (sub_account_hk, load_dts)
);

create table if not exists cloud_finops_vault.sat_resource (
    resource_hk        bytea not null references cloud_finops_vault.hub_resource(resource_hk),
    load_dts           timestamp not null,
    load_end_dts       timestamp,
    hash_diff          bytea not null,
    resource_name      varchar(255),
    resource_type      varchar(64),
    region_id          varchar(32),
    availability_zone  varchar(32),
    tagging_status     varchar(16) not null,
    created_ts         timestamp,
    terminated_ts      timestamp,
    rec_src            varchar not null,
    primary key (resource_hk, load_dts)
);

create table if not exists cloud_finops_vault.sat_resource_tags (
    resource_hk      bytea not null references cloud_finops_vault.hub_resource(resource_hk),
    tag_key          varchar(128) not null,
    load_dts         timestamp not null,
    load_end_dts     timestamp,
    hash_diff        bytea not null,
    tag_value        varchar(255),
    tag_source       varchar(16) not null,
    imputation_rule  varchar(64),
    applied_at       timestamp,
    rec_src          varchar not null,
    primary key (resource_hk, tag_key, load_dts)
);

create table if not exists cloud_finops_vault.sat_charge_line (
    link_hk                     bytea not null,
    load_dts                    timestamp not null,
    load_end_dts                timestamp,
    hash_diff                   bytea not null,
    charge_period_start         timestamp not null,
    charge_period_end           timestamp not null,
    charge_category             varchar(16) not null,
    charge_class                varchar(16),
    pricing_quantity            numeric(20, 6),
    consumed_quantity           numeric(20, 6),
    consumed_unit               varchar(32),
    list_unit_price             numeric(18, 8),
    contracted_unit_price       numeric(18, 8),
    list_cost                   numeric(18, 6),
    billed_cost                 numeric(18, 6) not null,
    effective_cost              numeric(18, 6) not null,
    invoice_id                  varchar(64),
    commitment_discount_status  varchar(16),
    rec_src                     varchar not null,
    primary key (link_hk, load_dts)
);

create table if not exists cloud_finops_vault.sat_commitment (
    commitment_hk     bytea not null references cloud_finops_vault.hub_commitment(commitment_hk),
    load_dts          timestamp not null,
    load_end_dts      timestamp,
    hash_diff         bytea not null,
    type              varchar(32) not null,
    category          varchar(32) not null,
    term              varchar(8),
    payment_option    varchar(16),
    hourly_commitment numeric(12, 4),
    total_commitment  numeric(18, 4),
    currency          varchar(3),
    scope             varchar(32),
    start_date        date,
    end_date          date,
    status            varchar(16) not null,
    rec_src           varchar not null,
    primary key (commitment_hk, load_dts)
);
