-- =============================================================================
-- Returns & Reverse Logistics — 3NF schema
-- Source standards (verbatim where the spec names a field):
--   GS1 EPCIS 2.0 — event-level traceability for returned goods.
--     https://www.gs1.org/standards/epcis
--   ASC X12 EDI 180 — Return Merchandise Authorization & Notification.
--     https://www.x12.org
--   ISO 14040 / 14044 / 14067 — life-cycle / carbon-footprint references for
--     scope-3 reverse-leg emissions.
--   GS1 GTIN-14 — primary item identifier.
--   PCI DSS v4.0 — applies when a refund hits an original card PAN.
-- =============================================================================

create schema if not exists returns_reverse_logistics;

-- Buying customer. PII-tokenized; raw demographics live in the CRM only.
create table if not exists returns_reverse_logistics.customer (
    customer_id              varchar(32) primary key,
    customer_ref_hash        varchar(64),                       -- SHA-256(loyalty_id + tenant-salt)
    country_iso2             varchar(2),
    loyalty_tier             varchar(16),                       -- bronze|silver|gold|platinum|none
    lifetime_orders          integer,
    lifetime_returns         integer,
    chronic_returner_flag    boolean,                           -- Newmine + internal model
    chronic_returner_score   numeric(5,3),                      -- 0..1
    status                   varchar(16),                       -- active|restricted|blocked
    created_at               timestamp
);

-- Original outbound sales order — joined for COGS / channel / ship-from node.
create table if not exists returns_reverse_logistics.sales_order (
    order_id          varchar(32) primary key,
    customer_id       varchar(32) references returns_reverse_logistics.customer(customer_id),
    channel           varchar(16),                              -- ecom|store|marketplace|wholesale
    order_ts          timestamp,
    ship_node         varchar(32),
    subtotal_minor    bigint,
    shipping_minor    bigint,
    tax_minor         bigint,
    total_minor       bigint,
    currency          varchar(3)
);

-- Reason code catalog — normalized from Loop/Narvar/Optoro/Newmine feeds.
create table if not exists returns_reverse_logistics.reason_code (
    reason_code_id        varchar(16) primary key,
    reason_code           varchar(32),
    reason_category       varchar(32),                          -- fit|quality|wrong_item|damaged|changed_mind|late|gift|wardrobing|fraud_suspected|other
    customer_facing_text  varchar(255),
    defect_attribution    varchar(32),                          -- supplier|carrier|merchant|customer|unknown
    actionable            boolean,
    severity              varchar(8)                            -- low|medium|high|critical
);

-- Disposition lane catalog — Optoro / Manhattan WMS / SAP S/4 Returns.
create table if not exists returns_reverse_logistics.disposition (
    disposition_id        varchar(16) primary key,
    disposition_code      varchar(32),                          -- restock_A|restock_open_box|refurb|b_stock_liquidation|donation|recycle|scrap|returnless
    disposition_name      varchar(64),
    target_channel        varchar(32),                          -- primary_inventory|open_box|b_stock_marketplace|donation_partner|recycler|landfill|n/a
    typical_recovery_pct  numeric(5,3),                         -- empirical recovery fraction
    lane_owner            varchar(64)                           -- Optoro|Manh_Active_WMS|SAP_S4_Returns|in_house_CRC|Good360|Liquidation_com|B-Stock|local_recycler
);

-- RMA — issued before the customer ships back or appears at a Return Bar / store. Maps to EDI 180.
create table if not exists returns_reverse_logistics.return_authorization (
    rma_id                          varchar(32) primary key,
    order_id                        varchar(32) references returns_reverse_logistics.sales_order(order_id),
    customer_id                     varchar(32) references returns_reverse_logistics.customer(customer_id),
    issued_ts                       timestamp,
    expires_ts                      timestamp,
    return_method                   varchar(32),                -- mail|boris_store|happy_returns_bar|doddle_qr|carrier_pickup|locker|returnless
    return_platform                 varchar(32),                -- Loop|Narvar|Optoro|HappyReturns|ReBound|ZigZag|Doddle|in_house|Salesforce_OMS|SAP_S4_Returns|Manh_Active_WMS
    carrier                         varchar(16),                -- USPS|UPS|FedEx|Hermes|EVRi|YunExpress|HappyReturns|n/a
    tracking_number                 varchar(64),
    cross_border                    boolean,
    source_country_iso2             varchar(2),
    destination_country_iso2        varchar(2),
    rma_status                      varchar(16),                -- issued|in_transit|received|cancelled|expired
    restocking_fee_eligible_minor   bigint,
    epcis_event_uri                 text                        -- GS1 EPCIS 2.0 object event pointer
);

-- One returned SKU / unit on an RMA. The grain of disposition / refurb / recovery analytics.
create table if not exists returns_reverse_logistics.return_item (
    return_item_id          varchar(32) primary key,
    rma_id                  varchar(32) references returns_reverse_logistics.return_authorization(rma_id),
    order_id                varchar(32) references returns_reverse_logistics.sales_order(order_id),
    sku_id                  varchar(32),
    gtin                    varchar(14),                        -- GS1 GTIN-14
    category                varchar(64),
    quantity                integer,
    unit_cogs_minor         bigint,
    unit_retail_minor       bigint,
    reason_code_id          varchar(16) references returns_reverse_logistics.reason_code(reason_code_id),
    condition_grade         varchar(8),                         -- A|B|C|D|scrap
    disposition_id          varchar(16) references returns_reverse_logistics.disposition(disposition_id),
    disposition_decided_ts  timestamp,
    serial_number           varchar(64)
);

