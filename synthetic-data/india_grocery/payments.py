"""Payments at Store 014's tills, on top of the world's bills.

Every bill is paid. What varies is how many tries it takes and what each party records.
A UPI attempt can be approved, declined for the customer's reasons (a business decline),
fail fast for a technical reason, or time out at the till. A timed-out attempt may already
have debited the customer: UPI then settles it later, either crediting the merchant late
or returning the money to the customer within RBI's T+5 days. Meanwhile the till has said
"failed" and the cashier has taken a second payment.

All random numbers are drawn up front per bill (common random numbers), so the till and
reconciliation policies in ``PayScenario`` change outcomes but never the customers, their
baskets or their banks.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta

import numpy as np

from . import spec
from .spec import param

COLS = 24
ATTEMPT_COLS = 6
MAX_UPI = 3
SECONDS = {"approved": 25, "declined": 15, "failed": 15, "timeout": 30, "card": 25, "cash": 40}
TILL_POLICIES = ("retry", "check")
RECON_POLICIES = ("manual", "bill_ref")


@dataclass(frozen=True)
class PayScenario:
    """How the store handles a UPI payment that times out, and how it reconciles."""

    till: str = "retry"  # "retry": take another payment at once; "check": wait for the 90-second status check first
    recon: str = "manual"  # "manual": match credits to bills by amount and time; "bill_ref": each UPI request carries its bill ID

    def __post_init__(self) -> None:
        if self.till not in TILL_POLICIES or self.recon not in RECON_POLICIES:
            raise ValueError(f"unknown till {self.till!r} or recon {self.recon!r}")

    @property
    def key(self) -> str:
        return f"{self.till}|{self.recon}"


AS_TODAY = PayScenario()


@dataclass
class Payments:
    scenario: PayScenario
    attempts: list[dict] = field(default_factory=list)  # truth and till view, one row per attempt
    psp: list[dict] = field(default_factory=list)  # the payment service provider's report, one row per UPI attempt
    refunds: list[dict] = field(default_factory=list)
    complaints: list[dict] = field(default_factory=list)
    doubles: list[dict] = field(default_factory=list)  # truth: bills a customer paid twice
    returns: list[dict] = field(default_factory=list)  # truth: debits the customer's bank gave back
    bill_seconds: dict[str, float] = field(default_factory=dict)  # time spent paying, per bill


def _ts(t: datetime) -> str:
    return t.isoformat(timespec="seconds")


def draws(seed: int, n: int) -> np.ndarray:
    """One row of uniforms per bill, in bill order. Independent of every store stream."""
    return np.random.default_rng([seed, 1001]).random((n, COLS))


def _in_slowdown(t: datetime) -> bool:
    s = param("upi_slowdown")
    return s["start"] <= _ts(t)[:16] < s["end"]  # type: ignore[index]


def june_bills(bills: list[dict]) -> list[dict]:
    return [b for b in bills if b["bill_ts"] >= spec.STORY_START.isoformat()]


def simulate_payments(bills: list[dict], scn: PayScenario = AS_TODAY, seed: int = 42,
                      u: np.ndarray | None = None) -> Payments:
    """Pay every bill of the story month. ``bills`` may hold the whole world; May is skipped."""
    bills = june_bills(bills)
    u = draws(seed, len(bills)) if u is None else u
    pay = Payments(scenario=scn)
    bd, td, tout = (float(param(k)) for k in ("upi_business_decline", "upi_technical_decline", "upi_till_timeout"))  # type: ignore[arg-type]
    slow = param("upi_slowdown")
    p_debited = float(param("upi_timeout_debited"))  # type: ignore[arg-type]
    p_late = float(param("upi_debited_late_credit"))  # type: ignore[arg-type]
    timing = param("upi_late_credit_timing")
    return_days = np.cumsum(param("upi_return_days"))  # type: ignore[arg-type]
    after = param("after_upi_failure")
    check_s = int(param("upi_status_check_seconds"))  # type: ignore[arg-type]
    c_double = float(param("complaint_charged_twice"))  # type: ignore[arg-type]
    c_return = float(param("complaint_debited_returned"))  # type: ignore[arg-type]
    refund_days = param("manual_refund_days")
    card_decline = float(param("card_decline"))  # type: ignore[arg-type]
    rrn_serial = 0
    end = datetime.combine(spec.END, datetime.min.time()).replace(hour=22)

    for i, b in enumerate(bills):
        row = u[i]
        clock = datetime.fromisoformat(b["bill_ts"]) + timedelta(seconds=int(row[0] * 59))
        start = clock
        tender = b["tender"]
        amount = float(b["amount_inr"])
        n_upi = 0
        debits: list[dict] = []  # UPI attempts that took the customer's money and did not complete the sale
        attempt = 0
        while True:
            base = 1 + min(attempt, 2) * ATTEMPT_COLS
            attempt += 1
            if tender == "cash":
                pay.attempts.append({"bill_id": b["bill_id"], "attempt": attempt, "ts": _ts(clock), "tender": "cash",
                                     "amount_inr": amount, "till_status": "approved", "rrn": None, "note": None,
                                     "debited": False, "final": "paid", "resolved_ts": _ts(clock)})
                clock += timedelta(seconds=SECONDS["cash"])
                break
            if tender == "card":
                ok = bool(row[23] >= card_decline or attempt > 1)
                pay.attempts.append({"bill_id": b["bill_id"], "attempt": attempt, "ts": _ts(clock), "tender": "card",
                                     "amount_inr": amount, "till_status": "approved" if ok else "declined", "rrn": None,
                                     "note": None, "debited": ok, "final": "paid" if ok else "declined",
                                     "resolved_ts": _ts(clock)})
                clock += timedelta(seconds=SECONDS["card"])
                if ok:
                    break
                tender = "cash"
                continue

            # UPI
            n_upi += 1
            rrn_serial += 1
            # A 12-digit retrieval reference number: year digit, day of year, hour, serial.
            rrn = f"6{clock.timetuple().tm_yday:03d}{clock.hour:02d}{rrn_serial % 1_000_000:06d}"
            x = row[base]
            if _in_slowdown(clock):
                p_td, p_to = float(slow["technical"]), float(slow["timeout"])  # type: ignore[index]
            else:
                p_td, p_to = td, tout
            note = None
            if x < bd:
                outcome, debited, final, resolved = "declined", False, "declined", clock
            elif x < bd + p_td:
                outcome, debited, final, resolved = "failed", False, "failed", clock
            elif x < bd + p_td + p_to:
                outcome = "timed out"
                debited = bool(row[base + 1] < p_debited)
                if debited and row[base + 2] < p_late:
                    # The merchant is credited late: often seconds after the till gave up, sometimes
                    # only when the deemed-approved payment is confirmed after settlement, hours later.
                    final = "late credit"
                    if row[base + 4] < float(timing["within_90s"]):  # type: ignore[index]
                        resolved = clock + timedelta(seconds=40 + 50 * row[base + 5])
                    else:
                        lo, hi = timing["hours"]  # type: ignore[index]
                        resolved = clock + timedelta(hours=float(lo) + (float(hi) - float(lo)) * row[base + 5] ** 2)
                elif debited:
                    final = "returned"
                    day = int(np.searchsorted(return_days, row[base + 5], side="right")) + 1
                    resolved = datetime.combine(clock.date() + timedelta(days=day), datetime.min.time()).replace(hour=11)
                else:
                    final, resolved = "failed", clock + timedelta(seconds=SECONDS["timeout"])
            else:
                outcome, debited, final, resolved = "approved", True, "success", clock

            paid = outcome == "approved"
            wait = SECONDS["approved"] if paid else SECONDS["timeout"] if outcome == "timed out" else SECONDS["declined"]
            if outcome == "timed out" and scn.till == "check":
                # Wait for the first status check NPCI allows, 90 seconds after the payment.
                wait = check_s
                if final == "late credit" and resolved <= clock + timedelta(seconds=check_s):
                    outcome, paid = "approved after status check", True
                elif final == "failed" and row[base + 4] < 0.8:
                    outcome = "failed at status check"
                else:
                    outcome, note = "pending at status check", "UPI pending: second payment taken"
            till_status = {"timed out": "failed: no response"}.get(outcome, outcome)
            pay.attempts.append({"bill_id": b["bill_id"], "attempt": attempt, "ts": _ts(clock), "tender": "UPI",
                                 "amount_inr": amount, "till_status": till_status, "rrn": rrn, "note": note,
                                 "debited": debited, "final": final, "resolved_ts": _ts(resolved)})
            psp_status = {"success": "success", "late credit": "success", "returned": "returned"}.get(final, "failed")
            pay.psp.append({"rrn": rrn, "initiated_ts": _ts(clock), "amount_inr": amount, "status": psp_status,
                            "status_ts": _ts(resolved),
                            "bill_ref": b["bill_id"] if scn.recon == "bill_ref" else None})
            if not paid and debited and final in ("late credit", "returned"):
                debits.append({"rrn": rrn, "ts": clock, "final": final, "resolved": resolved, "attempt": attempt})
            clock += timedelta(seconds=wait)
            if paid:
                break
            # Next tender: try UPI again, or switch.
            y = row[base + 3]
            if n_upi < MAX_UPI and y < float(after["upi_again"]):  # type: ignore[index]
                tender = "UPI"
            elif y < float(after["upi_again"]) + float(after["cash"]):  # type: ignore[index]
                tender = "cash"
            else:
                tender = "card"

        pay.bill_seconds[b["bill_id"]] = (clock - start).total_seconds()

        for d in debits:
            if d["final"] == "returned":
                complained = row[22] < c_return
                pay.returns.append({"bill_id": b["bill_id"], "rrn": d["rrn"], "amount_inr": amount,
                                    "debited_ts": _ts(d["ts"]), "returned_ts": _ts(d["resolved"]),
                                    "days": (d["resolved"].date() - d["ts"].date()).days})
                if complained:
                    when = datetime.combine(d["ts"].date() + timedelta(days=1), datetime.min.time()).replace(hour=10)
                    when = min(when, d["resolved"] - timedelta(minutes=30))
                    pay.complaints.append({"complaint_ts": _ts(when), "kind": "debited but the till said failed",
                                           "amount_inr": amount, "bill_id": b["bill_id"], "rrn": d["rrn"],
                                           "resolved_ts": _ts(d["resolved"]),
                                           "resolution": "customer's bank returned the money"})
                continue
            # A late credit: the store now holds two payments for one bill.
            credited = d["resolved"]
            refund = None
            if scn.recon == "bill_ref":
                # The credit names its bill, so the next morning's match flags it and refunds it.
                refund_at = datetime.combine(credited.date() + timedelta(days=1), datetime.min.time()).replace(hour=10)
                refund = {"trigger": "automatic match on bill ID", "requested": refund_at,
                          "completed": refund_at + timedelta(hours=2)}
                if row[19] < c_double * 0.3 and credited < refund_at - timedelta(hours=1):
                    pay.complaints.append({"complaint_ts": _ts(credited + timedelta(minutes=45)), "kind": "charged twice",
                                           "amount_inr": amount, "bill_id": b["bill_id"], "rrn": d["rrn"],
                                           "resolved_ts": _ts(refund["completed"]),
                                           "resolution": "refund already scheduled"})
            elif row[19] < c_double:
                complaint = datetime.combine(credited.date() + timedelta(days=1 + int(row[20] * 3)),
                                             datetime.min.time()).replace(hour=10 + int(row[20] * 30) % 10)
                lo, hi = refund_days  # type: ignore[misc]
                done = complaint + timedelta(days=int(lo) + int(row[21] * (int(hi) - int(lo) + 1)))
                refund = {"trigger": "customer complaint", "requested": complaint, "completed": done}
                pay.complaints.append({"complaint_ts": _ts(complaint), "kind": "charged twice", "amount_inr": amount,
                                       "bill_id": b["bill_id"], "rrn": d["rrn"], "resolved_ts": _ts(done),
                                       "resolution": "refunded after the store matched the credit by hand"})
            if refund:
                pay.refunds.append({"refund_id": f"RF-{d['rrn'][-6:]}", "rrn": d["rrn"], "bill_id": b["bill_id"],
                                    "amount_inr": amount, "trigger": refund["trigger"],
                                    "requested_ts": _ts(refund["requested"]), "completed_ts": _ts(refund["completed"])})
            pay.doubles.append({"bill_id": b["bill_id"], "rrn": d["rrn"], "amount_inr": amount,
                                "paid_ts": _ts(d["ts"]), "credited_ts": _ts(credited),
                                "refunded_ts": _ts(refund["completed"]) if refund else None,
                                "refunded_by_month_end": bool(refund and refund["completed"] <= end)})
    return pay


def _window(rows: list[dict], key: str, lo: str, hi: str) -> list[dict]:
    return [r for r in rows if lo <= r[key][:16] < hi]


def kpis(pay: Payments, bills: list[dict], lo: str, hi: str) -> dict:
    """Payment success for one period, measured four ways, plus what it cost customers."""
    att = _window(pay.attempts, "ts", lo, hi)
    upi = [a for a in att if a["tender"] == "UPI"]
    ids = {b["bill_id"] for b in bills if lo <= b["bill_ts"] < hi}
    approved_till = sum(a["till_status"].startswith("approved") for a in upi)
    credited = sum(a["final"] in ("success", "late credit") for a in upi)
    doubles = [d for d in pay.doubles if d["bill_id"] in ids]
    returned = [r for r in pay.returns if r["bill_id"] in ids]
    extra = {d["bill_id"] for d in doubles} | {r["bill_id"] for r in returned}
    n_bills = len(ids) or 1
    timeouts = sum(a["till_status"] in ("failed: no response", "pending at status check", "failed at status check",
                                        "approved after status check") for a in upi)
    return {
        "bills": len(ids), "upi_attempts": len(upi), "upi_timeouts": timeouts,
        "upi_business_declines": sum(a["final"] == "declined" for a in upi),
        "upi_technical_failures": sum(a["till_status"] == "failed" for a in upi),
        "four_ways": {
            "till": round(approved_till / max(1, len(upi)), 4),
            "bank": round(credited / max(1, len(upi)), 4),
            "bills_paid": 1.0,
            "charged_once": round(1 - len(extra) / n_bills, 4),
        },
        # A customer who retries during an outage can be charged three times; count customers and charges.
        "charged_twice": len({d["bill_id"] for d in doubles}), "extra_charges": len(doubles),
        "charged_twice_inr": round(sum(d["amount_inr"] for d in doubles), 2),
        "debited_and_returned": len({r["bill_id"] for r in returned}),
        "returned_within_t5": all(r["days"] <= 5 for r in returned),
        "second_payments": sum(1 for a in att if a["attempt"] > 1),
    }


def refunds_summary(pay: Payments) -> dict:
    days = sorted((datetime.fromisoformat(d["refunded_ts"]) - datetime.fromisoformat(d["paid_ts"])).total_seconds() / 86400
                  for d in pay.doubles if d["refunded_ts"])
    open_ = [d for d in pay.doubles if not d["refunded_by_month_end"]]
    return {
        "charged_twice": len({d["bill_id"] for d in pay.doubles}),
        "extra_charges": len(pay.doubles),
        "refunded": len(days),
        "median_days_to_refund": round(float(np.median(days)), 1) if days else None,
        "max_days_to_refund": round(days[-1], 1) if days else None,
        "unrefunded_at_month_end": len(open_),
        "unrefunded_inr": round(sum(d["amount_inr"] for d in open_), 2),
        "complaints": len(pay.complaints),
    }


def mdr(bills: list[dict], lo: str, hi: str) -> dict:
    """What the UPI merchant discount rate that started on 15 October 2026 would have cost on these bills."""
    rule = param("upi_mdr")
    above = [b for b in bills if lo <= b["bill_ts"] < hi and b["tender"] == "UPI" and b["amount_inr"] > rule["above"]]  # type: ignore[index]
    fee = sum(min(rule["cap"], b["amount_inr"] * rule["rate"]) for b in above)  # type: ignore[index]
    upi = [b for b in bills if lo <= b["bill_ts"] < hi and b["tender"] == "UPI"]
    return {"rule": rule, "upi_bills": len(upi), "upi_value_inr": round(sum(b["amount_inr"] for b in upi), 2),
            "bills_above": len(above), "value_above_inr": round(sum(b["amount_inr"] for b in above), 2),
            "fee_inr": round(fee, 2)}


def settlements(pay: Payments) -> list[dict]:
    """The acquirer's daily UPI settlement: credits confirmed on day D are paid out on D+1."""
    by_day: dict[str, dict] = {}
    for a in pay.attempts:
        if a["tender"] != "UPI" or a["final"] not in ("success", "late credit"):
            continue
        d = (datetime.fromisoformat(a["resolved_ts"]).date() + timedelta(days=1)).isoformat()
        r = by_day.setdefault(d, {"settlement_date": d, "upi_credits": 0, "gross_inr": 0.0, "refunds_inr": 0.0})
        r["upi_credits"] += 1
        r["gross_inr"] += a["amount_inr"]
    for f in pay.refunds:
        d = (datetime.fromisoformat(f["completed_ts"]).date() + timedelta(days=1)).isoformat()
        r = by_day.setdefault(d, {"settlement_date": d, "upi_credits": 0, "gross_inr": 0.0, "refunds_inr": 0.0})
        r["refunds_inr"] += f["amount_inr"]
    out = []
    for d in sorted(by_day):
        r = by_day[d]
        out.append({**r, "gross_inr": round(r["gross_inr"], 2), "refunds_inr": round(r["refunds_inr"], 2),
                    "mdr_inr": 0.0, "net_inr": round(r["gross_inr"] - r["refunds_inr"], 2)})
    return out


def till_minutes(pay: Payments, lo: str, hi: str) -> float:
    """Minutes the tills spent taking payment for bills that started in a period."""
    return round(sum(v for k, v in pay.bill_seconds.items()
                     if lo <= next(a["ts"] for a in pay.attempts if a["bill_id"] == k)[:16] < hi) / 60, 1)
