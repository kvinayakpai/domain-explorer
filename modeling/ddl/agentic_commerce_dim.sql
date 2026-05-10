-- =============================================================================
-- Agentic Commerce — Kimball dimensional schema
-- Star: fct_agent_transaction, fct_intent_event, fct_authorization_event
-- Conformed dims: dim_agent, dim_principal, dim_merchant, dim_authorization_scope, dim_date_agentic
-- =============================================================================

create schema if not exists agentic_commerce_dim;

-- ---------- DIMS ----------
create table if not exists agentic_commerce_dim.dim_date_agentic (
    date_key       integer primary key,        -- yyyymmdd
    cal_date       date,
    day_of_week    smallint,
    day_name       varchar(12),
    month          smallint,
    month_name     varchar(12),
    quarter        smallint,
    year           smallint,
    is_weekend     boolean
);

create table if not exists agentic_commerce_dim.dim_agent (
    agent_sk          bigint primary key,
    agent_id          varchar(64) unique,
    aaid              varchar(64),
    operator_org      varchar(255),
    agent_kind        varchar(32),
    model_family      varchar(64),
    kya_status        varchar(16),
    kya_trust_score   numeric(5,2),
    status            varchar(16),
    valid_from        timestamp,
    valid_to          timestamp,
    is_current        boolean
);

create table if not exists agentic_commerce_dim.dim_principal (
    principal_sk        bigint primary key,
    principal_id        varchar(64) unique,
    country_iso2        varchar(2),
    kyc_level           varchar(8),
    stepup_capable      boolean,
    status              varchar(16),
    valid_from          timestamp,
    valid_to            timestamp,
    is_current          boolean
);

create table if not exists agentic_commerce_dim.dim_merchant (
    merchant_sk          bigint primary key,
    merchant_id          varchar(64) unique,
    legal_name           varchar(255),
    domain               varchar(255),
    country_iso2         varchar(2),
    mcc                  varchar(4),
    agent_aware_tier     varchar(16),
    has_mcp_endpoint     boolean,
    has_ap2_endpoint     boolean
);

create table if not exists agentic_commerce_dim.dim_authorization_scope (
    scope_sk                       bigint primary key,
    grant_id                       varchar(64) unique,
    rar_type                       varchar(64),
    max_amount_minor               bigint,
    max_amount_currency            varchar(3),
    per_txn_cap_minor              bigint,
    stepup_required_above_minor    bigint,
    scope_expires_at               timestamp,
    status                         varchar(16)
);

create table if not exists agentic_commerce_dim.dim_psp (
    psp_sk          smallint primary key,
    psp             varchar(32) unique,
    rail            varchar(16),
    scheme_default  varchar(16)
);

-- ---------- FACTS ----------
create table if not exists agentic_commerce_dim.fct_agent_transaction (
    agent_txn_id        varchar(64) primary key,
    date_key            integer references agentic_commerce_dim.dim_date_agentic(date_key),
    agent_sk            bigint  references agentic_commerce_dim.dim_agent(agent_sk),
    principal_sk        bigint  references agentic_commerce_dim.dim_principal(principal_sk),
    merchant_sk         bigint  references agentic_commerce_dim.dim_merchant(merchant_sk),
    scope_sk            bigint  references agentic_commerce_dim.dim_authorization_scope(scope_sk),
    psp_sk              smallint references agentic_commerce_dim.dim_psp(psp_sk),
    cart_id             varchar(64),
    amount_minor        bigint,
    currency            varchar(3),
    amount_usd          numeric(15,4),                -- normalized for cross-currency rollups
    stepup_method       varchar(16),
    is_stepup           boolean,
    is_authorized       boolean,
    is_captured         boolean,
    is_declined         boolean,
    is_refunded         boolean,
    is_disputed         boolean,
    latency_ms          integer,
    authorized_at       timestamp,
    captured_at         timestamp
);

create table if not exists agentic_commerce_dim.fct_intent_event (
    intent_id           varchar(64) primary key,
    date_key            integer references agentic_commerce_dim.dim_date_agentic(date_key),
    agent_sk            bigint  references agentic_commerce_dim.dim_agent(agent_sk),
    principal_sk        bigint  references agentic_commerce_dim.dim_principal(principal_sk),
    session_id          varchar(64),
    state               varchar(16),
    category_hint       varchar(64),
    budget_min_minor    bigint,
    budget_max_minor    bigint,
    budget_currency     varchar(3),
    deadline_ts         timestamp,
    fulfilled           boolean,
    abandoned           boolean,
    intent_to_purchase_seconds integer,
    created_at          timestamp,
    resolved_at         timestamp
);

create table if not exists agentic_commerce_dim.fct_authorization_event (
    grant_event_id      varchar(64) primary key,
    grant_id            varchar(64),
    date_key            integer references agentic_commerce_dim.dim_date_agentic(date_key),
    agent_sk            bigint  references agentic_commerce_dim.dim_agent(agent_sk),
    principal_sk        bigint  references agentic_commerce_dim.dim_principal(principal_sk),
    scope_sk            bigint  references agentic_commerce_dim.dim_authorization_scope(scope_sk),
    event_type          varchar(16),                  -- issued|refreshed|exhausted|revoked|expired
    delta_amount_minor  bigint,
    occurred_at         timestamp
);

create table if not exists agentic_commerce_dim.fct_tool_call (
    tool_call_id        varchar(64) primary key,
    date_key            integer references agentic_commerce_dim.dim_date_agentic(date_key),
    agent_sk            bigint  references agentic_commerce_dim.dim_agent(agent_sk),
    intent_id           varchar(64),
    server_name         varchar(64),
    tool_name           varchar(128),
    latency_ms          integer,
    cost_usd            numeric(10,6),
    is_error            boolean,
    is_timeout          boolean,
    is_denied           boolean,
    started_at          timestamp
);

-- Helpful indexes
create index if not exists ix_fct_txn_date     on agentic_commerce_dim.fct_agent_transaction(date_key);
create index if not exists ix_fct_txn_agent    on agentic_commerce_dim.fct_agent_transaction(agent_sk);
create index if not exists ix_fct_txn_merchant on agentic_commerce_dim.fct_agent_transaction(merchant_sk);
create index if not exists ix_fct_intent_date  on agentic_commerce_dim.fct_intent_event(date_key);
create index if not exists ix_fct_tool_agent   on agentic_commerce_dim.fct_tool_call(agent_sk);
