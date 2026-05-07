# Data Availability Audit — Domain Explorer 116 Subdomains

**Author:** Domain Explorer research
**Date:** 2026-05-07
**Scope:** All 116 subdomains under `data/taxonomy/*.yaml`
**Question:** Which subdomains have enough public-domain data to build *fully attributed* anchor-grade data models, comparable to the seven existing anchors?

---

## TL;DR

Of the 116 subdomains, **66 are Tier 1** (public standards or open specs precise enough to model entities and attributes without imagination), **23 are Tier 2** (vendor public data dictionaries can be synthesised from 2–3 vendors), **18 are Tier 3** (mostly proprietary; any model would be largely speculation), and **9 are Tier 4** (formal standards exist but require paid membership or restricted access).

The seven existing anchors (Payments, P&C Claims, Merchandising, Demand Planning, Hotel Revenue Management, MES/Quality, Pharmacovigilance) sit inside the Tier 1/Tier 2 buckets. The next-most-valuable round of attribution should target the highest-leverage Tier 1 subdomains: **EHR Integrations** (FHIR), **Capital Markets** (FIX/FpML/ISO 20022), **Smart Metering** (ANSI C12 / DLMS-COSEM), **Clinical Trials** (CDISC SDTM/ADaM), **Cloud FinOps** (FOCUS 1.x), **EV Charging** (OCPP 2.0.1), **Tax Administration** (IRS MeF), **Real-World Evidence** (OMOP CDM v5.4), **Settlement & Clearing** (ISO 20022 securities messages), and **Ad Tech / Programmatic Advertising** (IAB OpenRTB / VAST). Each of these has a single, dominant, freely browsable spec that defines the bulk of the entity and attribute landscape.

The 18 Tier 3 subdomains — including Brand Marketing, Loyalty, Pricing, Bench Management, Knowledge Management, Airline Loyalty, Airline Revenue Management, Refinery Operations, Chip Design (EDA), Developer Relations, License Management, Marketplace Operations, Trade Promotion Management, Store Operations, Dark Stores, Warranty, Audit Workflow, Churn Management — are flagged as **not recommended for full attribution** without real customer datasets. Anything we ship for them today would be guessed.

---

## Method

### Tier definitions

