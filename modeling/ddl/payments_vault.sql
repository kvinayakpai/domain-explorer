-- =============================================================================
-- Payments — Data Vault 2.0 (excerpt)
-- Hubs / Links / Satellites for the core payment event.
-- =============================================================================

create schema if not exists payments_vault;

-- Hubs
create table if not exists payments_vault.hub_merchant (
    merchant_hk      bytea primary key,
    merchant_bk      varchar not null,
    load_dts         timestamp not null,
    rec_src          varchar not null
);

create table if not exists payments_vault.hub_transaction (
    transaction_hk   bytea primary key,
    transaction_bk   varchar not null,
    load_dts         timestamp not null,
    rec_src          varchar not null
);

create table if not exists payments_vault.hub_card_token (
    token_hk         bytea primary key,
    token_bk         varchar not null,
    load_dts         timestamp not null,
    rec_src          varchar not null
);

-- Links
create table if not exists payments_vault.link_txn_merchant (
    link_hk          bytea primary key,
    transaction_hk   bytea not null references payments_vault.hub_transaction(transaction_hk),
    merchant_hk      bytea not null references payments_vault.hub_merchant(merchant_hk),
    load_dts         timestamp not null,
    rec_src          varchar not null
);

-- Satellites
create table if not exists payments_vault.sat_transaction_state (
    transaction_hk   bytea not null references payments_vault.hub_transaction(transaction_hk),
    load_dts         timestamp not null,
    load_end_dts     timestamp,
    hash_diff        bytea not null,
    status           varchar(16) not null,
    amount_minor     bigint not null,
    currency         varchar(3) not null,
    rail             varchar(16) not null,
    rec_src          varchar not null,
    primary key (transaction_hk, load_dts)
);

create table if not exists payments_vault.sat_merchant_descriptive (
    merchant_hk      bytea not null references payments_vault.hub_merchant(merchant_hk),
    load_dts         timestamp not null,
    load_end_dts     timestamp,
    hash_diff        bytea not null,
    legal_name       varchar not null,
    mcc              varchar(4),
    country_iso2     varchar(2),
    rec_src          varchar not null,
    primary key (merchant_hk, load_dts)
);