-- Money / credit issued back to the customer. May or may not be tied to a return_item (returnless).
create table if not exists returns_reverse_logistics.refund (
    refund_id                       varchar(32) primary key,
    rma_id                          varchar(32),
    order_id                        varchar(32) references returns_reverse_logistics.sales_order(order_id),
    customer_id                     varchar(32) references returns_reverse_logistics.customer(customer_id),
    refund_type                     varchar(16),                -- original_tender|store_credit|exchange|gift_card|returnless
    refund_amount_minor             bigint,
    currency                        varchar(3),
    restocking_fee_collected_minor  bigint,
    issued_ts                       timestamp,
    psp_refund_id                   varchar(64),                -- Stripe re_*, PayPal txn id, Adyen pspReference
    payment_rail                    varchar(16),                -- card|ach|paypal|store_credit|gift_card|crypto
    status                          varchar(16)                 -- pending|issued|failed|reversed
);

-- Refurb / CRC outcome — one row per return_item per refurb attempt.
create table if not exists returns_reverse_logistics.refurb_outcome (
    refurb_outcome_id              varchar(32) primary key,
    return_item_id                 varchar(32) references returns_reverse_logistics.return_item(return_item_id),
    crc_id                         varchar(16),
    started_ts                     timestamp,
    completed_ts                   timestamp,
    labor_minutes                  integer,
    parts_cost_minor               bigint,
    outcome                        varchar(32),                 -- refurbed_A|refurbed_B|refurbed_open_box|scrapped|sent_to_liquidation|returned_to_vendor
    post_refurb_grade              varchar(8),                  -- A|B|C|scrap
    post_refurb_resale_value_minor bigint
);

-- Multi-item liquidation lot sold through B-Stock / Liquidation.com / BULQ.
create table if not exists returns_reverse_logistics.liquidation_lot (
    lot_id              varchar(32) primary key,
    marketplace         varchar(32),                            -- B-Stock|Liquidation_com|BULQ|Direct_Liquidation|eBay_B-Stock|Optoro_OptiTurn
    lot_name            varchar(255),
    item_count          integer,
    total_cogs_minor    bigint,
    starting_bid_minor  bigint,
    winning_bid_minor   bigint,
    proceeds_minor      bigint,
    currency            varchar(3),
    listed_ts           timestamp,
    sold_ts             timestamp,
    buyer_country_iso2  varchar(2),
    recovery_pct        numeric(6,4)
);

-- Bridge — many return_items into one lot.
create table if not exists returns_reverse_logistics.liquidation_lot_item (
    lot_item_id              varchar(32) primary key,
    lot_id                   varchar(32) references returns_reverse_logistics.liquidation_lot(lot_id),
    return_item_id           varchar(32) references returns_reverse_logistics.return_item(return_item_id),
    allocated_cogs_minor     bigint,
    allocated_proceeds_minor bigint
);

-- Per-return / per-customer fraud signal (Newmine / Appriss-style / internal).
create table if not exists returns_reverse_logistics.fraud_signal (
    fraud_signal_id  varchar(32) primary key,
    rma_id           varchar(32),
    customer_id      varchar(32) references returns_reverse_logistics.customer(customer_id),
    source           varchar(32),                               -- Newmine|Appriss_Retail|internal_xgb|Loop_workflow|Narvar_rule|Optoro_flag
    signal_type      varchar(32),                               -- wardrobing|serial_returner|wrong_item_swap|empty_box|receipt_fraud|cross_border_abuse|return_to_different_store|chronic_returner
    score            numeric(5,3),                              -- 0..1
    recommendation   varchar(16),                               -- approve|verify|deny|stepup_required
    scored_at        timestamp
);

-- Reverse-leg shipping label — Loop / Happy Returns / Doddle / ZigZag / ReBound.
create table if not exists returns_reverse_logistics.carrier_label (
    label_id              varchar(32) primary key,
    rma_id                varchar(32) references returns_reverse_logistics.return_authorization(rma_id),
    carrier               varchar(16),
    service_level         varchar(32),                          -- ground|expedited|consolidation|drop_off_qr|return_bar
    label_cost_minor      bigint,
    prepaid_by_merchant   boolean,
    created_ts            timestamp,
    scanned_ts            timestamp,
    delivered_ts          timestamp,
    status                varchar(16),                          -- issued|in_transit|delivered|exception|void
    scope3_kg_co2e        numeric(8,3)                          -- ISO 14040/14067 reverse-leg emissions
);

-- Helpful indexes on cardinality + time.
create index if not exists ix_rma_order              on returns_reverse_logistics.return_authorization(order_id);
create index if not exists ix_rma_customer           on returns_reverse_logistics.return_authorization(customer_id);
create index if not exists ix_rma_status             on returns_reverse_logistics.return_authorization(rma_status);
create index if not exists ix_ri_rma                 on returns_reverse_logistics.return_item(rma_id);
create index if not exists ix_ri_disposition         on returns_reverse_logistics.return_item(disposition_id);
create index if not exists ix_ri_reason              on returns_reverse_logistics.return_item(reason_code_id);
create index if not exists ix_refund_order           on returns_reverse_logistics.refund(order_id);
create index if not exists ix_refund_customer        on returns_reverse_logistics.refund(customer_id);
create index if not exists ix_refurb_item            on returns_reverse_logistics.refurb_outcome(return_item_id);
create index if not exists ix_lot_bridge_lot         on returns_reverse_logistics.liquidation_lot_item(lot_id);
create index if not exists ix_lot_bridge_item        on returns_reverse_logistics.liquidation_lot_item(return_item_id);
create index if not exists ix_fraud_customer         on returns_reverse_logistics.fraud_signal(customer_id);
create index if not exists ix_label_rma              on returns_reverse_logistics.carrier_label(rma_id);
