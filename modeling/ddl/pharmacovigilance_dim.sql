-- =============================================================================
-- Pharmacovigilance — dimensional mart (excerpt)
-- Star schema for case throughput, signal detection, submission timeliness.
-- =============================================================================

create schema if not exists pharmacovigilance_dim;

create table if not exists pharmacovigilance_dim.dim_date (
    date_key             integer primary key,
    date_actual          date not null,
    day_of_week          smallint not null,
    fiscal_period        varchar(8)
);

create table if not exists pharmacovigilance_dim.dim_product (
    product_key          bigint primary key,
    product_id           varchar not null,
    brand_name           varchar not null,
    inn                  varchar not null,
    atc_code             varchar(8),
    therapeutic_area     varchar(64),
    valid_from           timestamp not null,
    valid_to             timestamp,
    is_current           boolean not null
);

create table if not exists pharmacovigilance_dim.dim_meddra (
    meddra_key           bigint primary key,
    pt_code              varchar(16) not null,
    pt_name              varchar not null,
    soc_code             varchar(16) not null,
    soc_name             varchar not null,
    hlt_code             varchar(16),
    hlgt_code            varchar(16)
);

create table if not exists pharmacovigilance_dim.dim_authority (
    authority_key        smallint primary key,
    authority_code       varchar(16) not null,
    authority_name       varchar(64) not null,
    region               varchar(32) not null
);

create table if not exists pharmacovigilance_dim.dim_seriousness (
    seriousness_key      smallint primary key,
    seriousness_code     varchar(16) not null,
    seriousness_label    varchar(32) not null
);

create table if not exists pharmacovigilance_dim.dim_intake_channel (
    channel_key          smallint primary key,
    channel_code         varchar(16) not null,
    channel_name         varchar(32) not null
);

create table if not exists pharmacovigilance_dim.dim_country (
    country_key          smallint primary key,
    country_iso2         varchar(2) not null,
    country_name         varchar(64) not null,
    region               varchar(32) not null
);

create table if not exists pharmacovigilance_dim.fact_icsr (
    icsr_id              varchar primary key,
    intake_date_key      integer not null references pharmacovigilance_dim.dim_date(date_key),
    closed_date_key      integer references pharmacovigilance_dim.dim_date(date_key),
    product_key          bigint not null references pharmacovigilance_dim.dim_product(product_key),
    primary_meddra_key   bigint references pharmacovigilance_dim.dim_meddra(meddra_key),
    seriousness_key      smallint not null references pharmacovigilance_dim.dim_seriousness(seriousness_key),
    channel_key          smallint not null references pharmacovigilance_dim.dim_intake_channel(channel_key),
    country_key          smallint references pharmacovigilance_dim.dim_country(country_key),
    case_version         smallint not null,
    processing_days      integer,
    is_expedited         boolean not null
);

create table if not exists pharmacovigilance_dim.fact_submission (
    submission_id        varchar primary key,
    icsr_id              varchar not null references pharmacovigilance_dim.fact_icsr(icsr_id),
    submitted_date_key   integer references pharmacovigilance_dim.dim_date(date_key),
    due_date_key         integer not null references pharmacovigilance_dim.dim_date(date_key),
    authority_key        smallint not null references pharmacovigilance_dim.dim_authority(authority_key),
    on_time              boolean,
    transmission_status  varchar(16) not null
);

create table if not exists pharmacovigilance_dim.fact_signal (
    signal_id            varchar primary key,
    detected_date_key    integer not null references pharmacovigilance_dim.dim_date(date_key),
    product_key          bigint not null references pharmacovigilance_dim.dim_product(product_key),
    meddra_key           bigint not null references pharmacovigilance_dim.dim_meddra(meddra_key),
    detection_method     varchar(32) not null,
    disproportionality   numeric(8, 4),
    status               varchar(16) not null,
    label_change_recommended boolean not null default false
);

create table if not exists pharmacovigilance_dim.fact_case_volume_daily (
    date_key             integer not null references pharmacovigilance_dim.dim_date(date_key),
    product_key          bigint not null references pharmacovigilance_dim.dim_product(product_key),
    seriousness_key      smallint not null references pharmacovigilance_dim.dim_seriousness(seriousness_key),
    icsrs_received       integer not null,
    icsrs_closed         integer not null,
    avg_processing_days  numeric(8, 2),
    primary key (date_key, product_key, seriousness_key)
);
