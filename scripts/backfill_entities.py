"""Backfill light dataModel.entities arrays for all subdomains that lack them.

Adds 5-7 representative entity names + a 1-line description each. Editable text-only
inserts — does not rewrite the rest of the YAML.
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TAX = ROOT / "data" / "taxonomy"

# Curated entity catalogue. Each value is a list of (entity_name, description).
ENTITIES = {
    "ad_inventory": [
        ("AdSlot", "Inventory unit on a page or surface"),
        ("Placement", "Configured placement targeting"),
        ("Impression", "Served ad impression"),
        ("Forecast", "Inventory availability forecast"),
        ("AdBreak", "Video ad break definition"),
    ],
    "ad_tech": [
        ("Campaign", "Advertiser campaign"),
        ("Creative", "Creative asset"),
        ("Audience", "Targeting audience segment"),
        ("Conversion", "Tracked conversion event"),
        ("Bid", "Bid price/decision record"),
    ],
    "airline_disruption": [
        ("Flight", "Operating flight"),
        ("Disruption", "Cancellation/diversion event"),
        ("Rebooking", "Passenger rebooking"),
        ("CrewAssignment", "Crew assignment record"),
        ("AircraftRotation", "Aircraft rotation plan"),
    ],
    "airline_loyalty": [
        ("Member", "Loyalty member"),
        ("MileBalance", "Member mile balance"),
        ("AccrualEvent", "Mile accrual event"),
        ("RedemptionEvent", "Mile redemption event"),
        ("TierStatus", "Tier status assignment"),
        ("Promotion", "Loyalty promotion"),
    ],
    "airline_revenue_management": [
        ("Fare", "Filed fare"),
        ("BookingClass", "Inventory booking class"),
        ("Demand", "Demand forecast"),
        ("OD", "Origin-destination market"),
        ("RevenueOpportunity", "Spill / spoilage record"),
    ],
    "asset_health_monitoring": [
        ("Asset", "Monitored asset"),
        ("HealthScore", "Calculated health score"),
        ("SensorReading", "Telemetry reading"),
        ("Anomaly", "Detected anomaly"),
        ("MaintenanceEvent", "Linked maintenance event"),
    ],
    "bench_management": [
        ("Consultant", "Consulting employee"),
        ("Engagement", "Client engagement"),
        ("Allocation", "Consultant-to-engagement allocation"),
        ("BenchPeriod", "Period of unbillable bench time"),
        ("SkillProfile", "Consultant skill profile"),
    ],
    "benefits_administration": [
        ("Citizen", "Benefits applicant"),
        ("Application", "Benefits application"),
        ("EligibilityRecord", "Determined eligibility"),
        ("Payment", "Benefit payment"),
        ("Recertification", "Periodic recertification"),
    ],
    "bill_of_materials": [
        ("Product", "Manufactured product"),
        ("BomLine", "BOM line item"),
        ("Component", "Sub-component"),
        ("EngineeringChange", "Engineering change order"),
        ("RoutingStep", "Production routing step"),
    ],
    "bss_oss": [
        ("Customer", "Telecom customer"),
        ("ProductInstance", "Provisioned service instance"),
        ("Order", "Service order"),
        ("Inventory", "Network resource inventory"),
        ("Trouble", "Trouble ticket"),
        ("Bill", "Customer bill"),
    ],
    "capital_markets": [
        ("Trade", "Executed trade"),
        ("Order", "Order to trade"),
        ("Position", "End-of-day position"),
        ("Instrument", "Tradeable instrument"),
        ("MarketData", "Market data tick"),
        ("SettlementInstruction", "SSI for clearing"),
    ],
    "cards": [
        ("Cardholder", "Cardholder profile"),
        ("Card", "Issued card"),
        ("CardTransaction", "Card-present or CNP transaction"),
        ("AuthorizationLog", "Auth attempt record"),
        ("FraudDecision", "Fraud decision outcome"),
        ("Statement", "Periodic cardholder statement"),
        ("RewardsAccrual", "Rewards point accrual"),
    ],
    "churn_management": [
        ("Subscriber", "Service subscriber"),
        ("ChurnSignal", "Predictive churn signal"),
        ("Save", "Retention save event"),
        ("Offer", "Retention offer"),
        ("LifecycleEvent", "Lifecycle stage event"),
    ],
    "clinical_trials": [
        ("Trial", "Clinical trial"),
        ("Site", "Investigator site"),
        ("Subject", "Enrolled subject"),
        ("Visit", "Trial visit"),
        ("AdverseEvent", "Reported adverse event"),
        ("EDCForm", "Electronic data capture form"),
    ],
    "cloud_finops": [
        ("Account", "Cloud billing account"),
        ("Resource", "Tagged cloud resource"),
        ("CostLineItem", "CUR/billing line item"),
        ("Budget", "Configured budget"),
        ("Anomaly", "Spend anomaly"),
        ("Commitment", "Reserved/savings commitment"),
    ],
    "content_metadata": [
        ("Title", "Content title / programme"),
        ("Episode", "Episode within a series"),
        ("Asset", "Encoded video asset"),
        ("Right", "Acquired/licensed right"),
        ("MetadataRecord", "Descriptive metadata"),
    ],
    "contract_management": [
        ("Contract", "Master contract record"),
        ("Clause", "Reusable clause"),
        ("Obligation", "Contractual obligation"),
        ("Renewal", "Contract renewal"),
        ("Counterparty", "Contracting counterparty"),
    ],
    "court_records": [
        ("Case", "Court case"),
        ("Filing", "Court filing"),
        ("Hearing", "Scheduled hearing"),
        ("Party", "Case party"),
        ("Ruling", "Judicial ruling"),
    ],
    "customer_analytics": [
        ("Customer", "Customer master record"),
        ("Segment", "Behavioural segment"),
        ("Event", "Customer event"),
        ("Journey", "Multi-touch journey"),
        ("LtvScore", "Lifetime-value score"),
    ],
    "customer_care": [
        ("Case", "Care case / ticket"),
        ("Contact", "Customer contact attempt"),
        ("KnowledgeArticle", "Knowledge article"),
        ("SLA", "Linked SLA target"),
        ("Survey", "Post-contact survey"),
    ],
    "defense_logistics": [
        ("Asset", "Defence asset"),
        ("Maintenance", "Maintenance record"),
        ("SupplyClass", "Supply class category"),
        ("Movement", "Logistics movement"),
        ("Requisition", "Supply requisition"),
    ],
    "device_telemetry": [
        ("Device", "Connected device"),
        ("Telemetry", "Device telemetry sample"),
        ("Event", "Device event"),
        ("Firmware", "Firmware version"),
        ("Cohort", "Telemetry cohort"),
    ],
    "ecommerce": [
        ("Order", "Customer order"),
        ("Cart", "Shopping cart"),
        ("Product", "Product / SKU"),
        ("Customer", "Shopper"),
        ("Inventory", "Inventory snapshot"),
        ("Promotion", "Applied promotion"),
    ],
    "ehr_integrations": [
        ("Patient", "Patient record"),
        ("Encounter", "Clinical encounter"),
        ("Observation", "FHIR observation"),
        ("MedicationOrder", "Medication order"),
        ("LabResult", "Laboratory result"),
    ],
    "ehs": [
        ("Incident", "Safety incident"),
        ("NearMiss", "Near-miss report"),
        ("InspectionRecord", "EHS inspection"),
        ("PermitToWork", "Issued permit-to-work"),
        ("Hazard", "Logged hazard"),
    ],
    "energy_trading": [
        ("Trade", "Energy trade"),
        ("Position", "Net position"),
        ("Schedule", "Delivery schedule"),
        ("MarketPrice", "Market price tick"),
        ("RiskMeasure", "Calculated risk measure"),
    ],
    "ev_charging": [
        ("ChargingStation", "Physical charging station"),
        ("Charger", "Charger / dispenser"),
        ("Session", "Charging session"),
        ("Driver", "Registered driver"),
        ("Tariff", "Pricing tariff"),
    ],
    "expense_management": [
        ("Report", "Expense report"),
        ("ExpenseLine", "Individual line item"),
        ("Receipt", "Captured receipt"),
        ("Approval", "Approval step"),
        ("Reimbursement", "Reimbursement payout"),
    ],
    "fleet_telematics": [
        ("Vehicle", "Tracked vehicle"),
        ("TripEvent", "Trip event"),
        ("DriverEvent", "Driver behaviour event"),
        ("FuelTransaction", "Fuel purchase"),
        ("MaintenanceAlert", "Maintenance alert"),
    ],
    "fraud": [
        ("FraudCase", "Investigated fraud case"),
        ("Alert", "Fraud detection alert"),
        ("RuleHit", "Rule firing record"),
        ("ModelScore", "ML model score"),
        ("Disposition", "Case disposition"),
    ],
    "grid_ops": [
        ("Substation", "Grid substation"),
        ("Feeder", "Distribution feeder"),
        ("Switch", "Distribution switch"),
        ("DispatchOrder", "Dispatch instruction"),
        ("Telemetry", "SCADA telemetry"),
    ],
    "hotel_distribution": [
        ("Property", "Hotel property"),
        ("RatePlan", "Rate plan"),
        ("Inventory", "Room inventory"),
        ("Reservation", "Reservation record"),
        ("Channel", "Distribution channel"),
    ],
    "intelligence_analytics": [
        ("Source", "Intelligence source"),
        ("Report", "Intelligence report"),
        ("Entity", "Entity of interest"),
        ("Link", "Relationship between entities"),
        ("Indicator", "Indicator of compromise / interest"),
    ],
    "knowledge_management": [
        ("Article", "Knowledge article"),
        ("Topic", "Topic taxonomy"),
        ("Author", "Article author"),
        ("Version", "Article version"),
        ("Feedback", "Reader feedback"),
    ],
    "kyc_aml": [
        ("CustomerDueDiligence", "CDD record"),
        ("SanctionsHit", "Sanctions screening hit"),
        ("PepScreening", "Politically exposed person screening"),
        ("TransactionAlert", "Transaction monitoring alert"),
        ("SAR", "Suspicious activity report"),
        ("KycRefresh", "Periodic KYC refresh"),
    ],
    "last_mile_logistics": [
        ("Shipment", "Last-mile shipment"),
        ("Stop", "Stop on a route"),
        ("Route", "Optimised route"),
        ("Driver", "Delivery driver"),
        ("Exception", "Delivery exception"),
    ],
    "lending": [
        ("Application", "Loan application"),
        ("Loan", "Funded loan"),
        ("Underwriting", "Underwriting decision"),
        ("Payment", "Loan payment"),
        ("Delinquency", "Delinquency event"),
        ("Collateral", "Pledged collateral"),
    ],
    "license_management": [
        ("LicenseAsset", "Software license asset"),
        ("Entitlement", "Entitlement record"),
        ("Usage", "License usage record"),
        ("Vendor", "Software vendor"),
        ("Renewal", "Renewal event"),
    ],
    "licensing_permits": [
        ("Application", "Permit/license application"),
        ("Permit", "Issued permit"),
        ("Inspection", "Permit inspection"),
        ("Fee", "Application/permit fee"),
        ("Violation", "Recorded violation"),
    ],
    "loyalty": [
        ("Member", "Loyalty member"),
        ("PointsBalance", "Points balance"),
        ("Earn", "Points earn event"),
        ("Burn", "Points redemption event"),
        ("Tier", "Member tier"),
        ("Offer", "Personalised offer"),
    ],
    "maintenance": [
        ("Asset", "Maintainable asset"),
        ("WorkOrder", "Maintenance work order"),
        ("Task", "Work order task"),
        ("Inspection", "Inspection record"),
        ("PartsConsumption", "Spare parts consumed"),
    ],
    "marketplace_operations": [
        ("Seller", "Marketplace seller"),
        ("Listing", "Product listing"),
        ("Order", "Marketplace order"),
        ("Payout", "Seller payout"),
        ("Dispute", "Buyer-seller dispute"),
    ],
    "medical_devices": [
        ("Device", "Medical device"),
        ("Complaint", "Device complaint"),
        ("Servicing", "Servicing event"),
        ("Calibration", "Calibration record"),
        ("UDI", "Unique device identifier"),
    ],
    "mortgage_servicing": [
        ("Loan", "Mortgage loan"),
        ("Borrower", "Borrower party"),
        ("Payment", "Mortgage payment"),
        ("Escrow", "Escrow account"),
        ("Delinquency", "Delinquency event"),
        ("Modification", "Loan modification"),
    ],
    "outage_management": [
        ("Outage", "Distribution outage"),
        ("Crew", "Field crew"),
        ("Restoration", "Restoration step"),
        ("CallReport", "Customer outage call"),
        ("CauseCode", "Outage cause code"),
    ],
    "payer_provider": [
        ("Member", "Health plan member"),
        ("Provider", "Healthcare provider"),
        ("Claim", "Submitted medical claim"),
        ("Authorization", "Prior authorisation"),
        ("Capitation", "Capitation arrangement"),
    ],
    "pricing": [
        ("Product", "Priced product / SKU"),
        ("PriceList", "Active price list"),
        ("Promotion", "Promotion or markdown"),
        ("CompetitorPrice", "Observed competitor price"),
        ("PriceChange", "Price change event"),
    ],
    "production_scheduling": [
        ("WorkOrder", "Production work order"),
        ("Resource", "Production resource"),
        ("Shift", "Operating shift"),
        ("Schedule", "Optimised schedule"),
        ("Constraint", "Production constraint"),
    ],
    "real_world_evidence": [
        ("Patient", "RWE patient cohort member"),
        ("ClaimsRecord", "Linked claims record"),
        ("EhrRecord", "Linked EHR record"),
        ("Cohort", "Defined cohort"),
        ("Outcome", "Measured outcome"),
    ],
    "refinery_operations": [
        ("Unit", "Process unit"),
        ("Stream", "Hydrocarbon stream"),
        ("Yield", "Yield record"),
        ("LabSample", "Lab sample analysis"),
        ("ShutdownEvent", "Planned/unplanned shutdown"),
    ],
    "regulatory_reporting": [
        ("Report", "Regulatory report"),
        ("Filing", "Submitted filing"),
        ("Threshold", "Reporting threshold"),
        ("Lineage", "Report-to-source lineage"),
        ("Exception", "Reporting exception"),
    ],
    "returns_management": [
        ("ReturnRequest", "Customer return request"),
        ("RmaTicket", "Issued RMA ticket"),
        ("Disposition", "Return disposition"),
        ("Refund", "Issued refund"),
        ("Reason", "Return reason code"),
    ],
    "revenue_cycle": [
        ("Encounter", "Patient encounter"),
        ("Charge", "Charge capture"),
        ("Claim", "Submitted claim"),
        ("Denial", "Claim denial"),
        ("Payment", "Posted payment"),
        ("Adjustment", "Contractual adjustment"),
    ],
    "ride_share_dispatch": [
        ("Rider", "Ride-share rider"),
        ("Driver", "Ride-share driver"),
        ("Ride", "Completed or active ride"),
        ("DispatchOffer", "Match offer to driver"),
        ("Surge", "Surge pricing event"),
    ],
    "saas_metrics": [
        ("Account", "Tenant account"),
        ("Subscription", "Active subscription"),
        ("MrrMovement", "MRR movement event"),
        ("Churn", "Churn event"),
        ("UsageMetric", "Usage metric reading"),
    ],
    "securities_lending": [
        ("Loan", "Securities loan"),
        ("Collateral", "Posted collateral"),
        ("Recall", "Recall instruction"),
        ("Rebate", "Rebate calculation"),
        ("Counterparty", "Borrower counterparty"),
    ],
    "semiconductor_yield": [
        ("Wafer", "Manufactured wafer"),
        ("Die", "Individual die"),
        ("TestRun", "Wafer/die test run"),
        ("DefectMap", "Defect map"),
        ("ProcessStep", "Fab process step"),
    ],
    "settlement_clearing": [
        ("Trade", "Trade pending settlement"),
        ("Allocation", "Allocation to underlying account"),
        ("Confirmation", "Trade confirmation"),
        ("Settlement", "Settlement record"),
        ("Fail", "Settlement fail event"),
    ],
    "shop_floor_iot": [
        ("Machine", "Production machine"),
        ("Sensor", "Attached sensor"),
        ("Reading", "Sensor reading"),
        ("Event", "Machine event"),
        ("OeeMeasurement", "OEE measurement window"),
    ],
    "social_services_case_management": [
        ("Case", "Social services case"),
        ("Caseworker", "Assigned caseworker"),
        ("Visit", "Home/field visit"),
        ("ServicePlan", "Service plan"),
        ("Assessment", "Risk/need assessment"),
    ],
    "store_ops": [
        ("Store", "Retail store"),
        ("Shift", "Employee shift"),
        ("LaborSchedule", "Labor schedule"),
        ("Task", "Store task"),
        ("Audit", "Store ops audit"),
    ],
    "subscriber_billing": [
        ("Subscriber", "Telecom subscriber"),
        ("Plan", "Subscribed plan"),
        ("UsageRecord", "Usage data record"),
        ("Invoice", "Periodic invoice"),
        ("Payment", "Customer payment"),
    ],
    "supplier_quality": [
        ("Supplier", "Material supplier"),
        ("Inspection", "Receiving inspection"),
        ("Defect", "Detected defect"),
        ("CapaAction", "Corrective/preventive action"),
        ("Scorecard", "Supplier scorecard"),
    ],
    "supply_chain": [
        ("PurchaseOrder", "Purchase order to supplier"),
        ("Shipment", "Inbound/outbound shipment"),
        ("InventoryPosition", "Inventory position by node"),
        ("Demand", "Aggregated demand"),
        ("Forecast", "Demand forecast"),
    ],
    "time_and_billing": [
        ("Project", "Client project"),
        ("Timesheet", "Submitted timesheet"),
        ("Invoice", "Client invoice"),
        ("Receivable", "Outstanding receivable"),
        ("RateCard", "Project rate card"),
    ],
    "trade_promotion": [
        ("Promotion", "Trade promotion"),
        ("Account", "Retailer account"),
        ("Plan", "Promotional plan"),
        ("Lift", "Measured lift"),
        ("Deduction", "Customer deduction"),
    ],
    "treasury": [
        ("CashPosition", "Cash position by account"),
        ("FxTrade", "FX trade"),
        ("LiquidityForecast", "Liquidity forecast"),
        ("BankAccount", "Bank account"),
        ("Funding", "Intra-day funding action"),
    ],
    "value_based_care": [
        ("AttributedMember", "Attributed member"),
        ("CareGap", "Identified care gap"),
        ("QualityMeasure", "Quality measure"),
        ("PerformanceContract", "Risk-bearing contract"),
        ("Encounter", "Member encounter"),
    ],
    "warranty": [
        ("WarrantyClaim", "Warranty claim"),
        ("Product", "Covered product"),
        ("Repair", "Repair record"),
        ("FailureMode", "Catalogued failure mode"),
        ("Reimbursement", "Dealer reimbursement"),
    ],
    "wealth_management": [
        ("Client", "Wealth client / household"),
        ("Account", "Investment account"),
        ("Holding", "Account holding"),
        ("Plan", "Financial plan"),
        ("Goal", "Client goal"),
        ("AdvisorReview", "Advisor review record"),
    ],
}


def already_has_entities(text: str) -> bool:
    """True if the YAML text already declares dataModel.entities (non-empty)."""
    if "dataModel:" not in text:
        return False
    # crude: check that entities: is followed by at least one '- ' bullet within 20 lines
    lines = text.splitlines()
    in_dm = False
    for i, line in enumerate(lines):
        if line.startswith("dataModel:"):
            in_dm = True
            continue
        if in_dm:
            stripped = line.strip()
            if stripped.startswith("entities:"):
                # peek ahead
                for j in range(i + 1, min(i + 20, len(lines))):
                    nxt = lines[j].strip()
                    if nxt.startswith("- "):
                        return True
                    if nxt and not nxt.startswith("#") and ":" in nxt and not nxt.startswith("- "):
                        # we hit a different top-level key
                        return False
                return False
            if line and not line.startswith(" "):
                return False
    return False


def emit_block(entities) -> str:
    out = ["dataModel:", "  entities:"]
    for name, desc in entities:
        # quote desc with single quotes; escape embedded single quotes
        esc = desc.replace("'", "''")
        out.append(f"    - {{ name: {name}, description: '{esc}' }}")
    return "\n".join(out) + "\n"


def insert_block(text: str, block: str) -> str:
    """Insert block before sourceSystems: section, or append at EOF."""
    lines = text.splitlines(keepends=True)
    insertion = -1
    for i, line in enumerate(lines):
        if line.startswith("sourceSystems:"):
            insertion = i
            break
    block_with_sep = block + "\n"
    if insertion == -1:
        # append
        if not text.endswith("\n"):
            return text + "\n" + block_with_sep
        return text + block_with_sep
    return "".join(lines[:insertion]) + block_with_sep + "".join(lines[insertion:])


def main():
    updated = 0
    skipped = 0
    for sub_id, ents in ENTITIES.items():
        path = TAX / f"{sub_id}.yaml"
        if not path.exists():
            print(f"SKIP missing: {sub_id}")
            continue
        text = path.read_text(encoding="utf-8")
        if already_has_entities(text):
            skipped += 1
            continue
        block = emit_block(ents)
        # If file has dataModel: { entities: [] } empty but no entities, just replace dataModel block
        if "dataModel:" in text:
            # Replace empty/lone dataModel block with our block
            new = re.sub(
                r"dataModel:\s*\n(?:\s+entities:\s*\[\]\s*\n)?",
                block + "\n",
                text,
                count=1,
            )
            if new == text:
                # didn't match — fall back to insert_block path: drop existing dataModel: lines and reinsert
                lines = text.splitlines(keepends=True)
                kept = []
                in_dm = False
                for line in lines:
                    if line.startswith("dataModel:"):
                        in_dm = True
                        continue
                    if in_dm:
                        if line and not line.startswith(" ") and not line.startswith("\t"):
                            in_dm = False
                            kept.append(line)
                        # else: skip dataModel inner lines
                    else:
                        kept.append(line)
                new = insert_block("".join(kept), block)
            text = new
        else:
            text = insert_block(text, block)
        path.write_text(text, encoding="utf-8")
        updated += 1
    print(f"updated={updated} already_had={skipped}")


if __name__ == "__main__":
    main()
