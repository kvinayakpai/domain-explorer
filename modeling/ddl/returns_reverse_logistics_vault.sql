-- =============================================================================
-- Returns & Reverse Logistics — Data Vault 2.0 schema
-- Hubs (business keys) + Links (relationships) + Satellites (descriptive,
-- insert-only, time-stamped). Mirrors the EDI 180 / GS1 EPCIS / Optoro contracts.
-- =============================================================================

create schema if not exists returns_reverse_logistics_vault;

-- ---------- HUBS ----------
create table if not exists returns_reverse_logistics_vault.h_customer (
    hk_customer    varchar(32) primary key,                     -- MD5(customer_id)
    customer_id    varchar(32) unique,
    load_dts       timestamp,
    record_source  varchar(64)
);

create table if not exists returns_reverse_logistics_vault.h_order (
    hk_order       varchar(32) primary key,
    order_id       varchar(32) unique,
    load_dts       timestamp,
    record_source  varchar(64)
);

create table if not exists returns_reverse_logistics_vault.h_rma (
    hk_rma         varchar(32) primary key,
    rma_id         varchar(32) unique,
    load_dts       timestamp,
    record_source  varchar(64)
);

create table if not exists returns_reverse_logistics_vault.h_return_item (
    hk_return_item varchar(32) primary key,
    return_item_id varchar(32) unique,
    load_dts       timestamp,
    record_source  varchar(64)
);

create table if not exists returns_reverse_logistics_vault.h_refund (
    hk_refund      varchar(32) primary key,
    refund_id      varchar(32) unique,
    load_dts       timestamp,
    record_source  varchar(64)
);

create table if not exists returns_reverse_logistics_vault.h_lot (
    hk_lot         varchar(32) primary key,
    lot_id         varchar(32) unique,
    load_dts       timestamp,
    record_source  varchar(64)
);

create table if not exists returns_reverse_logistics_vault.h_reason_code (
    hk_reason_code varchar(32) primary key,
    reason_code_id varchar(16) unique,
    load_dts       timestamp,
    record_source  varchar(64)
);

create table if not exists returns_reverse_logistics_vault.h_disposition (
    hk_disposition varchar(32) primary key,
    disposition_id varchar(16) unique,
    load_dts       timestamp,
    record_source  varchar(64)
);

-- ---------- LINKS ----------
create table if not exists returns_reverse_logistics_vault.l_rma_order (
    hk_link        varchar(32) primary key,
    hk_rma         varchar(32) references returns_reverse_logistics_vault.h_rma(hk_rma),
    hk_order       varchar(32) references returns_reverse_logistics_vault.h_order(hk_order),
    hk_customer    varchar(32) references returns_reverse_logistics_vault.h_customer(hk_customer),
    load_dts       timestamp,
    record_source  varchar(64)
);

create table if not exists returns_reverse_logistics_vault.l_item_rma (
    hk_link        varchar(32) primary key,
    hk_return_item varchar(32) references returns_reverse_logistics_vault.h_return_item(hk_return_item),
    hk_rma         varchar(32) references returns_reverse_logistics_vault.h_rma(hk_rma),
    hk_reason_code varchar(32) references returns_reverse_logistics_vault.h_reason_code(hk_reason_code),
    hk_disposition varchar(32) references returns_reverse_logistics_vault.h_disposition(hk_disposition),
    load_dts       timestamp,
    record_source  varchar(64)
);

create table if not exists returns_reverse_logistics_vault.l_refund_order (
    hk_link        varchar(32) primary key,
    hk_refund      varchar(32) references returns_reverse_logistics_vault.h_refund(hk_refund),
    hk_order       varchar(32) references returns_reverse_logistics_vault.h_order(hk_order),
    hk_customer    varchar(32) references returns_reverse_logistics_vault.h_customer(hk_customer),
    hk_rma         varchar(32) references returns_reverse_logistics_vault.h_rma(hk_rma),
    load_dts       timestamp,
    record_source  varchar(64)
);

