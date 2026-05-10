-- =============================================================================
-- Agentic Commerce — Data Vault 2.0 schema
-- Hubs (business keys) + Links (relationships) + Satellites (descriptive,
-- insert-only, time-stamped). Mirrors the AP2/MCP source contract.
-- =============================================================================

create schema if not exists agentic_commerce_vault;

-- ---------- HUBS ----------
create table if not exists agentic_commerce_vault.h_agent (
    hk_agent       varchar(32) primary key,         -- MD5(agent_id)
    agent_id       varchar(64) unique,
    load_dts       timestamp,
    record_source  varchar(64)
);

create table if not exists agentic_commerce_vault.h_principal (
    hk_principal   varchar(32) primary key,
    principal_id   varchar(64) unique,
    load_dts       timestamp,
    record_source  varchar(64)
);

create table if not exists agentic_commerce_vault.h_merchant (
    hk_merchant    varchar(32) primary key,
    merchant_id    varchar(64) unique,
    load_dts       timestamp,
    record_source  varchar(64)
);

create table if not exists agentic_commerce_vault.h_intent (
    hk_intent      varchar(32) primary key,
    intent_id      varchar(64) unique,
    load_dts       timestamp,
    record_source  varchar(64)
);

create table if not exists agentic_commerce_vault.h_grant (
    hk_grant       varchar(32) primary key,
    grant_id       varchar(64) unique,
    load_dts       timestamp,
    record_source  varchar(64)
);

create table if not exists agentic_commerce_vault.h_session (
    hk_session     varchar(32) primary key,
    session_id     varchar(64) unique,
    load_dts       timestamp,
    record_source  varchar(64)
);

create table if not exists agentic_commerce_vault.h_purchase (
    hk_purchase    varchar(32) primary key,
    agent_txn_id   varchar(64) unique,
    load_dts       timestamp,
    record_source  varchar(64)
);

create table if not exists agentic_commerce_vault.h_cart (
    hk_cart        varchar(32) primary key,
    cart_id        varchar(64) unique,
    load_dts       timestamp,
    record_source  varchar(64)
);

-- ---------- LINKS ----------
create table if not exists agentic_commerce_vault.l_agent_intent (
    hk_link        varchar(32) primary key,
    hk_agent       varchar(32) references agentic_commerce_vault.h_agent(hk_agent),
    hk_intent      varchar(32) references agentic_commerce_vault.h_intent(hk_intent),
    hk_session     varchar(32) references agentic_commerce_vault.h_session(hk_session),
    load_dts       timestamp,
    record_source  varchar(64)
);

create table if not exists agentic_commerce_vault.l_intent_purchase (
    hk_link        varchar(32) primary key,
    hk_intent      varchar(32) references agentic_commerce_vault.h_intent(hk_intent),
    hk_purchase    varchar(32) references agentic_commerce_vault.h_purchase(hk_purchase),
    load_dts       timestamp,
    record_source  varchar(64)
);

create table if not exists agentic_commerce_vault.l_purchase_attribution (
    hk_link        varchar(32) primary key,
    hk_intent      varchar(32) references agentic_commerce_vault.h_intent(hk_intent),
    hk_purchase    varchar(32) references agentic_commerce_vault.h_purchase(hk_purchase),
    model          varchar(32),
    weight         numeric(5,4),
    load_dts       timestamp,
    record_source  varchar(64)
);

create table if not exists agentic_commerce_vault.l_authorization_grant (
    hk_link        varchar(32) primary key,
    hk_principal   varchar(32) references agentic_commerce_vault.h_principal(hk_principal),
    hk_agent       varchar(32) references agentic_commerce_vault.h_agent(hk_agent),
    hk_grant       varchar(32) references agentic_commerce_vault.h_grant(hk_grant),
    load_dts       timestamp,
    record_source  varchar(64)
);