- **Tier 1 — Public standards available.** A specific public standard, RFC, free spec, government schema, or open-source data model defines the entities and attributes precisely. A full anchor-grade model is possible without speculation. Cited inline.
- **Tier 2 — Vendor public data dictionary.** No single industry standard exists, but two or three dominant vendors publish enough of their public data dictionary or API reference that an anchor-grade model can be synthesised. Cited inline.
- **Tier 3 — Mostly proprietary / customer-specific.** Operational data lives inside vendor-specific schemas (or inside the customer's own warehouse) without a published reference model. **Any attribute-level model would be largely speculation without real customer data.** Not recommended.
- **Tier 4 — Standards exist but they're paid/restricted.** Formal standards (e.g. ACORD, IEC 61850, AIAG PPAP) exist and are precise, but reading the actual schema requires a paid membership or licensed copy. Building from these without paying is not safe; building *with* a membership is straightforward. Where a free vendor dictionary partially covers Tier 4 territory, we note it.

### Scope rules

The seven existing anchors are tagged inline with `[ANCHOR]`. They are included in the tier counts because they are part of the 116. The "recommended next anchors" list (at the end) excludes them.

For each subdomain we list the entities currently in `data/taxonomy/<id>.yaml`, plus 5–10 concrete entities we'd model from the cited public sources for Tier 1 / Tier 2 cases. Tier 3 entries explicitly do **not** propose attributes — that's the point.

---

## By Vertical

The verticals below match the `vertical:` field in the YAML files. Within each vertical, entries are sorted by tier (1 → 4) then alphabetically.

---

### BFSI (16 subdomains)

#### Payments (`payments`) [ANCHOR]

- **Tier 1.**
- **One-liner:** End-to-end money movement across rails (cards, ACH, wires, real-time) with auth, clearing, settlement, and dispute handling.
- **Standards / sources:**
  - ISO 20022 message catalogue (pacs.008, pacs.009, pain.001, camt.053): https://www.iso20022.org/iso-20022-message-definitions
  - ISO 8583 financial transaction message format (paid for full text via ISO; widely documented in vendor specs).
  - NACHA ACH file format & operating rules: https://www.nacha.org/rules
  - SWIFT MT message catalogue (paid via SWIFT, but every field documented in MyStandards).
  - Stripe API reference: https://docs.stripe.com/api
- **Note:** Already a fully-attributed anchor. The reason it works is that ISO 20022 and NACHA publish the field-level definitions; ISO 8583 is widely echoed by every card processor's docs.

#### Asset Management (`asset_management`)

- **Tier 1.**
- **One-liner:** Institutional and retail asset management: portfolios, IBOR, performance, and fees.
- **Standards / sources:**
  - SEC Form N-PORT (XBRL/XML monthly portfolio report): https://www.sec.gov/structureddata/n-port-data-sets
  - SEC Form ADV (investment adviser registration, public): https://www.sec.gov/about/forms/formadv.pdf
  - FpML (Financial products Markup Language) for derivative positions: https://www.fpml.org/
  - GIPS (Global Investment Performance Standards) — paid via CFA Institute, but performance methodology widely documented.
  - ISO 20022 securities messages (semt, sese): https://www.iso20022.org/
- **Concrete entities:** Portfolio, Holding, Lot, Transaction, Performance Period (TWR / IRR), Fee Schedule, Account, Mandate, Benchmark, Composite (GIPS).
- **Recommendation:** Build full model. Form N-PORT alone gives ~150 attributes per holding; FpML covers derivatives; GIPS covers performance reporting.

#### Capital Markets (`capital_markets`)

- **Tier 1.**
- **One-liner:** Front-to-back trade lifecycle for equities, FICC, and derivatives across execution, clearing, and settlement.
- **Standards / sources:**
  - FIX Protocol 4.4 / 5.0 SP2 / FIXatdl: https://www.fixtrading.org/standards/
  - FpML 5.x (rates, credit, equity derivatives, commodity): https://www.fpml.org/spec/
  - ISO 20022 securities (semt, sese, setr, reda): https://www.iso20022.org/
  - CFTC Part 43/45 swap data reporting fields list: https://www.cftc.gov/IndustryOversight/DataReporting
  - MiFID II RTS 22 transaction reporting (ESMA): https://www.esma.europa.eu/policy-rules/mifid-ii-and-mifir
  - SEC Rule 605/606 disclosure schemas: https://www.sec.gov/rules/final/34-43590.htm
- **Concrete entities:** Order, Execution Report, Trade, Allocation, Confirmation, Settlement Instruction, Position, Cash Account, Security Master, Counterparty, ISDA Master Agreement, Margin Call, Lifecycle Event (FpML).
- **Recommendation:** **Strong next-anchor candidate.** FIX defines pre-trade/execution; FpML defines post-trade derivative lifecycle; ISO 20022 defines securities clearing/settlement. Together they fully attribute the front-to-back model.

#### Cards (`cards`)

- **Tier 1.**
- **One-liner:** Issuing and acquiring of credit/debit/prepaid cards across schemes, lifecycle, and rewards.
- **Standards / sources:**
  - ISO/IEC 7812 (Issuer Identification Number / BIN): https://www.iso.org/standard/70484.html
  - ISO/IEC 7813 (track data) and ISO/IEC 7816 (smart cards): https://www.iso.org/standard/43317.html
  - EMVCo specifications (Books 1–4, Contactless A/B/C, 3-D Secure 2.x): https://www.emvco.com/specifications/
  - ISO 8583 message format (echoed in every card-network spec).
  - Visa CIS / Mastercard IPM clearing record layouts (paid via scheme membership; widely documented).
  - Marqeta API reference: https://www.marqeta.com/docs/core-api
  - Stripe Issuing API: https://docs.stripe.com/issuing
- **Concrete entities:** Cardholder, Card (PAN, expiry, CVV2), BIN/IIN Range, Authorization Request/Response, Capture, Chargeback, Dispute Cycle, Refund, Statement, Reward Accrual, Interchange Fee, Scheme Settlement File (TC33, IPM).
- **Recommendation:** Build full model. EMVCo + ISO 8583 cover the auth/clearing entities; scheme docs (Visa/Mastercard) cover settlement; Marqeta/Stripe cover lifecycle and rewards.

#### Cross-Border Payments (`cross_border_payments`)

- **Tier 1.**
- **One-liner:** FX-aware international remittances using SWIFT, RTP, and stablecoin rails.
- **Standards / sources:**
  - ISO 20022 cross-border messages (pacs.008/.009/.004, camt.053/.054, with CBPR+ usage guidelines): https://www.iso20022.org/
  - SWIFT CBPR+ (Cross-Border Payments and Reporting Plus) usage guidelines: https://www.swift.com/standards/iso-20022/cbpr-plus
  - SWIFT GPI tracker API: https://developer.swift.com/
  - FedNow ISO 20022 specs: https://www.federalreserve.gov/paymentsystems/fednow_about.htm
  - The Clearing House RTP message specs: https://www.theclearinghouse.org/payment-systems/rtp
  - UPI specifications (NPCI India): https://www.npci.org.in/what-we-do/upi/product-overview
- **Concrete entities:** Cross-Border Payment Instruction, FX Quote, FX Trade, Correspondent Leg, Settlement Account (Vostro/Nostro), GPI Tracker Event, Beneficiary, Sanctions Screening Hit, AML Hold, Compliance Reason Code.
- **Recommendation:** Build full model. CBPR+ alone is enough to fully attribute the message; GPI provides the lifecycle event model.

#### KYC & AML (`kyc_aml`)

- **Tier 1.**
- **One-liner:** Customer due diligence, sanctions screening, transaction monitoring, and SAR filing.
- **Standards / sources:**
  - FinCEN BSA E-Filing System schemas (SAR / CTR / FBAR XML): https://www.fincen.gov/resources/financial-institutions/bsa-e-filing-system
  - FinCEN Beneficial Ownership reporting schema (BOI): https://boiefiling.fincen.gov/
  - OFAC SDN list (XML, daily): https://ofac.treasury.gov/specially-designated-nationals-and-blocked-persons-list-sdn-human-readable-lists
  - UN Security Council Consolidated Sanctions List (XML): https://main.un.org/securitycouncil/en/content/un-sc-consolidated-list
  - EU Consolidated Financial Sanctions List: https://webgate.ec.europa.eu/fsd/fsf
  - FATF 40 Recommendations: https://www.fatf-gafi.org/en/topics/fatf-recommendations.html
  - goAML (UNODC): https://unite.un.org/goaml
- **Concrete entities:** Customer, Customer Due Diligence Record, Beneficial Owner, Sanctions Hit, PEP Match, Transaction Alert, Suspicious Activity Report (SAR), Currency Transaction Report (CTR), Watchlist Snapshot, Risk Score.
- **Recommendation:** Build full model. The FinCEN SAR XML schema alone defines ~80 attributes; OFAC and UN/EU sanctions lists give the watchlist entities; goAML covers the cross-border SAR exchange.

#### Lending (`lending`)

- **Tier 1.**
- **One-liner:** Origination through servicing for consumer, mortgage, and commercial loan portfolios.
- **Standards / sources:**
  - MISMO Reference Model v3.6 (logical data dictionary, XML schema): https://www.mismo.org/standards-resources/residential-specifications/reference-model
  - Uniform Residential Loan Application (URLA / Form 1003): https://singlefamily.fanniemae.com/applications-technology/urla
  - CFPB HMDA Loan/Application Register (LAR) submission specs: https://ffiec.cfpb.gov/documentation/2026/lar-data-fields/
  - Metro 2 credit furnishing format (CDIA) — paid for full spec, but field-level layout widely documented.
  - SBA 7(a) loan reporting (E-Tran data dictionary): https://www.sba.gov/partners/lenders/7a-loan-program/etran
- **Concrete entities:** Loan Application (URLA), Borrower, Co-Borrower, Property, Income Source, Asset, Liability, Loan, Disbursement, Payment, Escrow Account, Default Event, Charge-Off, HMDA LAR Record.
- **Recommendation:** Build full model. MISMO 3.6 alone defines several thousand data points across origination/servicing/closing.

#### Mortgage Servicing (`mortgage_servicing`)

- **Tier 1.**
- **One-liner:** Post-close loan administration — payments, escrow, default management, and investor reporting.
- **Standards / sources:**
  - MISMO Servicing Reference Model (extension of v3.6 above).
  - Fannie Mae Investor Reporting (LAR / Cash Remittance / SURF): https://singlefamily.fanniemae.com/servicing/investor-reporting
  - Freddie Mac Loan-Level Reporting: https://sf.freddiemac.com/servicing/loan-level-reporting
  - HUD Loss Mitigation reporting: https://www.hud.gov/program_offices/housing/sfh/sfhprocedures
  - Ginnie Mae MBS Pool reporting: https://www.ginniemae.gov/issuers/issuer_tools/Pages/multifamilyandissuermbsguide.aspx
- **Concrete entities:** Servicing Loan, Payment Posting, Escrow Disbursement, Tax/Insurance Bill, Delinquency Status, Loss Mitigation Workout, Foreclosure Event, Bankruptcy Stay, Investor Remittance, Investor LAR Record, MBS Pool.
- **Recommendation:** Build full model. MISMO + GSE investor-reporting field manuals give a complete picture.

#### Settlement & Clearing (`settlement_clearing`)

- **Tier 1.**
- **One-liner:** Net settlement, multilateral clearing, and reconciliation across CSDs, ACHs, and CCPs.
- **Standards / sources:**
  - ISO 20022 securities settlement messages (sese.023 settlement instruction, sese.024 status, semt.017 statement of holdings, camt.054 debit/credit notification): https://www.iso20022.org/
  - DTCC NSCC Continuous Net Settlement (CNS) record specs: https://www.dtcc.com/clearing-services/equities-clearing-services
  - DTCC DTC Settlement (BlueShift, ID Net): https://www.dtcc.com/settlement-and-asset-services/dtc-settlement
  - CHIPS / Fedwire formats (Fedwire Funds Service formats; ISO 20022 migration): https://www.frbservices.org/resources/financial-services/wires/index.html
  - SWIFT MT 535/536/537 (statement of holdings / transactions / pending): paid for full text but widely documented in operations manuals.
- **Concrete entities:** Settlement Instruction, Trade Match, Net Settlement Position, CCP Margin Call, Failed Trade, Buy-In, Pre-Settlement Matching Status, Cash Settlement Movement, Securities Movement, Reconciliation Break, CSD Account.
- **Recommendation:** **Strong next-anchor candidate.** ISO 20022 securities messages cover the full lifecycle.

#### Securities Lending (`securities_lending`)

- **Tier 1.**
- **One-liner:** Loans of securities to short-sellers and prime brokers — collateral, fees, and recall management.
- **Standards / sources:**
  - ESMA SFTR (Securities Financing Transactions Regulation) ISO 20022 schemas (auth.052, auth.060, auth.070): https://www.esma.europa.eu/policy-rules/sftr
  - SEC Rule 10c-1a (NSCC sec lending reporting) public order: https://www.sec.gov/rules/final/2023/34-98737.pdf
  - ISLA Global Master Securities Lending Agreement (GMSLA): https://www.islaemea.org/legal/gmsla/
  - FpML securities lending package: https://www.fpml.org/spec/
  - DTCC SFT Clearing service docs: https://www.dtcc.com/clearing-services/sft-clearing
- **Concrete entities:** Loan, Security on Loan, Borrow Contract, Collateral Schedule, Margin Call, Recall Notice, Rebate / Fee, Mark-to-Market, Default Event, SFTR Trade Report.
- **Recommendation:** Build full model. SFTR alone defines ~150 reporting attributes per loan.

#### Treasury Management (`treasury`)

- **Tier 1.**
- **One-liner:** Cash, liquidity, FX, and funding across the banking book to balance yield, capital, and resilience.
- **Standards / sources:**
  - ISO 20022 cash management (camt.052 BAI, camt.053 EOD statement, camt.054 debit/credit notification): https://www.iso20022.org/
  - SWIFT MT 940 / MT 942 customer statement (paid; documented in every TMS vendor spec).
  - BAI2 (Bank Administration Institute) statement format: https://www.bai.org/docs/default-source/libraries-data-management/bai2_complete_v3-7_2021.pdf
  - Federal Reserve H.15 rates (SOFR, EFFR): https://www.federalreserve.gov/releases/h15/
  - BAFT Standardized Bank Identifier Code (BIC).
- **Concrete entities:** Bank Account, Statement, Cash Position, Cash Forecast Bucket, FX Spot Trade, FX Forward, Money Market Deposit, Repo, Intraday Liquidity Event, Funding Concentration Limit.
- **Recommendation:** Build full model. ISO 20022 camt and BAI2 fully attribute statement-level entities.

#### Regulatory Reporting (`regulatory_reporting`)

- **Tier 1.**
- **One-liner:** Sourcing, transforming, and lodging supervisory reports (CCAR, COREP, MAS, etc.) with full lineage.
- **Standards / sources:**
  - FFIEC Call Report (FFIEC 031/041/051) MDRM (Micro Data Reference Manual): https://www.federalreserve.gov/apps/mdrm/
  - FR Y-9C / FR Y-14 (CCAR): https://www.federalreserve.gov/apps/reportforms/default.aspx
  - EBA COREP/FINREP XBRL taxonomy: https://www.eba.europa.eu/risk-and-data-analysis/reporting-frameworks
  - MAS 610: https://www.mas.gov.sg/regulation/forms-and-templates/regulatory-and-supervisory-framework
  - SEC EDGAR US-GAAP Taxonomy (XBRL): https://xbrl.us/xbrl-taxonomy/2024-us-gaap/
  - XBRL specification: https://specifications.xbrl.org/
- **Concrete entities:** Reporting Period, Regulatory Form, Form Line Item (MDRM), Counterparty Concentration, Capital Component (CET1, AT1, T2), Risk-Weighted Asset Bucket, Stress Scenario, Supervisory Submission, Reconciliation Break, Lineage Edge.
- **Recommendation:** Build full model. The MDRM dictionary alone defines ~10,000 reportable line items with formulas; XBRL provides the lineage/structure.

#### Wealth Management (`wealth_management`)

- **Tier 2.**
- **One-liner:** Advisory, portfolio management, and reporting for HNW and retail investors.
- **Standards / sources:** SEC Form ADV (Part 1 XML, Part 2 narrative): https://www.sec.gov/about/forms/formadv.pdf ; SEC Form CRS Customer Relationship Summary: https://www.sec.gov/about/forms/formcrs.pdf ; FINRA Rule 4530 reportable events: https://www.finra.org/rules-guidance/rulebooks/finra-rules/4530 ; Pershing NetX360 API docs: https://www.developer.bnymellon.com/ ; Envestnet ENV2 API; Charles Schwab Advisor API.
- **Concrete entities:** Advisor, Client Household, Goal/Plan, Risk Tolerance Profile, Account, Holding, Suitability Review, Fee Schedule, Performance Statement, Disclosure Document.
- **Recommendation:** Build full model from 2–3 vendors. Form ADV gives the firm-level entities; Pershing/Envestnet APIs cover the operational ones; the planning-side (e.g. eMoney, MoneyGuidePro) is more proprietary but documented at the API level.

#### Fraud & Financial Crime (`fraud`)

- **Tier 2.**
- **One-liner:** Detect, score, and disposition suspicious activity across cards, payments, and accounts.
- **Standards / sources:** FFIEC Authentication Guidance (and updates): https://www.ffiec.gov/press/PDF/Authentication-and-Access-to-Financial-Institution-Services-and-Systems.pdf ; FinCEN SAR/CTR (covered above); Visa Compelling Evidence 3.0 / Visa CE 3.0: https://usa.visa.com/dam/VCOM/global/support-legal/documents/visa-rules-public.pdf ; Mastercard Chargeback Reason Code Encyclopedia (paid but widely documented); FICO Falcon API limited public; NICE Actimize public marketing docs; Sift Console docs: https://sift.com/developers ; Stripe Radar rules: https://docs.stripe.com/radar/rules
- **Concrete entities:** Transaction, Risk Score, Rule Hit, Alert, Case, Disposition, Investigator Note, Fraud Reason Code, Recovery, Linked Identity Cluster.
- **Recommendation:** Build model from 2–3 vendor docs (Sift, Stripe Radar, plus card-scheme reason codes). The actual scoring logic is proprietary but the **entity** model is shared. Note that **fraud rules and model coefficients are NOT publicly modellable** — leave those abstract.

#### Merchant Acquiring (`merchant_acquiring`)

- **Tier 2.**
- **One-liner:** Onboarding, underwriting, and settlement of card-accepting merchants across MCCs.
- **Standards / sources:** Visa Implementation Guide / VOL clearing record (TC33/TC57; paid but widely documented); Mastercard IPM clearing record; ISO 18245 Merchant Category Codes: https://www.iso.org/standard/79450.html ; PCI DSS data flow definitions: https://www.pcisecuritystandards.org/ ; Stripe Connect API: https://docs.stripe.com/connect ; Adyen Marketpay: https://docs.adyen.com/marketpay/ ; Worldpay Acceptor docs.
- **Concrete entities:** Merchant Application, Merchant, Outlet/Terminal, MCC, Card Acceptance Agreement, Authorization, Capture, Settlement Funding, Reserve, Chargeback Recovery, Risk Underwriting Decision.
- **Recommendation:** Build from Stripe Connect + Adyen + ISO 18245 + Visa/MC clearing. Combined, these three sources fully cover the lifecycle.

#### Prepaid Cards (`prepaid_cards`)

- **Tier 2.**
- **One-liner:** Open and closed-loop prepaid card programs spanning gift, payroll, and benefits.
- **Standards / sources:** Marqeta Core API: https://www.marqeta.com/docs/core-api ; Galileo Pro: https://docs.galileo-ft.com/pro/ ; Stripe Issuing for closed-loop; CFPB Prepaid Account Rule (Reg E §1005.18) disclosure schemas; Network Branded Prepaid Card Association (NBPCA) glossary.
- **Concrete entities:** Card Program, Cardholder, Funding Source, Load, Card, Authorization, Negative Balance, Expiration, Disclosure Long Form, Cardholder Agreement.
- **Recommendation:** Build from Marqeta + Galileo + Reg E disclosures.

---

### Insurance (7 subdomains)

#### P&C Claims (`p_and_c_claims`) [ANCHOR]

- **Tier 1.**
- **One-liner:** First-notice-of-loss through adjudication, payout, and recovery for property & casualty claims.
- **Standards / sources:** ACORD claim, vehicle, property, FNOL forms — **Tier 4 (paid)**: https://www.acord.org/standards-architecture/acord-data-standards ; Guidewire ClaimCenter Cloud API & data dictionary (public): https://docs.guidewire.com/cloud/cc/ ; ISO ClaimSearch (Verisk) — paid; NAIC Annual Statement Schedule P loss development (free).
- **Note:** Already a fully-attributed anchor, built from a mix of paid ACORD + free Guidewire docs + NAIC public data.

#### Actuarial Pricing (`actuarial_pricing`)

- **Tier 1.**
- **One-liner:** Actuarial reserving, pricing models, and capital adequacy across lines of business.
- **Standards / sources:**
  - NAIC Annual Statement Instructions (Schedule P loss development triangles, Schedule F reinsurance, IRIS ratios): https://content.naic.org/cmte_e_app_blanks.htm
  - Solvency II QRT XBRL templates (EIOPA): https://www.eiopa.europa.eu/tools-and-data/supervisory-reporting-dpm-and-xbrl_en
  - SOA / CAS published research and exam syllabus materials: https://www.casact.org/ , https://www.soa.org/
  - NAIC Risk-Based Capital (RBC) instructions.
  - IFRS 17 disclosure illustrative examples (paid IASB but widely echoed).
- **Concrete entities:** Loss Development Triangle Cell, Reserve, Rate Class / Relativity, Pricing Model Run, Capital Scenario, Solvency II SCR Module, RBC Authorized Control Level, Benchmark Rate, Trend Curve, Catastrophe Load.
- **Recommendation:** Build full model. Schedule P alone gives row-level public data on every US insurer.

#### Claims & Subrogation (`claims_subrogation`)

- **Tier 2.**
- **One-liner:** Claims intake, adjudication, recovery, and subrogation across P&C and specialty lines.
- **Standards / sources:** Guidewire ClaimCenter docs (public): https://docs.guidewire.com/cloud/cc/ ; Mitchell Cloud Claims documentation (public): https://www.mitchell.com/insurance ; CCC ONE API: https://www.cccis.com/ ; Arbitration Forums (AF) data files (public for member insurers): https://www.arbfile.org/ ; NAIC Annual Statement Schedule F (reinsurance recoverables, public).
- **Concrete entities:** Claim, Loss Notice, Coverage, Reserve, Payment, Recovery, Subrogation Demand, Arbitration Filing, Salvage Disposition, Litigation Matter.
- **Recommendation:** Build from Guidewire + Mitchell + AF schemas. The subrogation-specific entities (demand letters, arbitration) are best documented by Arbitration Forums.

#### Policy Administration (`policy_admin`)

- **Tier 2.**
- **One-liner:** Core policy lifecycle: issuance, billing, endorsements, renewals, and cancellations across LOBs.
- **Standards / sources:** ACORD AL3 / P&C XML — Tier 4 (paid): https://www.acord.org/ ; Guidewire PolicyCenter docs (public): https://docs.guidewire.com/cloud/pc/ ; Duck Creek Policy public docs: https://www.duckcreek.com/ ; Majesco Policy data model docs (limited public); NAIC SERFF (System for Electronic Rate and Form Filing): https://www.serff.com/ filing schemas (free).
- **Concrete entities:** Policy, Policy Term, Insured / Producer, Coverage, Endorsement, Premium Schedule, Bill Plan, Cancellation Reason, Renewal Offer, SERFF Filing.
- **Recommendation:** Build from Guidewire + Duck Creek + SERFF. Anchor-quality possible without paying ACORD.

#### Life & Annuity (`life_annuity`)

- **Tier 4.**
- **One-liner:** Life insurance and annuity products covering issuance, in-force servicing, and benefits administration.
- **Standards / sources:**
  - ACORD Life & Annuity AML.XML — paid via ACORD: https://www.acord.org/standards-architecture/acord-data-standards
  - LIMRA member content — paid: https://www.limra.com/
  - DTCC Insurance Services (NSCC IPS / IFS) message specs — public for member firms only: https://www.dtcc.com/wealth-management-services/insurance-services
  - NAIC Annual Statement Life Blue Book — free: https://content.naic.org/cmte_e_app_blanks.htm
- **Concrete entities (would require ACORD/LIMRA membership for full attribute lists):** Policy, Insured, Beneficiary, Annuity Contract, Premium, Death Claim, Surrender, Annuitization Election, Reserve.
- **Recommendation:** **Hold pending ACORD or LIMRA membership.** NAIC Blue Book + DTCC IFS provide a partial entity list, but attribute-level fidelity needs ACORD AML.XML or vendor (Equisoft, FAST) docs that are member-only.

#### Reinsurance (`reinsurance`)

- **Tier 4.**
- **One-liner:** Treaty and facultative reinsurance ceded to balance net retention and capital.
- **Standards / sources:**
  - ACORD Reinsurance Standards (RUR / GRLC / GRPS) — paid: https://www.acord.org/standards-architecture/acord-data-standards
  - Lloyd's Market Association (LMA) clauses and contract certainty — semi-public: https://www.lmalloyds.com/
  - Lloyd's Coverholder reporting standards (CRS): https://www.lloyds.com/conducting-business/delegated-authorities
  - SCOR / Munich Re / Swiss Re internal models — proprietary.
  - NAIC Schedule F (cessions / recoverables) — public, but only at portfolio level.
- **Concrete entities (attribute fidelity blocked without ACORD):** Treaty, Facultative Cession, Bordereau (Premium / Claim), Retention Layer, Reinstatement Premium, Letter of Credit, Recoverable, Commutation.
- **Recommendation:** **Hold pending ACORD membership.** Modelling without it would require imagining bordereau structures.

#### Underwriting (`underwriting`)

- **Tier 4.**
- **One-liner:** Risk selection, pricing, and policy issuance across personal, commercial, and specialty lines.
- **Standards / sources:**
  - ACORD AL3 / P&C XML — paid.
  - Verisk ISO Statistical Plans (PPA, BOP, GL, etc.) — paid: https://www.verisk.com/
  - NCCI Workers Comp Statistical Plan — paid: https://www.ncci.com/
  - LexisNexis C.L.U.E. / current carrier — paid.
  - NAIC SERFF — public for filings: https://www.serff.com/
  - Lemonade / Hippo / Root Insurance public quote APIs — limited.
- **Concrete entities (attribute fidelity blocked without Verisk/ACORD):** Submission, Risk Object (Auto / Property / GL), Underwriting Question, Quote, Rating Engine Run, Bind, Issued Policy, Loss Run, Premium Bureau Code.
- **Recommendation:** **Hold pending Verisk/NCCI/ACORD access.** Without paid stat plans, attribute lists for rating bureaus are speculation.

---

### Healthcare (8 subdomains)

#### EHR Integrations (`ehr_integrations`)

- **Tier 1.**
- **One-liner:** Bidirectional clinical data flow between EHRs (Epic, Cerner) and downstream analytics, payer, and engagement systems.
- **Standards / sources:**
  - HL7 FHIR R4 / R5 (Patient, Encounter, Observation, MedicationRequest, ServiceRequest, DiagnosticReport, etc.): https://hl7.org/fhir/
  - HL7 v2.x message standards (ADT, ORM, ORU, SIU): https://www.hl7.org/implement/standards/product_section.cfm?section=13
  - IHE profiles (XDS, PIX/PDQ, ATNA, BPPC): https://profiles.ihe.net/
  - USCDI v3 (US Core Data for Interoperability): https://www.healthit.gov/isa/united-states-core-data-interoperability-uscdi
  - Epic on FHIR: https://fhir.epic.com/
  - Oracle Health Millennium FHIR APIs: https://docs.oracle.com/en/industries/health/millennium-platform-apis/
- **Concrete entities:** Patient, Encounter, Observation, Condition, Procedure, MedicationRequest, MedicationAdministration, AllergyIntolerance, Immunization, DiagnosticReport, ServiceRequest, Practitioner, Organization, Location, Coverage.
- **Recommendation:** **Strong next-anchor candidate.** FHIR R4 + USCDI v3 alone fully attribute the model; Epic and Oracle Health publish nearly identical resources. This is the single highest-leverage Tier 1 in healthcare.

#### Clinical Decision Support (`clinical_decision_support`)

- **Tier 1.**
- **One-liner:** Evidence-based alerts and order sets at the point of care, integrated with EHR.
- **Standards / sources:**
  - HL7 FHIR Clinical Reasoning module (PlanDefinition, ActivityDefinition, Library, Measure): https://hl7.org/fhir/clinicalreasoning-module.html
  - CDS Hooks v2.0 (HL7): https://cds-hooks.hl7.org/2.0/
  - CQL (Clinical Quality Language): https://cql.hl7.org/
  - SMART on FHIR launch framework: https://www.hl7.org/fhir/smart-app-launch/
- **Concrete entities:** Hook Trigger, CDS Service, CDS Card, PlanDefinition, ActivityDefinition, CQL Library, Suggestion, Override / Acceptance, Audit Event.
- **Recommendation:** Build full model. CDS Hooks alone fully attributes the request/response/card schema.

#### Medical Imaging (`medical_imaging`)

- **Tier 1.**
- **One-liner:** Radiology and imaging operations: PACS, RIS, AI triage, and reporting workflow.
- **Standards / sources:**
  - DICOM PS3 (Parts 3, 4, 6, 16, 18, 20): https://www.dicomstandard.org/current
  - HL7 FHIR ImagingStudy / ImagingSelection: https://hl7.org/fhir/imagingstudy.html
  - IHE Radiology Technical Framework: https://profiles.ihe.net/RAD/
  - DICOMweb (QIDO-RS, WADO-RS, STOW-RS): https://www.dicomstandard.org/dicomweb
  - RSNA RadLex ontology: https://radlex.org/
- **Concrete entities:** ImagingStudy, Series, Instance (SOP), Modality, Procedure Code (LOINC / SNOMED / RadLex), DICOM SR Report, AI Algorithm Output, Critical Finding, Worklist Item, Reporting Template.
- **Recommendation:** Build full model. DICOM PS3 is exhaustive.

#### Patient Engagement (`patient_engagement`)

- **Tier 1.**
- **One-liner:** Patient portals, messaging, reminders, and digital front-door experiences.
- **Standards / sources:**
  - HL7 FHIR Communication, CommunicationRequest, Appointment, Schedule, Slot: https://hl7.org/fhir/
  - SMART App Launch: https://www.hl7.org/fhir/smart-app-launch/
  - Da Vinci Patient Cost Transparency: https://hl7.org/fhir/us/davinci-pct/
  - CMS Patient Access API (Blue Button 2.0): https://bluebutton.cms.gov/developers/
- **Concrete entities:** Patient Account, Portal Session, Secure Message Thread, Appointment, Reminder Job, Consent, Notification Preference, Outreach Campaign, Engagement Event, Authorization (SMART scope).
- **Recommendation:** Build full model.

#### Payer-Provider Operations (`payer_provider`)

- **Tier 1.**
- **One-liner:** Claims adjudication, member enrolment, and provider network management for health plans.
- **Standards / sources:**
  - HIPAA EDI ASC X12 (270/271 eligibility, 276/277 claim status, 278 prior auth, 837P/I/D claim, 835 remittance, 820 premium): https://x12.org/products/transaction-sets — paid X12, but every payer publishes companion guides.
  - CAQH CORE Operating Rules: https://www.caqh.org/core/all-operating-rules
  - CMS NCPDP D.0 / SCRIPT (pharmacy): https://standards.ncpdp.org/ — paid; widely echoed.
  - HL7 FHIR US Core, Da Vinci PDex, CARIN BB IG, Da Vinci PAS prior auth: https://hl7.org/fhir/us/davinci-pas/
  - CMS Interoperability and Patient Access Final Rule: https://www.cms.gov/regulations-and-guidance/guidance/interoperability/index
- **Concrete entities:** Member, Subscriber, Coverage, Plan / Product, Eligibility Response, Claim Header, Claim Line, ERA (835), Provider, Practitioner Role, Prior Authorization, Network Affiliation, Capitation Roster.
- **Recommendation:** Build full model. The combination of X12 transactions + Da Vinci IGs gives a complete attribute set.

#### Revenue Cycle Management (`revenue_cycle`)

- **Tier 1.**
- **One-liner:** Patient access, coding, claims, denials, and collections to convert care delivered into cash.
- **Standards / sources:**
  - HIPAA X12 837P/I/D, 835, 277CA, 270/271 (above).
  - CMS National Correct Coding Initiative (NCCI) edits: https://www.cms.gov/medicare/coding-billing/national-correct-coding-initiative-ncci-edits
  - ICD-10-CM/PCS (CMS, free): https://www.cms.gov/medicare/coding/icd10
  - CPT (AMA, paid for full set): https://www.ama-assn.org/practice-management/cpt
  - HCPCS Level II (CMS, free): https://www.cms.gov/medicare/coding-billing/healthcare-common-procedure-system
  - CMS Outpatient/Inpatient Pricer logic.
- **Concrete entities:** Patient Encounter, Charge, Claim, Claim Line, ICD-10 / CPT / HCPCS Code, Modifier, Adjustment, Denial Reason (CARC/RARC), Bad Debt Write-Off, Self-Pay Plan, Patient Statement.
- **Recommendation:** Build full model.

#### Telehealth (`telehealth`)

- **Tier 1.**
- **One-liner:** Virtual care delivery: scheduling, video visits, e-prescribing, and remote monitoring.
- **Standards / sources:**
  - HL7 FHIR Encounter (with class=virtual), Appointment, Communication, MedicationRequest, DeviceMetric, Observation: https://hl7.org/fhir/
  - CMS Place of Service Code 02 (telehealth) and 10 (home telehealth) billing rules.
  - NCPDP SCRIPT for e-prescribing (paid; widely echoed).
  - DEA EPCS (Electronic Prescribing of Controlled Substances) requirements.
  - ATA Telehealth Practice Guidelines: https://www.americantelemed.org/resources/practice-guidelines/
- **Concrete entities:** Virtual Visit, Pre-Visit Form, Video Session, E-Prescription, Remote Monitoring Device, Vital Sign Stream, Patient-Reported Outcome, Consent for Telehealth, Care Plan Update.
- **Recommendation:** Build full model.

#### Value-Based Care (`value_based_care`)

- **Tier 1.**
- **One-liner:** Population health, risk adjustment, and quality measure attainment under risk-bearing contracts.
- **Standards / sources:**
  - CMS Star Ratings methodology: https://www.cms.gov/medicare/health-drug-plans/part-c-d-performance-data
  - NCQA HEDIS technical specifications — paid for full spec, but measure logic narratives are free: https://www.ncqa.org/hedis/
  - CMS MIPS Quality Payment Program measures: https://qpp.cms.gov/mips/quality-measures
  - HHS HCC v24/v28 risk adjustment models (free): https://www.cms.gov/medicare/payment/medicare-advantage-rates-statistics/risk-adjustment
  - HL7 FHIR Quality Measures (Da Vinci / CARIN): https://hl7.org/fhir/us/davinci-deqm/
  - ACO REACH / MSSP benchmark methodologies (CMS).
- **Concrete entities:** Attributed Member, Care Gap, Quality Measure, Numerator/Denominator/Exclusion, Risk Score (HCC), Shared Savings Settlement, Benchmark Cohort, Provider Quality Profile.
- **Recommendation:** Build full model. HEDIS spec costs money but the entities and measure-narrative are free.

---

### Life Sciences (5 subdomains)

#### Pharmacovigilance (`pharmacovigilance`) [ANCHOR]

- **Tier 1.**
- **Standards:** ICH E2B(R3), MedDRA, FAERS — already a fully-attributed anchor.

#### Clinical Trials (`clinical_trials`)

- **Tier 1.**
- **One-liner:** Protocol design, site activation, patient enrollment, and trial data capture for drug development.
- **Standards / sources:**
  - CDISC SDTM (Study Data Tabulation Model) v2.0 / v1.4: https://www.cdisc.org/standards/foundational/sdtm
  - CDISC ADaM v1.3 (Analysis Data Model): https://www.cdisc.org/standards/foundational/adam
  - CDISC ODM-XML v2.0 (Operational Data Model): https://www.cdisc.org/standards/data-exchange/odm
  - CDISC Define-XML v2.1: https://www.cdisc.org/standards/data-exchange/define-xml
  - CDISC CDASH (Clinical Data Acquisition Standards Harmonization): https://www.cdisc.org/standards/foundational/cdash
  - FDA Study Data Standards Catalog: https://www.fda.gov/industry/fda-data-standards-advisory-board/study-data-standards-resources
  - ClinicalTrials.gov XML/JSON public dataset: https://clinicaltrials.gov/data-api/api
  - EU CTIS (Clinical Trial Information System): https://euclinicaltrials.eu/
- **Concrete entities:** Study, Site, Subject, Visit, Protocol Version, Informed Consent, CRF Item, SDTM Domain (DM, AE, CM, EX, LB, VS, etc.), ADaM Dataset (ADSL, ADAE, ADTTE), Adverse Event, Concomitant Medication.
- **Recommendation:** **Strong next-anchor candidate.** CDISC is the single most rigorous, freely browsable data model in life sciences. Define-XML literally is the data dictionary.

#### Medical Devices (`medical_devices`)

- **Tier 1.**
- **One-liner:** Device design history, post-market surveillance, complaints, and field corrections under FDA/MDR.
- **Standards / sources:**
  - FDA UDI / GUDID (Global Unique Device Identification Database, public): https://accessgudid.nlm.nih.gov/
  - FDA MAUDE (Manufacturer and User Facility Device Experience), public adverse event DB: https://www.accessdata.fda.gov/scripts/cdrh/cfdocs/cfmaude/search.cfm
  - FDA MedWatch 3500A schema.
  - ISO 13485 and FDA 21 CFR 820 (QSR) — process standards, free reading.
  - EU MDR / Eudamed: https://ec.europa.eu/tools/eudamed/
  - IEC 62304 software lifecycle — paid (still useful).
- **Concrete entities:** Device, UDI-DI / UDI-PI, Lot, Complaint, MDR Report (MAUDE 3500A), CAPA, Field Action / Recall, Design History File, Risk File (ISO 14971 / FMEA), Post-Market Clinical Follow-Up.
- **Recommendation:** Build full model.

#### Pharma Supply Chain (`pharma_supply_chain`)

- **Tier 1.**
- **One-liner:** Cold-chain, serialization, and DSCSA-compliant supply chain for pharmaceuticals.
- **Standards / sources:**
  - GS1 EPCIS 2.0 (Electronic Product Code Information Services): https://ref.gs1.org/standards/epcis/
  - GS1 Healthcare GTIN, GLN, SSCC, GIAI: https://www.gs1.org/industries/healthcare
  - DSCSA (Drug Supply Chain Security Act) Title II FDA Guidance: https://www.fda.gov/drugs/drug-supply-chain-integrity/drug-supply-chain-security-act-dscsa
  - EU FMD (Falsified Medicines Directive) and EMVO data model: https://emvo-medicines.eu/
  - HL7 FHIR Medication, MedicationKnowledge resources.
- **Concrete entities:** Product Master (GTIN), Lot, Serial Number, Trade Item Hierarchy, Aggregation Event, Object Event, Transformation Event, Custody Transfer, EPCIS Document, T3 Track-and-Trace History.
- **Recommendation:** Build full model. EPCIS 2.0 is JSON-LD, fully spec'd, and the spec literally defines the event entities.

#### Real-World Evidence (`real_world_evidence`)

- **Tier 1.**
- **One-liner:** Curated EHR, claims, and registry data for outcomes research, label expansion, and HEOR studies.
- **Standards / sources:**
  - OMOP Common Data Model v5.4 (OHDSI): https://ohdsi.github.io/CommonDataModel/cdm54.html
  - OMOP Vocabulary (Athena): https://athena.ohdsi.org/
  - FDA Sentinel Common Data Model: https://www.sentinelinitiative.org/methods-data-tools/sentinel-common-data-model
  - PCORnet CDM v6: https://pcornet.org/data-driven-common-model/
  - HL7 FHIR US Core: https://hl7.org/fhir/us/core/
  - i2b2 Clinical Research Chart.
- **Concrete entities:** Person, Observation Period, Visit Occurrence, Condition Occurrence, Drug Exposure, Procedure Occurrence, Measurement, Death, Cohort, Cohort Definition, Vocabulary, Concept Hierarchy.
- **Recommendation:** **Strong next-anchor candidate.** OMOP CDM v5.4 has 39 tables fully documented; Athena gives the standard concepts. Best-in-class observational data model.

---

### Manufacturing (10 subdomains)

#### MES & Quality (`mes_quality`) [ANCHOR]

- **Tier 1.**
- **Standards:** ISA-95 / B2MML, OPC UA companion specs, Sparkplug B — already a fully-attributed anchor.

#### Environment, Health & Safety (`ehs`)

- **Tier 1.**
- **One-liner:** Incident reporting, hazard control, and regulatory EHS compliance across operating sites.
- **Standards / sources:**
  - OSHA Recordkeeping (Form 300, 300A, 301) Injury Tracking Application schema: https://www.osha.gov/recordkeeping
  - EPA Toxic Release Inventory (TRI) Form R XML: https://www.epa.gov/toxics-release-inventory-tri-program
  - GHS (Globally Harmonized System) Safety Data Sheet 16-section spec: https://unece.org/transport/dangerous-goods/ghs
  - ISO 14001 / 45001 process scope (free reading; auditing certificates public).
  - EPA NEI (National Emissions Inventory): https://www.epa.gov/air-emissions-inventories
- **Concrete entities:** Incident, Near-Miss, Injury / Illness Record (OSHA 300), Hazard Identification, Corrective Action, Permit, Air Emission Source, Waste Stream, Safety Data Sheet, Audit Finding.
- **Recommendation:** Build full model.

#### Production Scheduling (`production_scheduling`)

- **Tier 1.**
- **One-liner:** Finite-capacity sequencing of work orders across lines and resources to hit due dates and minimise changeovers.
- **Standards / sources:**
  - ISA-95 Part 4 (Production Scheduling) — free PDF on standards.iso.org for Part 1, B2MML schemas free: https://www.mesa.org/topics-resources/b2mml/
  - MESA Manufacturing Operations Management model: https://www.mesa.org/
  - Siemens Opcenter APS docs: https://docs.sw.siemens.com/
- **Concrete entities:** Production Schedule, Production Request, Job, Operation, Resource (Equipment / Personnel / Material), Capability, Work Master, Setup Time, Sequence-Dependent Changeover, Dispatch Rule.
- **Recommendation:** Build full model.

#### Shop-Floor IoT (`shop_floor_iot`)

- **Tier 1.**
- **One-liner:** Real-time machine, sensor, and edge data acquisition feeding OEE, energy, and predictive analytics.
- **Standards / sources:**
  - OPC UA companion specs (PackML, Robotics, Machine Tools, Devices): https://reference.opcfoundation.org/
  - MQTT v5 (OASIS): https://docs.oasis-open.org/mqtt/mqtt/v5.0/mqtt-v5.0.html
  - Sparkplug B v3.0: https://sparkplug.eclipse.org/
  - ISA-95 Part 2 object model.
  - NAMUR NE 107 device diagnostics.
- **Concrete entities:** Asset, Telemetry Tag, Time-Series Sample, OEE Bucket, Run / Down Event, Quality Reject, Alarm, Edge Gateway, Sparkplug Node, Sparkplug Device.
- **Recommendation:** Build full model.

#### Supply Chain Visibility (`supply_chain_visibility`)

- **Tier 1.**
- **One-liner:** End-to-end shipment, inventory, and ETA visibility across multi-tier supplier networks.
- **Standards / sources:**
  - GS1 EPCIS 2.0: https://ref.gs1.org/standards/epcis/
  - ANSI ASC X12 EDI 214 (transportation carrier shipment status), 856 (ASN), 945 (warehouse shipping advice): https://x12.org/
  - GS1 SSCC, GTIN, GLN identification keys.
  - FourKites / Project44 public APIs: https://www.project44.com/api
- **Concrete entities:** Shipment, Stop, Tracking Event, Container / Trailer, ETA Estimate, Exception (Late, Diverted), Carrier, Consignee, Hand-Off, Custody Event.
- **Recommendation:** Build full model.

#### Bill of Materials (`bill_of_materials`)

- **Tier 2.**
- **One-liner:** Engineering, manufacturing, and service BOM management with effectivity, ECN, and where-used.
- **Standards / sources:** ISO 10303 / STEP AP242 (XML schemas — paid; subset on standards.iso.org): https://www.iso.org/standard/66654.html ; ISA-95 Part 4 product/material model; Siemens Teamcenter data model docs (public): https://docs.sw.siemens.com/ ; PTC Windchill public docs; Autodesk Fusion Manage data model.
- **Concrete entities:** Item, Item Revision, BOM, BOM Line, Effectivity Range, Where-Used, Engineering Change Order, ECO Approval, Variant Configuration Rule, Substitution Group.
- **Recommendation:** Build from Teamcenter + Windchill + ISA-95 Part 4.

#### Asset & Maintenance Management (`maintenance`)

- **Tier 2.**
- **One-liner:** Predictive and preventive maintenance for plant assets — work orders, spares, and reliability engineering.
- **Standards / sources:** ISO 14224 (Reliability data collection for petroleum, petrochemical and natural gas industries) — paid; widely cited; IBM Maximo Application Suite data model docs (public): https://www.ibm.com/docs/en/maximo-as ; SAP Plant Maintenance (PM) public docs; MIMOSA OSA-EAI: https://www.mimosa.org/ ; ISO 55000 asset management process.
- **Concrete entities:** Asset, Functional Location, Work Order, Job Plan, PM Schedule, Failure Code (ISO 14224 taxonomy), Spare Part / BOM, Crew, Meter Reading, Reliability KPI (MTBF / MTTR).
- **Recommendation:** Build from Maximo + SAP PM + ISO 14224 (membership ideal, but the failure taxonomy is widely echoed).

#### Predictive Maintenance (`predictive_maintenance`)

- **Tier 2.**
- **One-liner:** ML-driven prediction of equipment failure using sensor telemetry and historical maintenance.
- **Standards / sources:** ISO 13374 (condition monitoring) — paid; ISO 17359 (general guidelines) — paid; NASA C-MAPSS / Turbofan public dataset: https://www.nasa.gov/intelligent-systems-division/discovery-and-systems-health/pcoe/pcoe-data-set-repository/ ; AWS Lookout for Equipment data schema: https://docs.aws.amazon.com/lookout-for-equipment/ ; PTC ThingWorx Analytics docs.
- **Concrete entities:** Asset, Sensor Channel, Telemetry Sample, Health Index, Anomaly, Remaining Useful Life Estimate, Failure Mode, Recommended Action, Maintenance Trigger, Model Version.
- **Recommendation:** Build from NASA C-MAPSS + AWS Lookout + ISO 13374 narrative.

#### Supplier Quality (`supplier_quality`)

- **Tier 2.**
- **One-liner:** Incoming inspection, NCRs, supplier scorecards, and corrective actions across the supplier base.
- **Standards / sources:** AIAG APQP / PPAP / IATF 16949 — paid via AIAG: https://www.aiag.org/ ; VDA Volumes — paid via VDA; EDI 832 (price/sales catalog) and EDI 856; ISO 9001 / ISO 19011 audit; Siemens Opcenter Quality docs (public): https://docs.sw.siemens.com/
- **Concrete entities:** Supplier, Part Approval (PPAP Level 1–5), Control Plan, Incoming Inspection Lot, Non-Conformance Report (NCR / 8D), Corrective Action, Supplier Scorecard, Cost of Poor Quality, Sub-Supplier Tier.
- **Recommendation:** Build from Opcenter Quality + Hexagon Q-DAS + 8D narrative + IATF abstracted process. Note: the **APQP/PPAP form templates** are paid; we'd model the entities, not the form fields verbatim.

#### Warranty & Aftermarket (`warranty`)

- **Tier 3.**
- **One-liner:** Claims processing, supplier recovery, and field-failure analytics for warranty operations.
- **Standards / sources:** AIAG TQRDC (paid). Most OEM warranty schemas are proprietary (Ford SMART recall is partial). Mize / PTC ThingWorx Service Apps public docs are limited.
- **Honest note:** **Would require imagination — not recommended for full attribution.** Warranty schemas vary radically by OEM (auto vs. consumer electronics vs. industrial). No public reference model exists at attribute fidelity. Recommend pulling real warranty data dictionaries from a customer before modelling.

---

### Retail (7 subdomains)

#### Merchandising (`merchandising`) [ANCHOR]

- **Tier 1.**
- **Standards:** GS1, NRF, EDI 850/810/856/852 — already a fully-attributed anchor.

#### Ecommerce (`ecommerce`)

- **Tier 1.**
- **One-liner:** Storefront, search, fulfillment, and conversion analytics across the digital channel.
- **Standards / sources:**
  - schema.org Product / Offer / Order / Review / Organization: https://schema.org/Product
  - GS1 GTIN, GS1 GPC: https://www.gs1.org/standards/gpc
  - Open Application Group (OAGi) BOD (Business Object Document): https://oagi.org/
  - Shopify Admin API: https://shopify.dev/docs/api/admin
  - Magento (Adobe Commerce) data model: https://developer.adobe.com/commerce/
  - WooCommerce REST API: https://woocommerce.github.io/woocommerce-rest-api-docs/
  - Google Merchant Center feed spec: https://support.google.com/merchants/answer/7052112
- **Concrete entities:** Product, Variant, Offer, Cart, Order, Order Line, Customer, Address, Shipment, Payment, Refund, Review, Promo, Inventory Position.
- **Recommendation:** Build full model.

#### Returns Management (`returns_management`)

- **Tier 1.**
- **One-liner:** Reverse logistics, restocking, refunds, and disposition for returned merchandise.
- **Standards / sources:**
  - ANSI ASC X12 EDI 180 (Return Merchandise Authorization), EDI 754 / 215 (Routing Instruction): https://x12.org/
  - schema.org Order / OrderItem with returnPolicy: https://schema.org/Order
  - Loop Returns API: https://docs.loopreturns.com/
  - Happy Returns API: https://www.happyreturns.com/
  - Shopify Order Returns API.
- **Concrete entities:** Return Authorization, Return Line, Return Reason, Inspection Result, Disposition (Restock / Refurb / Liquidate / Destroy), Refund, Replacement Order, Reverse Shipment, RMA Document.
- **Recommendation:** Build full model.

#### Customer Analytics (`customer_analytics`)

- **Tier 2.**
- **One-liner:** Unified customer profile, segmentation, lifetime value, and journey analytics across channels.
- **Standards / sources:** Adobe XDM (Experience Data Model): https://github.com/adobe/xdm ; Salesforce CDP / Data Cloud schema: https://developer.salesforce.com/docs/atlas.en-us.c360a_api.meta/c360a_api/c360a_api_intro.htm ; Segment Common Spec: https://segment.com/docs/connections/spec/common/ ; mParticle data model docs; schema.org Action / Event types.
- **Concrete entities:** Person Profile, Identity Map, Event (Page View / Add to Cart / Purchase), Audience / Segment, Journey, Touchpoint, Lifetime Value, Consent State, Identity Graph Edge.
- **Recommendation:** Build from Adobe XDM (which is open-source) + Segment Common Spec + Salesforce Data Cloud. Three sources cover the entity model.

#### Last Mile Delivery (`last_mile_delivery`)

- **Tier 2.**
- **One-liner:** Final-mile delivery orchestration to consumer doorstep including gig and 3PL fleets.
- **Standards / sources:** ANSI ASC X12 214 (carrier shipment status); GS1 EPCIS; FedEx Ship Manager API: https://developer.fedex.com/ ; UPS APIs: https://developer.ups.com/ ; USPS Web Tools API: https://www.usps.com/business/web-tools-apis/ ; Bringg / Onfleet / DispatchTrack public APIs.
- **Concrete entities:** Order, Delivery Job, Driver, Route, Stop, Geofence, Proof of Delivery (signature/photo), Delivery Window, Exception (Failed Attempt), Customer Notification.
- **Recommendation:** Build from FedEx + UPS + Onfleet APIs.

#### Dark Stores (`dark_stores`)

- **Tier 3.**
- **Honest note:** **Would require imagination — not recommended.** Dark-store ops (Instacart, Getir, Gopuff, Gorillas, Zepto) are operationally proprietary. The order/picker/route entities map loosely to ecommerce + last-mile-delivery, but micro-fulfilment-specific concepts (slot/bin/shopper-pace, automated MFC rate) are not publicly modelled at attribute fidelity. Recommend reusing the ecommerce anchor for the order side and flagging dark-store internals as unmodelled.

#### Store Operations (`store_ops`)

- **Tier 3.**
- **Honest note:** **Would require imagination — not recommended.** Workforce scheduling and shrink management are dominated by vendor-specific (Reflexis, Theatro, Kronos UKG, Legion) and chain-specific schemas. The NRF Store Operations Reference is a high-level capability model, not a data dictionary. Recommend deferring until customer data is available.

---

### CPG (4 subdomains)

#### Demand Planning (`demand_planning`) [ANCHOR]

- **Tier 1.**
- **Standards:** APICS standard SCM (paid), SAP IBP public docs — already a fully-attributed anchor.

#### Retail Execution (`retail_execution`)

- **Tier 2.**
- **One-liner:** In-store execution at the retailer: planograms, OSA, perfect store, and field rep activity.
- **Standards / sources:** GS1 Smart Centre planogram (GTIN-based item placement) docs: https://www.gs1.org/ ; Salesforce Consumer Goods Cloud data model: https://developer.salesforce.com/docs/atlas.en-us.cgcloud_dev_guide.meta/cgcloud_dev_guide/cgcloud_dev_guide.htm ; Repsly public API: https://www.repsly.com/api ; Spotio public API.
- **Concrete entities:** Account / Outlet, Visit, Visit Task, Photo / Image, Out-of-Stock Detection, Planogram Compliance Score, Promo Compliance, Field Rep Route, Survey Question.
- **Recommendation:** Build from Salesforce CG Cloud + Repsly + GS1 Smart Centre.

#### Brand Marketing (`brand_marketing`)

- **Tier 3.**
- **Honest note:** **Would require imagination — not recommended.** Nielsen Brand Health, Kantar, Ipsos, YouGov BrandIndex are paid syndicated panels with proprietary schemas. Marketing mix model (MMM) input/output schemas are agency-specific. No standard reference model exists. Recommend deferring.

#### Trade Promotion Management (`trade_promotion`)

- **Tier 3.**
- **Honest note:** **Would require imagination — not recommended.** SAP TPM, Vistex, Exceedra, Anaplan TPM are dominant but their accrual/deduction/lift attribution schemas differ widely. NRF/EDI 852 covers POS feedback but not promo design or accrual. Recommend deferring until customer data is available.

---

### TTH — Travel, Transportation & Hospitality (10 subdomains)

#### Hotel Revenue Management (`hotel_revenue_management`) [ANCHOR]

- **Tier 1.**
- **Standards:** HTNG, OpenTravel Alliance schemas, STR definitions — already a fully-attributed anchor.

#### Hotel Distribution (`hotel_distribution`)

- **Tier 1.**
- **One-liner:** Channel mix across direct, GDS, OTA, and wholesale to optimise reach versus commission cost.
- **Standards / sources:**
  - OpenTravel Alliance schemas (OTA_HotelAvailRQ/RS, OTA_HotelResRQ/RS, OTA_HotelRateAmountNotifRQ): https://opentravel.org/specifications/
  - HTNG Distribution working group schemas: https://www.htng.org/page/Workgroups
  - GDS connectivity: Sabre Hospitality / Amadeus Hotel Platform public dev portals: https://developer.sabre.com/ , https://developers.amadeus.com/
  - Booking.com Connectivity API: https://developers.booking.com/connectivity/
  - Expedia Partner Solutions: https://developers.expediagroup.com/
- **Concrete entities:** Property, Rate Plan, Room Type, Channel, Inventory Allotment, Restriction (LOS / CTA / CTD), Booking, Cancellation, Commission Schedule, Channel Performance Snapshot.
- **Recommendation:** Build full model.

#### Baggage Tracking (`baggage_tracking`)

- **Tier 1.**
- **One-liner:** End-to-end baggage handling and tracking for airlines and ground handlers.
- **Standards / sources:**
  - IATA RP 1745 Baggage Source Message (BSM) format: https://www.iata.org/en/services/passenger/baggage/
  - IATA Resolution 753 baggage tracking mandate (4-point handling): https://www.iata.org/en/programs/ops-infra/baggage/baggage-tracking/
  - SITA WorldTracer® data model (member-only but widely echoed): https://www.sita.aero/
  - IATA Baggage Reference Manual (paid): https://www.iata.org/en/publications/baggage-reference-manual/
  - IATA AHM (Airport Handling Manual): https://www.iata.org/en/publications/manuals/airport-handling-manual/
- **Concrete entities:** Baggage Tag, Bag Source Message (BSM), Bag Manifest Message (BMM), Handling Event (Acceptance / Sortation / Loading / Reconciliation / Delivery), Mishandled Bag File (PIR), Tracing Event, Bag Pool, Aircraft Container (ULD).
- **Recommendation:** Build full model. RP 1745 + Resolution 753 are public; AHM is paid via IATA but the message field structure is in vendor docs.

#### Fleet Telematics (`fleet_telematics`)

- **Tier 1.**
- **One-liner:** Vehicle GPS, ELD compliance, fuel, and driver behaviour analytics for commercial fleets.
- **Standards / sources:**
  - FMCSA Electronic Logging Device rule (49 CFR Part 395): https://www.fmcsa.dot.gov/hours-service/elds/electronic-logging-devices
  - SAE J1939 (paid; widely echoed in PGN docs).
  - SAE J1979 / OBD-II PIDs: https://en.wikipedia.org/wiki/OBD-II_PIDs
  - AEMP / ISO 15143-3 telematics interoperability: https://www.iso.org/standard/65156.html
  - Geotab MyGeotab API: https://geotab.github.io/sdk/
  - Samsara API: https://developers.samsara.com/
  - NHTSA FMVSS data dictionaries.
- **Concrete entities:** Vehicle, Asset Identifier (VIN), Driver, Trip, GPS Sample, Engine Fault Code (J1939 SPN/FMI), Fuel Event, Hours-of-Service Log (ELD RODS), Speeding/Harsh-Brake Event, Geofence Crossing.
- **Recommendation:** Build full model.

#### Last-Mile Logistics (`last_mile_logistics`)

- **Tier 1.**
- **One-liner:** Route, dispatch, and proof-of-delivery for parcel and same-day delivery operations.
- **Standards / sources:** Same as Last Mile Delivery above, but framed for parcel (FedEx/UPS/USPS) plus DHL XML Services: https://developer.dhl.com/ ; ANSI ASC X12 214/215; Open Shipping Specification (OSS).
- **Concrete entities:** Pickup, Sort Manifest, Linehaul Lane, Hub Hand-Off, Delivery Stop, Service Failure, Driver Manifest, Delivery Confirmation, Address Validation Response.
- **Recommendation:** Build full model.

#### Airline Disruption Management (`airline_disruption`)

- **Tier 2.**
- **One-liner:** Detect, reaccommodate, and recover passengers and crew from cancellations, delays, and IROPs.
- **Standards / sources:** IATA AIDX 17.1/22.1 (Aviation Information Data Exchange) XML: https://www.iata.org/en/publications/info-data-exchange/ ; IATA SSIM (Standard Schedules Information Manual) — paid; IATA NDC for re-ticketing: https://developer.iata.org/ ; SESAR A-CDM (free implementation guidance): https://www.eurocontrol.int/concept/airport-collaborative-decision-making ; ARINC airport feeds.
- **Concrete entities:** Flight Leg, Schedule Change, Movement Event (off-block, take-off, touch-down, on-block), Disruption Reason (IATA delay code), Reaccommodation Offer, Crew Pairing, Crew Disruption, Passenger PNR Impact, Notification.
- **Recommendation:** Build from AIDX + NDC + SESAR A-CDM. AIDX alone defines 180+ data elements.

#### Vacation Rentals (`vacation_rentals`)

- **Tier 2.**
- **One-liner:** Short-term rental marketplace operations for hosts, guests, and property managers.
- **Standards / sources:** Airbnb Channel API: https://www.airbnb.com/help/article/1257 (limited public); Vrbo / HomeAway Connect: https://www.partner.vrbo.com/ ; Booking.com vacation-rentals connectivity (above); HTNG VR working group; iCal / RFC 5545 for availability sync; NextPax / Rentals United / Hostfully channel-manager APIs (public docs).
- **Concrete entities:** Listing, Property, Calendar Slot, Booking, Guest, Host, Cleaning Job, Channel Sync Status, Rate Plan, Damage Deposit.
- **Recommendation:** Build from Vrbo Connect + Booking.com VR + iCal + NextPax.

#### Ride-Share Dispatch (`ride_share_dispatch`)

- **Tier 2.**
- **One-liner:** Match riders and drivers in real time with surge pricing, ETA prediction, and supply rebalancing.
- **Standards / sources:** NYC TLC Trip Record Data (Yellow / Green / FHV / High-Volume FHV) — extensive public schema: https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page ; Chicago Transportation Network Providers public dataset; California PUC TNC reporting format; MaaS Alliance / MOD Sandbox API specs; Uber Movement (historical); Lyft Bikes & Scooters GBFS spec: https://gbfs.org/
- **Concrete entities (excluding proprietary matching logic):** Trip Request, Trip, Driver, Rider, Surge Multiplier Region, Pickup, Dropoff, Pickup-Location-ID (TLC), Fare Structure, Tip, Cancellation Event.
- **Recommendation:** Build entity model from NYC TLC + Chicago TNP + GBFS. Note: dispatch matching/ETA models are proprietary — leave abstract.

#### Airline Loyalty (`airline_loyalty`)

- **Tier 3.**
- **Honest note:** **Would require imagination — not recommended.** Frequent flyer program rules (mileage accrual ratios, tier qualification, partner co-brand earn) are radically per-program. IATA / Star Alliance / Oneworld interlining files are member-only. Plusgrade for upgrades is proprietary. The Loyalty member entity exists across programs but the rule data is per-airline. Recommend deferring.

#### Airline Revenue Management (`airline_revenue_management`)

- **Tier 3.**
- **Honest note:** **Would require imagination — not recommended.** O&D bid-price tables, fare class controls, overbooking models are deeply proprietary (PROS O&D, Sabre AirVision RM, Amadeus Altea RM). ATPCO fare data is paid and licensed for direct use only. Public structure exists for fare classes (booking class letters), but the *attributes* of an RM run are vendor-specific. Recommend deferring.

---

### Telecom (7 subdomains)

#### BSS / OSS (`bss_oss`)

- **Tier 1.**
- **One-liner:** Order, billing, and service activation across telecom business and operational support systems.
- **Standards / sources:**
  - TM Forum Information Framework (SID) v22 / v23: https://www.tmforum.org/oda/information-systems/information-framework-sid/
  - TM Forum Open APIs (TMF620 Product Catalog, TMF622 Product Ordering, TMF629 Customer, TMF635 Usage, TMF637 Product Inventory): https://www.tmforum.org/oda/open-apis/directory/
  - eTOM Business Process Framework: https://www.tmforum.org/business-process-framework/
  - 3GPP TS 32 series (charging) and TS 28 series (management): https://www.3gpp.org/specifications-technologies
  - MEF (Metro Ethernet Forum) LSO APIs: https://www.mef.net/lso-apis/
- **Concrete entities:** Customer, Account, Product Offering, Product Specification, Service, Resource, Order, Order Item, Inventory, Trouble Ticket (TMF621), Usage Record, Billing Account.
- **Recommendation:** Build full model.

#### Customer Care (`customer_care`)

- **Tier 1.**
- **One-liner:** Multi-channel contact centre operations — voice, chat, self-serve — for service support and retention.
- **Standards / sources:**
  - TM Forum TMF621 Trouble Ticket API: https://www.tmforum.org/oda/open-apis/directory/trouble-ticket-api-TMF621/
  - TM Forum SID Customer domain.
  - ITIL v4 Incident Management process (free overview).
  - Genesys Cloud Public API: https://developer.genesys.cloud/
  - Twilio Flex / Salesforce Service Cloud / Zendesk public data models.
  - WAI Aria + WCAG for accessible self-service flows.
- **Concrete entities:** Interaction, Contact, Channel, Queue, Routing Decision, Agent, Skill, Trouble Ticket, Resolution, NPS / CSAT Response, Knowledge Article Reference.
- **Recommendation:** Build full model.

#### Network Operations (`network_operations`)

- **Tier 1.**
- **One-liner:** Monitor, assure, and remediate carrier network elements end-to-end across RAN, transport, and core.
- **Standards / sources:**
  - 3GPP TS 28.500 series (5G / OAM): https://www.3gpp.org/DynaReport/28-series.htm
  - ETSI NFV-MANO and ZSM specs: https://www.etsi.org/technologies/nfv ; https://www.etsi.org/technologies/zero-touch-network-service-management
  - ONF YANG models: https://www.opennetworking.org/
  - TM Forum Open APIs (TMF638 Service Inventory, TMF641 Service Ordering, TMF642 Alarm Management).
  - IETF YANG models for SNMP/NETCONF: https://datatracker.ietf.org/wg/netmod/about/
- **Concrete entities:** Network Element, Cell / gNB, Link, Alarm, Performance KPI Sample, Topology Edge, Trouble Ticket, Change Request, Maintenance Window, Configuration Change.
- **Recommendation:** Build full model.

#### 5G Network Slicing (`network_slicing_5g`)

- **Tier 1.**
- **One-liner:** Lifecycle management of 5G network slices for enterprise SLAs and consumer use cases.
- **Standards / sources:**
  - 3GPP TS 28.530 series (network slice management): https://www.3gpp.org/DynaReport/28530.htm
  - 3GPP TS 28.541 (5G NRM): https://www.3gpp.org/DynaReport/28541.htm
  - 3GPP TS 28.554 (5G performance KPIs).
  - ETSI ZSM 008 cross-domain orchestration.
  - GSMA Generic Network Slice Template (GST) NG.116: https://www.gsma.com/newsroom/wp-content/uploads/NG.116-v3.0.pdf
  - TM Forum IG1218 / TMF641.
- **Concrete entities:** Network Slice Subnet, Slice Profile (eMBB / URLLC / mIoT), GST Attribute, S-NSSAI, Service Level Specification, Slice Lifecycle Event, KPI Snapshot, Tenant.
- **Recommendation:** **Strong next-anchor candidate.** GST alone defines ~40 named slice attributes; TS 28.541 NRM is the data dictionary.

#### Subscriber Billing (`subscriber_billing`)

- **Tier 1.**
- **One-liner:** Rate, charge, invoice, and dunning for prepaid and postpaid telecom and broadband subscribers.
- **Standards / sources:**
  - 3GPP TS 32.250 series (charging) and Rf/Ro interfaces: https://www.3gpp.org/DynaReport/32-series.htm
  - 3GPP TS 32.298 CDR (Call Detail Record) parameter encoding (ASN.1): https://www.3gpp.org/DynaReport/32298.htm
  - TM Forum TMF635 Usage Management API.
  - TM Forum SID Bill domain.
- **Concrete entities:** Subscriber, Service, Tariff, Charge, Usage Event, Rated CDR, Bundle / Allowance, Bill Run, Invoice, Dunning Step.
- **Recommendation:** Build full model.

#### Video Streaming QoE (`video_streaming_qoe`)

- **Tier 1.**
- **One-liner:** Quality of experience for OTT video: rebuffering, startup time, and bitrate adaptation.
- **Standards / sources:**
  - CTA-2066 / CMCD (Common Media Client Data): https://shop.cta.tech/products/web-application-video-ecosystem-common-media-client-data-cta-2066
  - CTA-5004 / CMSD (Common Media Server Data): https://www.cta.tech/Resources/Standards
  - DASH-IF guidelines: https://dashif.org/guidelines/
  - HLS RFC 8216bis: https://datatracker.ietf.org/wg/hls/about/
  - Streaming Video Alliance QoE definitions: https://www.svta.org/
  - Conviva Video AI metrics docs (limited public).
- **Concrete entities:** Session, Asset / Manifest, Bitrate Switch Event, Buffer Underrun, Startup Time Sample, Rebuffer Event, CDN Edge, ABR Decision, Error Code (HTTP / DRM), Device / Player.
- **Recommendation:** Build full model.

#### Churn Management (`churn_management`)

- **Tier 3.**
- **Honest note:** **Would require imagination — not recommended.** While the customer/contract/billing entities are covered by TM Forum SID, the **churn model itself** (features, propensity, save offers, save-rate by channel) is operator-specific. Recommend modelling the customer/contract entities by deferring to BSS/OSS, and flagging churn-prediction internals as proprietary.

---

### Utilities (6 subdomains)

#### Smart Metering (`smart_metering`)

- **Tier 1.**
- **One-liner:** AMI head-end + meter data management for billing, outage, and grid analytics.
- **Standards / sources:**
  - ANSI C12.19 Utility Industry End Device Data Tables: https://www.nema.org/standards/view/American-National-Standard-for-Utility-Industry-End-Device-Data-Tables
  - ANSI C12.22 Application Layer Messaging.
  - DLMS/COSEM IEC 62056 (free downloadable Blue/Green/Yellow Books): https://www.dlms.com/
  - IEC 61968-9 (CIM messages for meter reading and control): https://webstore.iec.ch/publication/56477
  - Smart Energy Profile 2.0 (SEP 2.0 / IEEE 2030.5): https://standards.ieee.org/ieee/2030.5/5897/
  - MultiSpeak v5.2 (free, rural co-op focused): https://www.multispeak.org/
- **Concrete entities:** Meter, Endpoint, Interval Reading, Register Reading, Meter Event (tamper / outage), Service Point, Demand Reading, Time-of-Use Bucket, Disconnect/Reconnect Command, Firmware Version.
- **Recommendation:** **Strong next-anchor candidate.** ANSI C12 + DLMS-COSEM + CIM 61968-9 fully attribute the model. SEP 2.0 covers the customer-facing side.

#### Outage Management (`outage_management`)

- **Tier 1.**
- **One-liner:** Detect, locate, and restore power outages with crew dispatch and customer communications.
- **Standards / sources:**
  - MultiSpeak v5.2 OMS schemas (free): https://www.multispeak.org/
  - IEC 61968-3 (CIM for distribution operations).
  - DOE Form OE-417 emergency incident reporting (public XML): https://www.oe.netl.doe.gov/oe417.aspx
  - IEEE 1366 Distribution Reliability Indices (SAIDI/SAIFI/CAIDI) — paid for full text but definitions public.
  - State PUC outage reporting formats (e.g. CA PUC, TX PUC).
- **Concrete entities:** Outage, Outage Cause, Affected Customers / Meters, Predicted Restoration Time, Crew, Crew Dispatch, Switching Step, Customer Notification, OE-417 Incident.
- **Recommendation:** Build full model.

#### Water Utilities (`water_utilities`)

- **Tier 2.**
- **One-liner:** Water distribution: treatment, metering, non-revenue water, and quality compliance.
- **Standards / sources:** EPA Safe Drinking Water Information System (SDWIS) public XML: https://www.epa.gov/ground-water-and-drinking-water/safe-drinking-water-information-system-sdwis-federal-reporting ; AWWA standards (paid); WaterML 2.0 (OGC / WMO): https://www.ogc.org/standard/waterml/ ; AMR/AMI water meters via DLMS.
- **Concrete entities:** Service Connection, Meter, Reading, Sample / Analyte, Compliance Determination, Treatment Plant, Distribution Node, Leak Event, Flushing Event, NRW Audit.
- **Recommendation:** Build from EPA SDWIS + WaterML 2.0 + AWWA narrative.

#### Gas Distribution (`gas_distribution`)

- **Tier 2.**
- **One-liner:** Natural gas distribution, leak detection, odorization, and customer service.
- **Standards / sources:** PHMSA Form 7100.1-1 / 7100.2-1 distribution annual reports (public): https://www.phmsa.dot.gov/data-and-statistics/pipeline/distribution-transmission-gathering-lng-and-liquid-annual-data ; NAESB Wholesale Gas Quadrant (WGQ) standards: https://www.naesb.org/ ; American Gas Association standards (paid).
- **Concrete entities:** Pipeline Segment, Asset, Leak Survey Record, Leak Repair, Gas Quality Reading, Odorant Injection, Cathodic Protection Reading, Customer Premise, PHMSA Annual Report.
- **Recommendation:** Build from PHMSA + NAESB + AGA narrative.

#### Asset Health Monitoring (`asset_health_monitoring`)

- **Tier 4.**
- **One-liner:** Predictive analytics on transformers, breakers, and lines to drive condition-based maintenance and capex.
- **Standards / sources:**
  - IEC 61850 substation messaging — paid: https://webstore.iec.ch/publication/6028
  - IEC 61968 / 61970 CIM — paid: https://webstore.iec.ch/publication/6195
  - IEEE C57 transformer family — paid.
  - DNV / CIGRE working group reports — paid.
  - Bentley AssetWise APM and IBM Maximo APM data models (public, but partial).
- **Concrete entities (with paid IEC docs):** Substation, Bay, Logical Node (LN), CIM Asset, Asset Health Index, Dissolved Gas Analysis Result, Partial Discharge Sample, IEEE C57 Test Record, Risk Score.
- **Recommendation:** **Hold pending IEC membership.** Without 61850/61968, attribute fidelity is speculation.

#### Grid Operations (`grid_ops`)

- **Tier 4.**
- **One-liner:** Real-time monitoring and control of transmission and distribution networks for reliability and DER integration.
- **Standards / sources:**
  - IEC 61850 (above) — paid.
  - CIM IEC 61968/61970 — paid.
  - DNP3 (paid).
  - IEEE C37.118 synchrophasor — paid.
  - NERC TADS / GADS / DADS reporting templates (members only): https://www.nerc.com/pa/RAPA/Pages/PerformanceAnalysis.aspx
  - DOE OE-417 (free).
  - MultiSpeak (free, distribution side).
- **Concrete entities (with paid IEC docs):** Substation, Feeder, Switch, PMU Sample, SCADA Point, Topology Node, Outage, NERC Event Type, Curtailment, DER Aggregation.
- **Recommendation:** **Hold pending IEC + NERC membership.** A partial model from MultiSpeak + DOE OE-417 is possible but won't reach anchor fidelity.

---

### Energy (5 subdomains)

#### Carbon Accounting (`carbon_accounting`)

- **Tier 1.**
- **One-liner:** Scope 1/2/3 GHG accounting, sustainability reporting, and offset tracking.
- **Standards / sources:**
  - GHG Protocol Corporate Standard / Scope 3 Standard (free): https://ghgprotocol.org/standards
  - EPA GHG Mandatory Reporting Program (Subpart C / W) data files: https://www.epa.gov/ghgreporting
  - CDP Climate Change disclosure schemas: https://www.cdp.net/en/guidance
  - ISSB IFRS S2 Climate-related Disclosures: https://www.ifrs.org/issued-standards/ifrs-sustainability-standards-navigator/ifrs-s2-climate-related-disclosures/
  - SBTi (Science Based Targets) target validation forms.
  - EPA eGRID emission factors: https://www.epa.gov/egrid
- **Concrete entities:** Activity Data Record, Emission Factor, Scope 1/2/3 Category, Facility, Inventory Period, Verification Statement, Offset Project, Retired Credit (Verra / Gold Standard), Target / Pathway, IFRS S2 Disclosure Item.
- **Recommendation:** Build full model.

#### Energy Trading & Risk (`energy_trading`)

- **Tier 1.**
- **One-liner:** Wholesale power, gas, and emissions trading with position management and risk limits.
- **Standards / sources:**
  - CFTC Part 43 / 45 swap data reporting (above): https://www.cftc.gov/IndustryOversight/DataReporting
  - FERC EQR (Electric Quarterly Report) data: https://www.ferc.gov/power-sales-and-markets/electric-quarterly-reports-eqr
  - EU REMIT reporting (ACER): https://www.acer.europa.eu/remit
  - FpML commodity / energy product types: https://www.fpml.org/spec/
  - NAESB Wholesale Electric Quadrant standards.
  - ICE / CME / EEX product specifications (free contract specs).
- **Concrete entities:** Trade, Trade Leg, Delivery Period (Hourly / Block), Position, Mark-to-Market, Settlement Price (ICE / CME / EEX), Hedge Designation, Risk Limit, REMIT Trade Report, FERC EQR Record.
- **Recommendation:** Build full model.

#### EV Charging Operations (`ev_charging`)

- **Tier 1.**
- **One-liner:** Public and fleet EV charge point operations — sessions, pricing, demand response, and uptime.
- **Standards / sources:**
  - OCPP 2.0.1 (Open Charge Point Protocol — IEC 63584 since 2024): https://openchargealliance.org/protocols/open-charge-point-protocol/
  - OCPI 2.2.1 (Open Charge Point Interface): https://evroaming.org/ocpi-protocol/
  - ISO 15118 Vehicle-to-Grid Communication: https://www.iso.org/standard/77845.html
  - IEC 61851 Conductive charging system.
  - OpenADR 2.0b for demand response: https://www.openadr.org/
  - eMI3 group (eMobility roaming).
- **Concrete entities:** Charge Point, Connector, EVSE, Charging Session, Authorization (RFID / Plug & Charge), Tariff, CDR (Charge Detail Record), Reservation, Smart Charging Profile, OCPI Token.
- **Recommendation:** **Strong next-anchor candidate.** OCPP 2.0.1 is now an IEC standard; OCPI is the roaming layer. Fully attribute-able.

#### Renewable Generation (`renewable_generation`)

- **Tier 4.**
- **One-liner:** Wind, solar, and hybrid generation: forecasting, dispatch, and curtailment.
- **Standards / sources:**
  - IEC 61400-25 (wind plant SCADA) — paid: https://webstore.iec.ch/publication/5434
  - IEC 61724-1 (solar PV performance monitoring) — paid.
  - FERC Form 556 (small power production qualifying facility, public).
  - EIA-923 (US power plant generation, public XLS): https://www.eia.gov/electricity/data/eia923/
  - SunSpec Modbus map (free): https://sunspec.org/
- **Concrete entities (with paid IEC):** Plant, Turbine / Module, SCADA Tag, Power Output Sample, Forecast (POE10/50/90), Curtailment Event, Availability, EIA-923 Record, REC Issuance.
- **Recommendation:** **Hold pending IEC membership.** SunSpec Modbus + EIA-923 give a partial model; full attribute fidelity needs 61400-25 / 61724.

#### Refinery Operations (`refinery_operations`)

- **Tier 3.**
- **Honest note:** **Would require imagination — not recommended.** Crude scheduling, blending, and unit yields use AspenTech (PIMS / Aspen HYSYS), Honeywell UniSim, KBC Petro-SIM, KBR Yield Forecaster — all proprietary schemas. ISA-95 covers some shop-floor but not refinery-specific stream cuts. Recommend deferring.

---

### High-Tech (7 subdomains)

#### Cloud FinOps (`cloud_finops`)

- **Tier 1.**
- **One-liner:** Cloud cost visibility, allocation, optimisation, and unit economics across AWS, Azure, and GCP.
- **Standards / sources:**
  - FOCUS 1.2 / 1.3 (FinOps Open Cost & Usage Specification, ratified by FinOps Foundation): https://focus.finops.org/focus-specification/
  - AWS Cost and Usage Report (CUR) data dictionary: https://docs.aws.amazon.com/cur/latest/userguide/data-dictionary.html
  - Azure Cost Management Exports schema: https://learn.microsoft.com/en-us/azure/cost-management-billing/automate/automation-overview
  - GCP Billing BigQuery export schema: https://cloud.google.com/billing/docs/how-to/export-data-bigquery-tables
  - Kubecost / OpenCost (CNCF): https://opencost.io/
- **Concrete entities:** Billing Account, Resource, Charge Line, Service / SKU, Tag / Label, Reservation / Savings Plan, Commitment, Allocation Rule, Cost Center, Unit Economic KPI.
- **Recommendation:** **Strong next-anchor candidate.** FOCUS 1.2 is recent (May 2025) and 1.3 ratified December 2025; the spec literally enumerates ~50 columns with strict types. AWS/Azure/GCP all publish native FOCUS exports.

#### Device Telemetry (`device_telemetry`)

- **Tier 1.**
- **One-liner:** Connected device event, crash, and feature-usage pipelines feeding product, support, and reliability.
- **Standards / sources:**
  - OpenTelemetry semantic conventions (CNCF): https://opentelemetry.io/docs/specs/semconv/
  - W3C Trace Context: https://www.w3.org/TR/trace-context/
  - OMA-DM and LWM2M for IoT device management: https://www.openmobilealliance.org/
  - Mixpanel data model: https://docs.mixpanel.com/docs/data-structure/events-and-properties
  - Amplitude data taxonomy: https://www.docs.developers.amplitude.com/data/data-taxonomy/
  - schema.org / IAB ad event types.
- **Concrete entities:** Device, Session, Event, Trace / Span, Resource (host / k8s / function), Crash Report, Feature Flag Exposure, Cohort, Identity, Pipeline Lag.
- **Recommendation:** Build full model.

#### Chip Design — EDA (`chip_design_eda`)

- **Tier 3.**
- **Honest note:** **Would require imagination — not recommended.** SystemVerilog/UVM (Accellera, free), IEEE 1801 UPF, SDF, SDC, LEF/DEF describe the *interchange formats* but the design-flow data structures (synthesis reports, P&R timing, simulation regression results) are radically vendor-specific (Synopsys, Cadence, Siemens EDA). Most EDA companies treat their schemas as competitive moat. Recommend deferring.

#### Developer Relations (`developer_relations`)

- **Tier 3.**
- **Honest note:** **Would require imagination — not recommended.** No public reference model exists for DevRel metrics (SDK downloads, GitHub stars, time-to-first-API-call, sample-app forks). Each company stitches together GitHub API, npm/PyPI registries, Discord/Slack, marketing automation. Recommend deferring.

#### License Management (`license_management`)

- **Tier 3.**
- **Honest note:** **Would require imagination — not recommended.** ISO/IEC 19770-1/2/3 (Software Asset Management) is a paid process standard, not a data dictionary. Flexera FlexNet, Reprise, Microsoft MLS schemas are proprietary. SBOM standards (SPDX, CycloneDX) cover bill-of-materials but not entitlements / activation / metering. Recommend deferring.

#### Marketplace Operations (`marketplace_operations`)

- **Tier 3.**
- **Honest note:** **Would require imagination — not recommended.** Two-sided marketplace internals (seller-quality, listing-health, dispute outcomes, payout schedules) are proprietary across Amazon, eBay, Etsy, Shopify, Mercado Libre. Amazon SP-API gives an opinionated *seller-side* surface but not the marketplace-operator perspective. Recommend deferring or scoping narrowly to "seller-side from SP-API".

#### Semiconductor Yield (`semiconductor_yield`)

- **Tier 4.**
- **One-liner:** Wafer test, defect classification, parametric drift, and yield engineering across fabs and OSATs.
- **Standards / sources:**
  - SEMI E10 RAM (Reliability, Availability, Maintainability): https://www.semi.org/en/standards
  - SEMI E30 GEM, E37 HSMS (factory communication).
  - SEMI E120 CEM (Common Equipment Model), E125 EDA, E132, E134.
  - SEMI E142 (substrate mapping).
  - SEMI standards individually paid, but SEMICon membership often includes them.
  - KLA / Camtek / Onto Innovation file formats (vendor-specific).
- **Concrete entities (with SEMI access):** Lot, Wafer, Die, Reticle, Test Record (E142), Defect Classification (E10), Parametric Result, OEE / E10 State, Recipe, MES Job.
- **Recommendation:** **Hold pending SEMI membership.** A partial model is possible from open WAT/MAP files, but anchor fidelity needs E10/E30/E142.

---

### Media (5 subdomains)

#### Ad Tech (`ad_tech`)

- **Tier 1.**
- **One-liner:** Programmatic ad buying/selling, audience targeting, and campaign measurement across publishers and brands.
- **Standards / sources:**
  - IAB OpenRTB 2.6 / 3.0: https://iabtechlab.com/standards/openrtb/
  - IAB VAST 4.x (Video Ad Serving Template): https://iabtechlab.com/standards/vast/
  - IAB OMID (Open Measurement SDK): https://iabtechlab.com/standards/open-measurement-sdk/
  - IAB ads.txt / sellers.json / buyers.json: https://iabtechlab.com/ads-txt/
  - MRC viewability standards: https://mediaratingcouncil.org/standards
  - Prebid.org JSON schemas: https://docs.prebid.org/
  - SCTE-224 (linear ad signaling): https://www.scte.org/standards/library/
- **Concrete entities:** Ad Request, Bid Request (OpenRTB), Bid Response, Impression, Click, Conversion, Creative, Deal ID, Audience Segment, Site / App / Inventory, Auction Outcome.
- **Recommendation:** **Strong next-anchor candidate.** OpenRTB alone defines hundreds of fields; combined with VAST and OMID, the entire programmatic stack is open.

#### Programmatic Advertising (`programmatic_advertising`)

- **Tier 1.**
- **One-liner:** Real-time bidded ad transactions across SSPs, DSPs, and ad exchanges.
- **Standards / sources:** Same set as Ad Tech above (this subdomain heavily overlaps and could be merged with `ad_tech`).
- **Concrete entities:** Auction, Bid, Floor Price, SSP, DSP, Ad Exchange, Win Notice, Auction Loss Reason, Header-Bidder, ssp.json/sellers.json identity.
- **Recommendation:** Build full model. Note overlap with `ad_tech`.

#### Ad Inventory & Yield (`ad_inventory`)

- **Tier 1.**
- **One-liner:** Forecast, package, and price linear and digital ad inventory to maximise sell-through and CPM.
- **Standards / sources:** IAB OpenRTB; SCTE-224 / SCTE-35 (linear ad signaling): https://www.scte.org/ ; FreeWheel / Operative public docs (limited); Google Ad Manager API: https://developers.google.com/ad-manager/api ; Magnite / PubMatic public docs.
- **Concrete entities:** Inventory Pool, Forecast Run, Package / Bundle, Sales Order, Line Item (Sponsorship / Standard / House), Daypart, Yield Curve, CPM Floor, Make-Good Credit.
- **Recommendation:** Build full model.

#### Content Metadata (`content_metadata`)

- **Tier 1.**
- **One-liner:** Asset descriptors, taxonomies, rights windows, and identifiers across the content supply chain.
- **Standards / sources:**
  - EIDR (Entertainment Identifier Registry): https://eidr.org/documents/
  - MovieLabs MDDF (Metadata Data Description Framework — CMD, Manifest, Avails, Rights): https://www.movielabs.com/md/
  - SMPTE timeline / metadata standards: https://www.smpte.org/
  - GS1 / EAN for physical media.
  - Schema.org TVSeries / Movie / VideoObject.
  - DDEX for music: https://kb.ddex.net/
- **Concrete entities:** Title, Edit (EIDR L2), Manifestation, Avails Window, Rights Holder, Talent Credit, Genre Tag, Subtitles / Audio Track, Content Identifier (EIDR / ISAN / GTIN), Royalty Statement.
- **Recommendation:** Build full model.

#### SaaS Revenue Metrics (`saas_metrics`)

- **Tier 2.**
- **One-liner:** ARR, retention, and product-led growth metrics for B2B SaaS go-to-market and finance.
- **Standards / sources:** No formal standard, but: Stripe Billing data model: https://docs.stripe.com/billing ; Maxio (Chargify / SaaSOptics) glossary: https://maxio.com/resources/saas-metrics-glossary ; Chargebee data model: https://www.chargebee.com/docs/2.0/api_v2/ ; KeyBanc Capital Markets SaaS Survey definitions; Bessemer State of the Cloud benchmark definitions.
- **Concrete entities:** Subscription, Plan, Customer, MRR Movement (New / Expansion / Contraction / Churn), Net Revenue Retention Cohort, ARR Snapshot, Product Usage Event, Trial / PLG Conversion, Customer Health Score.
- **Recommendation:** Build from Stripe Billing + Chargebee + Maxio glossary. Not a formal standard but three vendors converge on the same entity model.

---

### Professional Services (7 subdomains)

#### Time & Billing (`time_and_billing`)

- **Tier 1.**
- **One-liner:** Capture billable hours, apply rates and discounts, generate invoices, and shorten lockup.
- **Standards / sources:**
  - LEDES (Legal Electronic Data Exchange Standard) — free: https://ledes.org/
  - LEDES UTBMS (Uniform Task-Based Management System): https://ledes.org/utbms-codes/
  - LEDES 1998B / 2000 / XML 2.x invoice formats.
  - American Bar Association billing guidance.
- **Concrete entities:** Timekeeper, Matter / Engagement, Time Entry (UTBMS task code, activity code), Expense Entry, Rate Card, Discount, Invoice, Invoice Line, WIP Snapshot, Lockup Day.
- **Recommendation:** Build full model.

#### Contract Lifecycle Management (`contract_management`)

- **Tier 2.**
- **One-liner:** Authoring, negotiation, e-sign, repository, and obligation management for client and vendor contracts.
- **Standards / sources:** OASIS LegalRuleML: https://www.oasis-open.org/committees/legalruleml/ ; OASIS UBL (Universal Business Language) Contract documents: https://docs.oasis-open.org/ubl/ ; Adobe Acrobat Sign API: https://developer.adobe.com/document-services/docs/overview/adobe-sign-api/ ; DocuSign eSignature API: https://developers.docusign.com/ ; Ironclad / Icertis public docs (limited).
- **Concrete entities:** Contract, Contract Type, Clause Library Entry, Negotiation Round, Redline, Signatory, Obligation, Renewal Trigger, Approval Workflow Step, Audit Event.
- **Recommendation:** Build from DocuSign + UBL + Ironclad / Icertis narrative.

#### Expense Management (`expense_management`)

- **Tier 2.**
- **One-liner:** T&E capture, policy compliance, approvals, and reimbursement across the consultant base.
- **Standards / sources:** SAP Concur API: https://developer.concur.com/api-explorer/v3-0.html ; Expensify API: https://integrations.expensify.com/ ; Brex / Ramp public docs; CFDI 4.0 (Mexican electronic invoices): http://www.sat.gob.mx/ ; HMRC/IRS receipt/mileage rates.
- **Concrete entities:** Expense Report, Expense Item, Receipt Image, Mileage Entry, Card Transaction Match, Policy Violation, Approver, Reimbursement Disbursement, Per Diem.
- **Recommendation:** Build from Concur + Expensify + Brex / Ramp. Three vendor data models converge.

#### Legal Case Management (`legal_case_management`)

- **Tier 2.**
- **One-liner:** Matter management for law firms and legal departments: intake, conflicts, and time capture.
- **Standards / sources:** LEDES (above); NIEM Justice Domain (subset relevant to private practice): https://release.niem.gov/niem-domains/justice/ ; Clio Public API: https://developers.clio.com/ ; LexisNexis Time Matters / PCLaw (limited public); MyCase API.
- **Concrete entities:** Matter, Client / Opposing Party, Conflict Search, Intake Questionnaire, Document, Calendar/Court Event, Task, Time Entry (LEDES UTBMS), Trust Ledger, Statute of Limitations Tickler.
- **Recommendation:** Build from Clio + LEDES + NIEM Justice.

#### Audit Workflow (`audit_workflow`)

- **Tier 3.**
- **Honest note:** **Would require imagination — not recommended.** PCAOB AS, IAASB ISA, AICPA SSAE define the audit *process* and reportable items, but the workflow data (audit programs, working papers, sampling, control test results) is dominated by Wolters Kluwer CCH, Thomson Reuters, MindBridge, Workiva — all proprietary schemas. Recommend deferring.

#### Bench Management (`bench_management`)

- **Tier 3.**
- **Honest note:** **Would require imagination — not recommended.** No standards exist for consultant bench/utilisation. Vendors (Replicon, Mavenlink, Kantata, Beeline, Oracle PPM Cloud) each model differently. Even within Big 4 firms, the bench-management entities (skill, availability, ramp-up, named-account exclusivity) are firm-specific. Recommend deferring.

#### Knowledge Management (`knowledge_management`)

- **Tier 3.**
- **Honest note:** **Would require imagination — not recommended.** Knowledge-management schemas (case studies, methodologies, deliverables, expertise locator) are firm-specific. SECI / Nonaka model is conceptual; no data dictionary exists. Document repositories use generic metadata (DCMI, schema.org) but the *PS-firm* extensions are bespoke. Recommend deferring.

---

### Public Sector (9 subdomains)

#### Tax Administration (`tax_administration`)

- **Tier 1.**
- **One-liner:** Citizen and business tax filing, audit selection, refund processing, and compliance enforcement.
- **Standards / sources:**
  - IRS Modernized e-File (MeF) XML schemas: https://www.irs.gov/e-file-providers/modernized-e-file-mef-schemas-and-business-rules
  - IRS Form data dictionaries (1040, 1099, W-2, 1120, 941, etc.): https://www.irs.gov/forms-instructions
  - SSA EFW2 / EFW2C wage reporting.
  - OECD Standard Audit File for Tax (SAF-T): https://www.oecd.org/tax/administration/standardauditfile-taxsaf-t.htm
  - OECD Common Reporting Standard (CRS) and FATCA XML.
  - State Department of Revenue MeF state schemas.
- **Concrete entities:** Taxpayer, Filing Period, Return (1040 / 1120 / etc.), Schedule, Line Item, Information Return (1099 / W-2), Refund Disbursement, Audit Case, Examination Finding, Collection Lien.
- **Recommendation:** **Strong next-anchor candidate.** IRS MeF XML alone is one of the deepest, most public data models in government.

#### Court Records & Case Management (`court_records`)

- **Tier 1.**
- **One-liner:** Civil and criminal case filing, docketing, scheduling, and disposition across court systems.
- **Standards / sources:**
  - OASIS LegalXML Electronic Court Filing (ECF) 4.01 / 5.0: https://groups.oasis-open.org/communities/community-home?CommunityKey=4ce92f63-c534-413a-a9da-44e09c11b817
  - NIEM Justice Domain: https://release.niem.gov/niem-domains/justice/
  - National Center for State Courts (NCSC) data standards: https://www.ncsc.org/services-and-experts/areas-of-expertise/courts-data-standards
  - PACER / CM/ECF (federal courts) integration patterns: https://pacer.uscourts.gov/
- **Concrete entities:** Case, Party, Filing, Docket Entry, Hearing, Order, Judgment, Sentence, Charge / Statute, Court Calendar Slot.
- **Recommendation:** Build full model. ECF 4.01 + NIEM Justice fully attribute the model.

#### Emergency Response (`emergency_response`)

- **Tier 1.**
- **One-liner:** 911 dispatch, incident management, and inter-agency coordination for emergency services.
- **Standards / sources:**
  - NENA i3 (Next-Generation 9-1-1) standards: https://www.nena.org/page/i3_Stage3_Spec
  - OASIS Common Alerting Protocol (CAP) v1.2: https://docs.oasis-open.org/emergency/cap/v1.2/CAP-v1.2-os.html
  - OASIS Emergency Data Exchange Language (EDXL-DE, EDXL-RM, EDXL-SitRep): https://www.oasis-open.org/committees/tc_home.php?wg_abbrev=emergency
  - NIEM Emergency Management Domain.
  - APCO Project 25 (P25) for radio.
- **Concrete entities:** Call (PSAP), Caller Location, Incident, Unit, Dispatch Assignment, Status Change (En Route / On Scene / Clear), CAD Note, Multi-Agency Resource Request, CAP Alert.
- **Recommendation:** Build full model.

#### Social Services Case Management (`social_services_case_management`)

- **Tier 1.**
- **One-liner:** Intake, eligibility, services delivery, and outcomes tracking across child welfare, TANF, SNAP, and housing.
- **Standards / sources:**
  - NIEM Human Services Domain: https://acf.gov/cb/niem
  - ACF CCWIS (Comprehensive Child Welfare Information System) data model: https://acf.gov/cb/training-technical-assistance/ccwis
  - USDA SNAP / FNS Standardized E&T data: https://www.fns.usda.gov/snap/et
  - HUD HMIS Data Standards (free): https://www.hudexchange.info/programs/hmis/hmis-data-standards/
  - SSA EVS (Enumeration Verification Service).
- **Concrete entities:** Client / Household, Intake Application, Eligibility Determination, Benefit Issuance, Service Plan, Case Note, Worker, Provider, HMIS Universal Data Element, Outcome.
- **Recommendation:** Build full model.

#### Transit Operations (`transit_operations`)

- **Tier 1.**
- **One-liner:** Public transit operations: scheduling, real-time vehicle telemetry, and service alerts.
- **Standards / sources:**
  - GTFS-Static (Google / MobilityData): https://gtfs.org/schedule/reference/
  - GTFS-Realtime: https://gtfs.org/realtime/reference/
  - NeTEx (CEN/TS 16614): https://netex-cen.eu/
  - SIRI (Service Interface for Real-time Information): https://www.transmodel-cen.eu/standards/siri/
  - GBFS (Bikeshare / scooters): https://gbfs.org/
  - FTA NTD reporting templates: https://www.transit.dot.gov/ntd
- **Concrete entities:** Agency, Route, Trip, Stop, Stop Time, Vehicle Position, Trip Update, Service Alert, Calendar Date, Fare Rule.
- **Recommendation:** Build full model.

#### Benefits Administration (`benefits_administration`)

- **Tier 1.**
- **One-liner:** Eligibility, enrolment, and disbursement for social safety net and benefit programs.
- **Standards / sources:**
  - NIEM Human Services (above).
  - USDA SNAP / WIC / NSLP data dictionaries.
  - SSA Title II / Title XVI program records.
  - VA / TRICARE eligibility files.
  - State unemployment insurance UI ICON.
- **Concrete entities:** Beneficiary, Application, Eligibility Determination, Benefit Plan, Disbursement, Recertification, Sanction / Overpayment, Provider Enrollment, EBT Account.
- **Recommendation:** Build full model.

#### Licensing & Permits (`licensing_permits`)

- **Tier 2.**
- **One-liner:** Issue, renew, and inspect citizen and business licenses and permits across regulated activities.
- **Standards / sources:** NIEM (subset for permits); Accela Civic Platform docs (public): https://docs.accela.com/ ; Tyler Technologies EnerGov public docs; MyGovHub (Granicus) docs; OpenReferral HSDS (community services).
- **Concrete entities:** Application, License Type, Applicant, Inspection, Inspection Result, Violation, Renewal Cycle, Fee Schedule, Permit Document.
- **Recommendation:** Build from Accela + EnerGov + NIEM.

#### Defense Logistics (`defense_logistics`)

- **Tier 4.**
- **One-liner:** Sustainment of weapons systems — supply, maintenance, transportation, and readiness reporting.
- **Standards / sources:**
  - MIL-STD-3007 / MIL-STD-1388-2A LSAR (Logistic Support Analysis Record) — free DoD-published.
  - DLA / DLM 4000.25 series (Defense Logistics Manual).
  - NATO STANAGs for ammunition / spare parts.
  - DPAS (Defense Property Accountability System) data model — semi-public.
  - DLA EMALL data dictionary — restricted.
  - GFEBS / LMP / GCSS-Army public RFIs but actual schemas are CUI/FOUO.
- **Concrete entities (with DoD access):** Weapon System, NSN (National Stock Number), Bill of Materials, Maintenance Action, Supply Requisition, Readiness Rating (R-Rating), Materiel Movement, Property Book Item.
- **Recommendation:** **Hold pending DoD/CUI access.** Some MIL-STDs are public, but the day-to-day defense-logistics fact tables are CUI.

#### Intelligence Analytics (`intelligence_analytics`)

- **Tier 4.**
- **One-liner:** Multi-source fusion (SIGINT, OSINT, HUMINT) for analyst tradecraft, link analysis, and reporting.
- **Standards / sources:**
  - STIX 2.1 / TAXII (cyber threat intelligence — free): https://oasis-open.github.io/cti-documentation/
  - DDMS (DoD Discovery Metadata Specification — free): https://metadata.ces.mil/dse/irs/DDMS/
  - IC ITE Trusted Data Format (IC-TDF) — restricted.
  - CIDS (Community Intel Data Standard) — classified.
  - INT marker schemas (US, FVEY) — controlled.
- **Concrete entities (with cleared access):** Report, Source, Selector, Entity (Person / Org / Place), Link / Relationship, Confidence, Classification Marking, Disclosure Authorization, Tasking.
- **Recommendation:** **Hold pending cleared access.** STIX/TAXII covers the cyber-threat slice; the broader intelligence-analytics fact model lives behind classification.

---

### RCG — Retail / Consumer Goods crossover (3 subdomains)

#### Supply Chain (`supply_chain`)

- **Tier 1.**
- **One-liner:** End-to-end logistics, distribution, and inventory across DCs, carriers, and stores.
- **Standards / sources:**
  - GS1 EPCIS 2.0 (above).
  - ANSI ASC X12 EDI 850/810/856/852/214/940/943/945 (full set): https://x12.org/products/transaction-sets
  - GS1 GTIN, SSCC, GLN.
  - NRF Retail Data Model: https://nrf.com/research-insights/research-archive/data-model
  - VICS CPFR (Collaborative Planning, Forecasting and Replenishment).
- **Concrete entities:** Purchase Order, Advance Ship Notice, Goods Receipt, Inventory Position, Distribution Centre, Bill of Lading, Carrier Manifest, Transfer Order, Cycle Count, Lot Trace.
- **Recommendation:** Build full model. Heavily overlaps with Supply Chain Visibility (Manufacturing) and Merchandising (Retail anchor); could be consolidated with one of those.

#### Loyalty & CRM (`loyalty`)

- **Tier 3.**
- **Honest note:** **Would require imagination — not recommended.** Loyalty schemas vary radically by program (Sephora Beauty Insider, Starbucks Rewards, Sainsbury's Nectar, Carrefour Pass) — accrual ratios, tier rules, redemption catalogs, reciprocity. Salesforce Loyalty Management and SAP Emarsys publish partial APIs but none give an attribute-fidelity reference model. Recommend deferring.

#### Pricing (`pricing`)

- **Tier 3.**
- **Honest note:** **Would require imagination — not recommended.** List/promo/channel pricing engines (Pricefx, PROS Pricing, Vendavo, Zilliant) are competitive software with proprietary data dictionaries. Demand-elasticity inputs and price-recommendation outputs are not standardised. The *price entity* (price list, scale, discount) is straightforward but the optimisation entities (lift curve, competitive index) are vendor-specific. Recommend deferring or modelling only the basic price-list entity.

---

## Summary Table — Vertical × Tier

| Vertical | Tier 1 | Tier 2 | Tier 3 | Tier 4 | **Total** |
|---|---:|---:|---:|---:|---:|
| BFSI | 12 | 4 | 0 | 0 | **16** |
| Insurance | 2 | 2 | 0 | 3 | **7** |
| Healthcare | 8 | 0 | 0 | 0 | **8** |
| LifeSciences | 5 | 0 | 0 | 0 | **5** |
| Manufacturing | 5 | 4 | 1 | 0 | **10** |
| Retail | 3 | 2 | 2 | 0 | **7** |
| CPG | 1 | 1 | 2 | 0 | **4** |
| TTH | 5 | 3 | 2 | 0 | **10** |
| Telecom | 6 | 0 | 1 | 0 | **7** |
| Utilities | 2 | 2 | 0 | 2 | **6** |
| Energy | 3 | 0 | 1 | 1 | **5** |
| HiTech | 2 | 0 | 4 | 1 | **7** |
| Media | 4 | 1 | 0 | 0 | **5** |
| ProfessionalServices | 1 | 3 | 3 | 0 | **7** |
| PublicSector | 6 | 1 | 0 | 2 | **9** |
| RCG | 1 | 0 | 2 | 0 | **3** |
| **Total** | **66** | **23** | **18** | **9** | **116** |

---

## Recommended next anchors (Tier 1, highest leverage)

The seven existing anchors are excluded. The list below is ranked for next-round full attribution by **(a)** depth of the public spec, **(b)** coverage of a vertical that doesn't yet have an anchor, and **(c)** strategic fit (is this what customers ask about?).

1. **EHR Integrations** — HL7 FHIR R4/R5 + USCDI v3 + Epic on FHIR. The single highest-leverage Tier 1 in healthcare; FHIR resources directly become the entity list.
2. **Capital Markets** — FIX 4.4 + FpML 5.x + ISO 20022 securities. Three precise specs cover front-to-back; gives BFSI a deep front-office anchor (Payments was retail / corporate).
3. **Smart Metering** — ANSI C12.19/22 + DLMS-COSEM (IEC 62056) + CIM 61968-9 + SEP 2.0. Brings utilities to anchor-grade depth.
4. **Clinical Trials** — CDISC SDTM v2.0 + ADaM v1.3 + ODM-XML + Define-XML. Define-XML is *literally a data dictionary* — one of the cleanest Tier 1 sources on this list.
5. **Cloud FinOps** — FOCUS 1.2 / 1.3. Modern, ratified, native exports from AWS/Azure/GCP. Gives HiTech a fully-attributed anchor.
6. **EV Charging Operations** — OCPP 2.0.1 (now IEC 63584) + OCPI 2.2.1 + ISO 15118 + OpenADR. Energy-vertical anchor.
7. **Tax Administration** — IRS MeF XML + SAF-T + OECD CRS. Public sector anchor; among the deepest government XML schemas anywhere.
8. **Real-World Evidence** — OMOP CDM v5.4 (39 tables, fully documented). Best-in-class observational health data model.
9. **Settlement & Clearing** — ISO 20022 securities messages (sese / semt / camt) + DTCC NSCC/DTC docs. Pairs naturally with Payments and Capital Markets anchors.
10. **Ad Tech / Programmatic Advertising** — IAB OpenRTB 2.6 + VAST 4.x + OMID + ads.txt. Single-vertical depth; the Media vertical's strongest candidate.

---

## Subdomains explicitly NOT recommended for full attribution

These 18 Tier 3 subdomains should remain in the taxonomy with their current entity stubs but should **not** be expanded to attribute fidelity without real customer data:

Brand Marketing, Trade Promotion Management, Loyalty & CRM, Pricing (RCG), Airline Loyalty, Airline Revenue Management, Refinery Operations, Chip Design (EDA), Developer Relations, License Management, Marketplace Operations, Audit Workflow, Bench Management, Knowledge Management, Warranty & Aftermarket, Dark Stores, Store Operations, Churn Management.

In every case the *entities* are knowable but the *attributes* are vendor- or customer-specific. Filling them in from imagination would mislead users.

---

## Tier 4 subdomains — block-listed pending paid memberships

These 9 subdomains have precise standards but require paid access. They are cataloguable but not buildable without an org-level investment in membership:

Life & Annuity (ACORD), Reinsurance (ACORD), Underwriting (Verisk ISO / NCCI / ACORD), Asset Health Monitoring (IEC 61850 / 61968 / 61970), Grid Operations (IEC + NERC), Renewable Generation (IEC 61400-25 / 61724), Semiconductor Yield (SEMI E-series), Defense Logistics (DoD CUI), Intelligence Analytics (IC).

If/when memberships are obtained, these all become Tier 1 candidates.

---

## Caveats & honesty notes

- "Tier 1" here means a *single-document or two-document* spec covers most of the entity-attribute landscape. It does not guarantee that a customer's actual implementation matches the spec exactly. Real customer schemas drift.
- "Tier 2" means we believe 2–3 vendors converge enough that triangulation works. We have not validated this by building each one — that's the next step.
- "Tier 3" means **don't model attributes**. Listing entity *names* is fine; assigning columns is speculation. The brief explicitly forbids imagination.
- "Tier 4" means the standard exists and is precise, but reading it requires payment. We have NOT attempted to model from leaked / second-hand copies.
- The seven existing anchors were tagged inline; their tier reflects what was actually used to build them, which in some cases (P&C Claims) blends Tier 4 paid (ACORD) and Tier 2 free (Guidewire docs).
- Subdomains that overlap heavily (Programmatic Advertising vs. Ad Tech; Last Mile Delivery vs. Last-Mile Logistics; Supply Chain vs. Supply Chain Visibility) should be considered for consolidation in the next taxonomy revision.

---

*End of audit.*
