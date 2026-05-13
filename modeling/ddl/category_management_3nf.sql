-- =============================================================================
-- Category Management — 3NF schema
-- Source standards (verbatim where the spec names a field):
--   GS1 GTIN-14 / GLN / GDSN / GPC / Attribute Standard
--   ASC X12 EDI 852 (Product Activity Data) / EDI 867 (Resale) / EDI 832 (Price)
--   Blue Yonder Space Planning (planogram XML / PSA / POG)
--   Symphony RetailAI CINDE / Category Manager
--   Circana Unify / NielsenIQ Connect / Numerator / Kantar Worldpanel / dunnhumby
--   RELEX Solutions (assortment + space + floor planning)
-- =============================================================================

create schema if not exists category_management;

-- Category hierarchy node (total_store -> department -> category -> subcategory -> segment)
create table if not exists category_management.category (
    category_id          varchar(32) primary key,
    category_name        varchar(128),
    parent_category_id   varchar(32),
    category_level       varchar(16),                 -- total_store|department|category|subcategory|segment
    category_role        varchar(16),                 -- destination|routine|occasional_seasonal|convenience
    linear_ft_target     numeric(10,2),
    gpc_brick            varchar(16),                  -- GS1 GPC brick code
    status               varchar(16),
    created_at           timestamp
);

-- Manufacturer SKU as scoped for category-management decisions.
create table if not exists category_management.sku (
    sku_id               varchar(32) primary key,
    gtin                 varchar(14),                  -- GS1 GTIN-14
    brand                varchar(64),
    sub_brand            varchar(64),
    manufacturer         varchar(128),
    category_id          varchar(32) references category_management.category(category_id),
    pack_size            varchar(32),
    case_pack_qty        smallint,
    width_cm             numeric(8,2),                 -- facing dimensions
    height_cm            numeric(8,2),
    depth_cm             numeric(8,2),
    weight_g             integer,
    list_price_cents     bigint,
    srp_cents            bigint,
    cost_of_goods_cents  bigint,
    private_label_flag   boolean,
    launch_date          date,
    lifecycle_stage      varchar(16),                  -- intro|grow|core|decline|discontinued
    status               varchar(16)
);

-- Attribute hierarchy values per SKU — input to consumer decision tree.
create table if not exists category_management.sku_attribute (
    sku_id            varchar(32) references category_management.sku(sku_id),
    attribute_name    varchar(64),
    attribute_value   varchar(128),
    attribute_level   smallint,
    source_system     varchar(32),
    primary key (sku_id, attribute_name)
);

-- Retailer store outlet within category-management scope.
create table if not exists category_management.store (
    store_id            varchar(32) primary key,
    banner              varchar(64),
    store_number        varchar(16),
    gln                 varchar(13),                    -- GS1 GLN
    country_iso2        varchar(2),
    state_region        varchar(8),
    postal_code         varchar(16),
    format              varchar(32),                    -- supercenter|grocery|club|express|c-store
    cluster_id          varchar(32),
    shopper_segment     varchar(32),
    total_linear_ft     numeric(10,2),
    status              varchar(16)
);

-- Planogram header — authoritative shelf layout for a category × cluster × window.
create table if not exists category_management.planogram (
    planogram_id        varchar(32) primary key,
    category_id         varchar(32) references category_management.category(category_id),
    cluster_id          varchar(32),
    version             varchar(16),
    effective_from      date,
    effective_to        date,
    total_linear_ft     numeric(10,2),
    total_facings       integer,
    total_sku_count     integer,
    authoring_system    varchar(32),                    -- blueyonder_space|symphony_catman|relex|quad_tag|inhouse
    created_by          varchar(64),
    created_at          timestamp,
    approved_at         timestamp,
    status              varchar(16)                     -- draft|approved|in_market|superseded|killed
);

-- One position on a planogram — the grain of compliance audits.
create table if not exists category_management.planogram_position (
    position_id            varchar(40) primary key,
    planogram_id           varchar(32) references category_management.planogram(planogram_id),
    sku_id                 varchar(32) references category_management.sku(sku_id),
    shelf_number           smallint,
    position_index         smallint,
    facings                smallint,
    facing_depth           smallint,
    linear_ft_allocated    numeric(6,3),
    block_id               varchar(32),
    adjacency_left_sku     varchar(32),
    adjacency_right_sku    varchar(32),
    is_mandated            boolean,
    is_innovation_slot     boolean
);