create table if not exists agentic_commerce_vault.l_purchase_merchant (
    hk_link        varchar(32) primary key,
    hk_purchase    varchar(32) references agentic_commerce_vault.h_purchase(hk_purchase),
    hk_merchant    varchar(32) references agentic_commerce_vault.h_merchant(hk_merchant),
    load_dts       timestamp,
    record_source  varchar(64)
);

create table if not exists agentic_commerce_vault.l_cart_intent (
    hk_link        varchar(32) primary key,
    hk_cart        varchar(32) references agentic_commerce_vault.h_cart(hk_cart),
    hk_intent      varchar(32) references agentic_commerce_vault.h_intent(hk_intent),
    load_dts       timestamp,
    record_source  varchar(64)
);

-- ---------- SATELLITES ----------
create table if not exists agentic_commerce_vault.s_agent_trust_score (
    hk_agent          varchar(32) references agentic_commerce_vault.h_agent(hk_agent),
    load_dts          timestamp,
    source            varchar(32),
    score             numeric(5,2),
    signal_summary    text,
    record_source     varchar(64),
    primary key (hk_agent, load_dts)
);

create table if not exists agentic_commerce_vault.s_agent_descriptive (
    hk_agent       varchar(32) references agentic_commerce_vault.h_agent(hk_agent),
    load_dts       timestamp,
    operator_org   varchar(255),
    agent_kind     varchar(32),
    model_family   varchar(64),
    aaid           varchar(64),
    kya_status     varchar(16),
    status         varchar(16),
    record_source  varchar(64),
    primary key (hk_agent, load_dts)
);

create table if not exists agentic_commerce_vault.s_intent_state (
    hk_intent          varchar(32) references agentic_commerce_vault.h_intent(hk_intent),
    load_dts           timestamp,
    state              varchar(16),
    budget_min_minor   bigint,
    budget_max_minor   bigint,
    budget_currency    varchar(3),
    deadline_ts        timestamp,
    resolved_at        timestamp,
    record_source      varchar(64),
    primary key (hk_intent, load_dts)
);

create table if not exists agentic_commerce_vault.s_authorization_scope (
    hk_grant                       varchar(32) references agentic_commerce_vault.h_grant(hk_grant),
    load_dts                       timestamp,
    rar_type                       varchar(64),
    max_amount_minor               bigint,
    max_amount_currency            varchar(3),
    merchant_scope                 text,
    category_scope                 text,
    per_txn_cap_minor              bigint,
    stepup_required_above_minor    bigint,
    scope_expires_at               timestamp,
    status                         varchar(16),
    record_source                  varchar(64),
    primary key (hk_grant, load_dts)
);

create table if not exists agentic_commerce_vault.s_purchase_status (
    hk_purchase     varchar(32) references agentic_commerce_vault.h_purchase(hk_purchase),
    load_dts        timestamp,
    status          varchar(16),
    psp             varchar(32),
    rail            varchar(16),
    scheme          varchar(16),
    agent_indicator varchar(16),
    amount_minor    bigint,
    currency        varchar(3),
    stepup_method   varchar(16),
    decline_reason  varchar(64),
    record_source   varchar(64),
    primary key (hk_purchase, load_dts)
);

create table if not exists agentic_commerce_vault.s_merchant_descriptive (
    hk_merchant         varchar(32) references agentic_commerce_vault.h_merchant(hk_merchant),
    load_dts            timestamp,
    legal_name          varchar(255),
    domain              varchar(255),
    country_iso2        varchar(2),
    mcc                 varchar(4),
    agent_aware_tier    varchar(16),
    record_source       varchar(64),
    primary key (hk_merchant, load_dts)
);

create table if not exists agentic_commerce_vault.s_principal_descriptive (
    hk_principal       varchar(32) references agentic_commerce_vault.h_principal(hk_principal),
    load_dts           timestamp,
    country_iso2       varchar(2),
    kyc_level          varchar(8),
    stepup_capable     boolean,
    status             varchar(16),
    record_source      varchar(64),
    primary key (hk_principal, load_dts)
);