create table if not exists returns_reverse_logistics_vault.l_lot_item (
    hk_link        varchar(32) primary key,
    hk_lot         varchar(32) references returns_reverse_logistics_vault.h_lot(hk_lot),
    hk_return_item varchar(32) references returns_reverse_logistics_vault.h_return_item(hk_return_item),
    allocated_cogs_minor     bigint,
    allocated_proceeds_minor bigint,
    load_dts       timestamp,
    record_source  varchar(64)
);

-- ---------- SATELLITES ----------
create table if not exists returns_reverse_logistics_vault.s_rma_status (
    hk_rma           varchar(32) references returns_reverse_logistics_vault.h_rma(hk_rma),
    load_dts         timestamp,
    rma_status       varchar(16),
    return_method    varchar(32),
    return_platform  varchar(32),
    carrier          varchar(16),
    cross_border     boolean,
    record_source    varchar(64),
    primary key (hk_rma, load_dts)
);

create table if not exists returns_reverse_logistics_vault.s_item_disposition (
    hk_return_item         varchar(32) references returns_reverse_logistics_vault.h_return_item(hk_return_item),
    load_dts               timestamp,
    condition_grade        varchar(8),
    disposition_decided_ts timestamp,
    unit_cogs_minor        bigint,
    unit_retail_minor      bigint,
    quantity               integer,
    record_source          varchar(64),
    primary key (hk_return_item, load_dts)
);

create table if not exists returns_reverse_logistics_vault.s_refund_descriptive (
    hk_refund                       varchar(32) references returns_reverse_logistics_vault.h_refund(hk_refund),
    load_dts                        timestamp,
    refund_type                     varchar(16),
    refund_amount_minor             bigint,
    currency                        varchar(3),
    restocking_fee_collected_minor  bigint,
    payment_rail                    varchar(16),
    status                          varchar(16),
    record_source                   varchar(64),
    primary key (hk_refund, load_dts)
);

create table if not exists returns_reverse_logistics_vault.s_lot_proceeds (
    hk_lot              varchar(32) references returns_reverse_logistics_vault.h_lot(hk_lot),
    load_dts            timestamp,
    marketplace         varchar(32),
    item_count          integer,
    total_cogs_minor    bigint,
    proceeds_minor      bigint,
    currency            varchar(3),
    recovery_pct        numeric(6,4),
    sold_ts             timestamp,
    record_source       varchar(64),
    primary key (hk_lot, load_dts)
);

create table if not exists returns_reverse_logistics_vault.s_customer_descriptive (
    hk_customer              varchar(32) references returns_reverse_logistics_vault.h_customer(hk_customer),
    load_dts                 timestamp,
    country_iso2             varchar(2),
    loyalty_tier             varchar(16),
    lifetime_orders          integer,
    lifetime_returns         integer,
    chronic_returner_flag    boolean,
    chronic_returner_score   numeric(5,3),
    status                   varchar(16),
    record_source            varchar(64),
    primary key (hk_customer, load_dts)
);

create table if not exists returns_reverse_logistics_vault.s_refurb_outcome (
    hk_return_item                  varchar(32) references returns_reverse_logistics_vault.h_return_item(hk_return_item),
    load_dts                        timestamp,
    outcome                         varchar(32),
    post_refurb_grade               varchar(8),
    labor_minutes                   integer,
    parts_cost_minor                bigint,
    post_refurb_resale_value_minor  bigint,
    record_source                   varchar(64),
    primary key (hk_return_item, load_dts)
);

create table if not exists returns_reverse_logistics_vault.s_fraud_signal (
    hk_rma          varchar(32) references returns_reverse_logistics_vault.h_rma(hk_rma),
    load_dts        timestamp,
    source          varchar(32),
    signal_type     varchar(32),
    score           numeric(5,3),
    recommendation  varchar(16),
    record_source   varchar(64),
    primary key (hk_rma, load_dts)
);

create table if not exists returns_reverse_logistics_vault.s_carrier_label (
    hk_rma              varchar(32) references returns_reverse_logistics_vault.h_rma(hk_rma),
    load_dts            timestamp,
    carrier             varchar(16),
    service_level       varchar(32),
    label_cost_minor    bigint,
    scope3_kg_co2e      numeric(8,3),
    status              varchar(16),
    record_source       varchar(64),
    primary key (hk_rma, load_dts)
);
