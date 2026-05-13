-- =============================================================================
-- Loss Prevention — Kimball dimensional schema
-- Star marts: fct_exceptions, fct_incidents, fct_investigations, fct_recoveries,
-- fct_shrink_snapshot.
-- Conformed dims (suffixed _lp on collisions): dim_date_lp, dim_store_lp,
-- dim_product_lp, dim_employee, dim_incident_type.
-- =============================================================================

create schema if not exists loss_prevention_dim;

-- ---------- DIMS ----------
create table if not exists loss_prevention_dim.dim_date_lp (
    date_key       integer primary key,           -- yyyymmdd
    cal_date       date,
    day_of_week    smallint,
    day_name       varchar(12),
    month          smallint,
    month_name     varchar(12),
    quarter        smallint,
    year           smallint,
    iso_week       integer,
    is_weekend     boolean
);

create table if not exists loss_prevention_dim.dim_store_lp (
    store_sk          bigint primary key,
    store_id          varchar(16) unique,
    store_name        varchar(255),
    banner            varchar(64),
    region            varchar(64),
    country_iso2      varchar(2),
    format            varchar(32),
    lp_staffing_tier  varchar(8),
    eas_enabled       boolean,
    rfid_enabled      boolean,
    status            varchar(16),
    valid_from        timestamp,
    valid_to          timestamp,
    is_current        boolean
);

create table if not exists loss_prevention_dim.dim_product_lp (
    product_sk         bigint primary key,
    item_id            varchar(32) unique,
    gtin               varchar(14),
    department         varchar(64),
    category           varchar(64),
    unit_cost_minor    bigint,
    unit_retail_minor  bigint,
    craved_score       numeric(4,2),
    eas_protected      boolean,
    rfid_tagged        boolean
);

create table if not exists loss_prevention_dim.dim_employee (
    employee_sk         bigint primary key,
    employee_id         varchar(16) unique,
    employee_ref_hash   varchar(64),                 -- still hashed in dim
    home_store_id       varchar(16),
    role                varchar(32),
    status              varchar(16),
    valid_from          timestamp,
    valid_to            timestamp,
    is_current          boolean
);

create table if not exists loss_prevention_dim.dim_incident_type (
    incident_type_sk   smallint primary key,
    incident_type      varchar(32) unique,
    severity_tier      varchar(8),                  -- high|medium|low
    reportable_nibrs   boolean,
    description        text
);

create table if not exists loss_prevention_dim.dim_exception_type (
    exception_type_sk  smallint primary key,
    exception_type     varchar(32) unique,
    rule_family        varchar(32),                  -- void_abuse|refund|sweethearting|cash_skim|discount
    description        text
);

-- ---------- FACTS ----------
create table if not exists loss_prevention_dim.fct_exceptions (
    exception_id          varchar(32) primary key,
    date_key              integer references loss_prevention_dim.dim_date_lp(date_key),
    store_sk              bigint  references loss_prevention_dim.dim_store_lp(store_sk),
    employee_sk           bigint  references loss_prevention_dim.dim_employee(employee_sk),
    exception_type_sk     smallint references loss_prevention_dim.dim_exception_type(exception_type_sk),
    transaction_id        varchar(32),
    exception_score       numeric(5,3),
    source_system         varchar(32),
    amount_at_risk_minor  bigint,
    is_open               boolean,
    is_closed_confirmed   boolean,
    is_closed_unfounded   boolean,
    detected_at           timestamp
);

create table if not exists loss_prevention_dim.fct_incidents (
    incident_id          varchar(32) primary key,
    date_key             integer references loss_prevention_dim.dim_date_lp(date_key),
    store_sk             bigint  references loss_prevention_dim.dim_store_lp(store_sk),
    incident_type_sk     smallint references loss_prevention_dim.dim_incident_type(incident_type_sk),
    suspect_id           varchar(32),
    detected_via         varchar(32),
    gross_loss_minor     bigint,
    recovered_minor      bigint,
    net_loss_minor       bigint,
    nibrs_code           varchar(8),
    is_open              boolean,
    is_closed_recovered  boolean,
    is_closed_prosecuted boolean,
    is_closed_writeoff   boolean,
    incident_ts          timestamp
);

create table if not exists loss_prevention_dim.fct_investigations (
    investigation_id          varchar(32) primary key,
    date_key                  integer references loss_prevention_dim.dim_date_lp(date_key),
    incident_id               varchar(32),
    store_sk                  bigint  references loss_prevention_dim.dim_store_lp(store_sk),
    investigation_type        varchar(32),
    status                    varchar(16),
    evidence_count            integer,
    video_evidence_minutes    integer,
    duration_hours            numeric(10,2),
    prosecution_referred      boolean,
    alto_shared               boolean,
    opened_at                 timestamp,
    closed_at                 timestamp
);

create table if not exists loss_prevention_dim.fct_recoveries (
    recovery_id              varchar(32) primary key,
    date_key                 integer references loss_prevention_dim.dim_date_lp(date_key),
    incident_id              varchar(32),
    investigation_id         varchar(32),
    store_sk                 bigint  references loss_prevention_dim.dim_store_lp(store_sk),
    recovered_amount_minor   bigint,
    recovery_type            varchar(32),
    recovered_at             timestamp
);

create table if not exists loss_prevention_dim.fct_shrink_snapshot (
    snapshot_id              varchar(32) primary key,
    date_key                 integer references loss_prevention_dim.dim_date_lp(date_key),
    store_sk                 bigint  references loss_prevention_dim.dim_store_lp(store_sk),
    department               varchar(64),
    period_start             date,
    period_end               date,
    opening_inventory_minor  bigint,
    receipts_minor           bigint,
    cogs_minor               bigint,
    closing_inventory_minor  bigint,
    known_shrink_minor       bigint,
    unknown_shrink_minor     bigint,
    total_shrink_minor       bigint,
    shrink_pct               numeric(6,4)
);

-- Helpful indexes
create index if not exists ix_fct_exc_date    on loss_prevention_dim.fct_exceptions(date_key);
create index if not exists ix_fct_exc_store   on loss_prevention_dim.fct_exceptions(store_sk);
create index if not exists ix_fct_inc_date    on loss_prevention_dim.fct_incidents(date_key);
create index if not exists ix_fct_inc_store   on loss_prevention_dim.fct_incidents(store_sk);
create index if not exists ix_fct_inv_store   on loss_prevention_dim.fct_investigations(store_sk);
create index if not exists ix_fct_rec_date    on loss_prevention_dim.fct_recoveries(date_key);
create index if not exists ix_fct_shr_store   on loss_prevention_dim.fct_shrink_snapshot(store_sk);
