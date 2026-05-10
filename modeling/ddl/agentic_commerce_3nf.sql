-- =============================================================================
-- Agentic Commerce — 3NF schema
-- Source standards (verbatim where the spec names a field):
--   AP2 — Agentic Payments Protocol (https://ap2-protocol.org)
--     IntentMandate, CartMandate, PaymentMandate; AAID; carry-back.
--   Visa Trusted Agent Protocol / Visa Agent Toolkit
--     AGI flag, AAID, signed mandate.
--   Mastercard Agent Pay
--     AAI flag, Authorization Token for Agents.
--   Stripe Agentic Commerce SDK
--     CheckoutSession with agent context, SetupIntent bound to grant.
--   Anthropic Model Context Protocol (https://modelcontextprotocol.io)
--     JSON-RPC 2.0 method invocations (tool calls).
--   OAuth 2.1 + RFC 9396 Rich Authorization Requests
--     authorization_details for {agentic_purchase, recurring_purchase, refund}.
--   ISO 4217 currency / ISO 18245 MCC / ISO 8583 underlying card-auth.
-- =============================================================================

create schema if not exists agentic_commerce;

-- The autonomous AI actor. AAID is network-issued (Visa/Mastercard).
create table if not exists agentic_commerce.agent (
    agent_id          varchar(64) primary key,
    aaid              varchar(64) unique,                  -- AP2 §4.2 / Mastercard AAI registry
    operator_org      varchar(255),                         -- anthropic|openai|google|amazon|klarna|...
    agent_kind        varchar(32),                          -- shopping_assistant|task_agent|browser_agent|...
    model_family      varchar(64),                          -- claude-opus-4|gpt-4o|gemini-2-ultra|...
    kya_status        varchar(16),                          -- verified|self_asserted|denied (Skyfire / Visa KYA)
    kya_trust_score   numeric(5,2),                         -- 0..100
    created_at        timestamp,
    status            varchar(16)
);

-- Human cardholder-of-record per Visa Trusted Agent Protocol passthrough.
create table if not exists agentic_commerce.principal (
    principal_id        varchar(64) primary key,
    external_user_ref   varchar(128),                       -- pseudonymous wallet/issuer ref
    country_iso2        varchar(2),
    kyc_level           varchar(8),                         -- L0|L1|L2|L3 per FATF
    created_at          timestamp,
    stepup_capable      boolean,                             -- WebAuthn/SPC/push enrolled
    status              varchar(16)
);

-- Merchant / seller, optionally agent-aware.
create table if not exists agentic_commerce.merchant (
    merchant_id        varchar(64) primary key,
    legal_name         varchar(255),
    domain             varchar(255),
    country_iso2       varchar(2),
    mcc                varchar(4),                          -- ISO 18245
    agent_aware_tier   varchar(16),                         -- tier1_native|tier2_mcp|tier3_legacy
    mcp_endpoint       text,                                 -- JSON-RPC 2.0 MCP server URL
    ap2_endpoint       text,
    created_at         timestamp
);

-- OAuth 2.1 + RFC 9396 RAR grant. AP2 IntentMandate maps onto this.
create table if not exists agentic_commerce.authorization_grant (
    grant_id                       varchar(64) primary key,
    principal_id                   varchar(64) references agentic_commerce.principal(principal_id),
    agent_id                       varchar(64) references agentic_commerce.agent(agent_id),
    rar_type                       varchar(64),              -- agentic_purchase | recurring_purchase | refund
    max_amount_minor               bigint,                   -- ISO 4217 minor units
    max_amount_currency            varchar(3),
    merchant_scope                 text,                     -- JSON: allowed merchant_ids / domain wildcards
    category_scope                 text,                     -- JSON: MCC / category constraints
    per_txn_cap_minor              bigint,
    scope_expires_at               timestamp,
    stepup_required_above_minor    bigint,
    issued_at                      timestamp,
    revoked_at                     timestamp,
    status                         varchar(16)               -- active|expired|revoked|exhausted
);

-- Bounded interaction window per AP2 + MCP.
create table if not exists agentic_commerce.agent_session (
    session_id          varchar(64) primary key,
    agent_id            varchar(64) references agentic_commerce.agent(agent_id),
    principal_id        varchar(64) references agentic_commerce.principal(principal_id),
    grant_id            varchar(64) references agentic_commerce.authorization_grant(grant_id),
    started_at          timestamp,
    ended_at            timestamp,
    client_signature    text,                                 -- signed JWT from operator
    principal_present   boolean
);

-- Stated intent — AP2 IntentMandate. The grain of agentic-conversion attribution.
create table if not exists agentic_commerce.intent_event (
    intent_id           varchar(64) primary key,
    session_id          varchar(64) references agentic_commerce.agent_session(session_id),
    principal_id        varchar(64) references agentic_commerce.principal(principal_id),
    agent_id            varchar(64) references agentic_commerce.agent(agent_id),
    intent_text_hash    varchar(128),                         -- SHA-256 of normalized intent
    category_hint       varchar(64),
    budget_min_minor    bigint,
    budget_max_minor    bigint,
    budget_currency     varchar(3),
    deadline_ts         timestamp,
    state               varchar(16),                          -- received|searching|cart_built|awaiting_auth|fulfilled|abandoned|expired
    created_at          timestamp,
    resolved_at         timestamp
);

-- One MCP tool invocation made by the agent.
create table if not exists agentic_commerce.tool_call (
    tool_call_id        varchar(64) primary key,
    session_id          varchar(64) references agentic_commerce.agent_session(session_id),
    intent_id           varchar(64) references agentic_commerce.intent_event(intent_id),
    server_name         varchar(64),                          -- stripe-mcp|shopify-mcp|merchant-mcp|search-mcp
    tool_name           varchar(128),
    started_at          timestamp,
    latency_ms          integer,
    cost_usd            numeric(10,6),
    status              varchar(16),                          -- ok|error|timeout|rate_limited|denied
    input_size_bytes    integer,
    output_size_bytes   integer
);

-- AP2 CartMandate — items the agent intends to purchase.
create table if not exists agentic_commerce.cart (
    cart_id                  varchar(64) primary key,
    intent_id                varchar(64) references agentic_commerce.intent_event(intent_id),
    merchant_id              varchar(64) references agentic_commerce.merchant(merchant_id),
    subtotal_minor           bigint,
    tax_minor                bigint,
    shipping_minor           bigint,
    total_minor              bigint,
    currency                 varchar(3),
    line_count               smallint,
    signed_payload_hash      varchar(128),                    -- SHA-256 of canonical AP2 CartMandate JSON
    signature_alg            varchar(16),                     -- ES256|RS256
    built_at                 timestamp,
    confirmed_by_principal   boolean,
    confirmation_ts          timestamp
);

-- AP2 PaymentMandate execution.
create table if not exists agentic_commerce.agent_transaction (
    agent_txn_id        varchar(64) primary key,
    cart_id             varchar(64) references agentic_commerce.cart(cart_id),
    grant_id            varchar(64) references agentic_commerce.authorization_grant(grant_id),
    agent_id            varchar(64) references agentic_commerce.agent(agent_id),
    principal_id        varchar(64) references agentic_commerce.principal(principal_id),
    merchant_id         varchar(64) references agentic_commerce.merchant(merchant_id),
    psp                 varchar(32),                          -- stripe|adyen|braintree|skyfire|crossmint|klarna
    rail                varchar(16),                          -- card|ach|sepa|stable_usd|wire
    scheme              varchar(16),                          -- Visa|Mastercard|Amex|Discover|JCB|n/a
    agent_indicator     varchar(16),                          -- Visa AGI / Mastercard AAI
    amount_minor        bigint,
    currency            varchar(3),
    stepup_method       varchar(16),                          -- none|webauthn|spc|push|sms|email_otp
    status              varchar(16),                          -- authorized|captured|declined|reversed|refunded|disputed
    authorized_at       timestamp,
    captured_at         timestamp,
    decline_reason      varchar(64),
    latency_ms          integer
);

-- Multi-touch attribution edge.
create table if not exists agentic_commerce.attribution_link (
    attribution_id      varchar(64) primary key,
    intent_id           varchar(64) references agentic_commerce.intent_event(intent_id),
    agent_txn_id        varchar(64) references agentic_commerce.agent_transaction(agent_txn_id),
    model               varchar(32),                           -- first_touch|last_touch|linear|time_decay|ml_uplift
    weight              numeric(5,4),
    lookback_seconds    integer,
    created_at          timestamp
);

-- KYA / Skyfire trust-score datapoint.
create table if not exists agentic_commerce.trust_score_event (
    trust_event_id      varchar(64) primary key,
    agent_id            varchar(64) references agentic_commerce.agent(agent_id),
    source              varchar(32),                           -- skyfire|visa_kya|mastercard_aai|merchant_local
    score               numeric(5,2),
    signal_summary      text,
    observed_at         timestamp
);

-- Chargeback / dispute on an agent transaction. Visa AP2 §7 carry-back.
create table if not exists agentic_commerce.dispute (
    dispute_id              varchar(64) primary key,
    agent_txn_id            varchar(64) references agentic_commerce.agent_transaction(agent_txn_id),
    reason_code             varchar(8),
    opened_at               timestamp,
    resolved_at             timestamp,
    amount_minor            bigint,
    currency                varchar(3),
    outcome                 varchar(16),                       -- won|lost|withdrawn|carried_back
    carryback_to_operator   boolean
);

-- Helpful indexes on time and cardinality.
create index if not exists ix_intent_session   on agentic_commerce.intent_event(session_id);
create index if not exists ix_tool_session     on agentic_commerce.tool_call(session_id);
create index if not exists ix_cart_intent      on agentic_commerce.cart(intent_id);
create index if not exists ix_txn_grant        on agentic_commerce.agent_transaction(grant_id);
create index if not exists ix_txn_merchant     on agentic_commerce.agent_transaction(merchant_id);
create index if not exists ix_dispute_txn      on agentic_commerce.dispute(agent_txn_id);