-- Per store × SKU × week distribution-status fact (EDI 852 + syndicated panels).
create table if not exists category_management.distribution_record (
    distribution_record_id    varchar(40) primary key,
    store_id                  varchar(32) references category_management.store(store_id),
    sku_id                    varchar(32) references category_management.sku(sku_id),
    week_start_date           date,
    is_listed                 boolean,
    is_on_shelf               boolean,
    acv_weight                numeric(8,4),
    mandated_flag             boolean,
    compliant_flag            boolean,
    source_doc                varchar(16),               -- EDI_852|circana|niq|numerator|kantar|first_party
    ingested_at               timestamp
);

-- Syndicated POS / panel measurement at SKU × store(or geography) × week grain.
create table if not exists category_management.syndicated_measurement (
    measurement_id           varchar(40) primary key,
    sku_id                   varchar(32) references category_management.sku(sku_id),
    store_id                 varchar(32) references category_management.store(store_id),
    category_id              varchar(32) references category_management.category(category_id),
    gtin                     varchar(14),
    week_start_date          date,
    geography                varchar(32),
    units_sold               bigint,
    dollars_sold_cents       bigint,
    avg_retail_price_cents   bigint,
    market_share_pct         numeric(7,4),
    penetration_pct          numeric(7,4),
    buy_rate_units           numeric(10,2),
    any_promo_flag           boolean,
    source                   varchar(32),                -- circana|niq|numerator|kantar|gfk|first_party
    panel_id                 varchar(16),
    projection_factor        numeric(8,4),
    ingested_at              timestamp
);

-- A range-review cycle for a category × banner × season.
create table if not exists category_management.range_review (
    range_review_id                  varchar(32) primary key,
    category_id                      varchar(32) references category_management.category(category_id),
    banner                           varchar(64),
    cycle_name                       varchar(128),
    scheduled_date                   date,
    decision_date                    date,
    in_market_date                   date,
    sku_count_before                 integer,
    sku_count_after                  integer,
    sku_adds                         integer,
    sku_drops                        integer,
    forecast_category_sales_delta_cents bigint,
    forecast_margin_delta_cents      bigint,
    status                           varchar(16),
    led_by                           varchar(64),
    created_at                       timestamp
);

-- One SKU-level outcome from a range review.
create table if not exists category_management.range_review_decision (
    decision_id           varchar(40) primary key,
    range_review_id       varchar(32) references category_management.range_review(range_review_id),
    sku_id                varchar(32) references category_management.sku(sku_id),
    decision_type         varchar(16),                  -- add|drop|keep|mandate|cluster_restrict|reclass|repack
    cluster_scope         varchar(32),
    rationale             varchar(64),
    confidence            numeric(4,3),
    decision_authority    varchar(32),
    decided_at            timestamp
);

-- Store-level audit observation of planogram compliance.
create table if not exists category_management.planogram_compliance_audit (
    audit_id              varchar(40) primary key,
    store_id              varchar(32) references category_management.store(store_id),
    planogram_id          varchar(32) references category_management.planogram(planogram_id),
    audit_date            date,
    positions_audited     integer,
    positions_compliant   integer,
    missing_facings       integer,
    out_of_stock_count    integer,
    misplaced_sku_count   integer,
    extra_sku_count       integer,
    compliance_score      numeric(5,2),
    source                varchar(32),                  -- afs|sfdc_cg|numerator|niq_audit|inhouse
    photo_evidence_uri    text
);

-- Helpful indexes for time/cardinality
create index if not exists ix_cm_sku_category         on category_management.sku(category_id);
create index if not exists ix_cm_pog_position_pog     on category_management.planogram_position(planogram_id);
create index if not exists ix_cm_pog_position_sku     on category_management.planogram_position(sku_id);
create index if not exists ix_cm_dist_store_week      on category_management.distribution_record(store_id, week_start_date);
create index if not exists ix_cm_dist_sku_week        on category_management.distribution_record(sku_id, week_start_date);
create index if not exists ix_cm_meas_sku_week        on category_management.syndicated_measurement(sku_id, week_start_date);
create index if not exists ix_cm_meas_store_week      on category_management.syndicated_measurement(store_id, week_start_date);
create index if not exists ix_cm_rrd_rr               on category_management.range_review_decision(range_review_id);
create index if not exists ix_cm_audit_store_date     on category_management.planogram_compliance_audit(store_id, audit_date);
