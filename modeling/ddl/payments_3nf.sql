-- =============================================================================
-- Payments — 3NF schema (excerpt)
-- Anchor subdomain only; other subdomains will follow in later phases.
-- =============================================================================

create schema if not exists payments_3nf;

create table if not exists payments_3nf.merchant (
    merchant_id      varchar primary key,
    legal_name       varchar not null,
    mcc              varchar(4),
    country_iso2     varchar(2),
    onboarded_at     timestamp not null,
    is_active        boolean not null default true
);

create table if not exists payments_3nf.card_token (
    token_id         varchar primary key,
    masked_pan       varchar(19) not null,
    bin              varchar(8) not null,
    last4            varchar(4) not null,
    network          varchar(16) not null,
    issuer_country   varchar(2)
);

create table if not exists payments_3nf.transaction (
    transaction_id   varchar primary key,
    merchant_id      varchar not null references payments_3nf.merchant(merchant_id),
    token_id         varchar references payments_3nf.card_token(token_id),
    rail             varchar(16) not null,
    amount_minor     bigint not null,
    currency         varchar(3) not null,
    initiated_at     timestamp not null,
    status           varchar(16) not null
);

create table if not exists payments_3nf.authorization (
    auth_id          varchar primary key,
    transaction_id   varchar not null references payments_3nf.transaction(transaction_id),
    response_code    varchar(8) not null,
    approved         boolean not null,
    auth_ts          timestamp not null
);

create table if not exists payments_3nf.settlement (
    settlement_id    varchar primary key,
    transaction_id   varchar not null references payments_3nf.transaction(transaction_id),
    settled_amount_minor bigint not null,
    settled_at       timestamp not null,
    interchange_minor bigint
);

create table if not exists payments_3nf.dispute (
    dispute_id       varchar primary key,
    transaction_id   varchar not null references payments_3nf.transaction(transaction_id),
    reason_code      varchar(16) not null,
    opened_at        timestamp not null,
    resolved_at      timestamp,
    outcome          varchar(16)
);
