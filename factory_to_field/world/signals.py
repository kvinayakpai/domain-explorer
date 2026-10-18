"""Time series for the historians: daily aggregates for every tag, 5-minute raw windows for the stories,
vibration spectra, drive diagnostics and production allocation. Physics-flavoured, not Gaussian noise."""
from __future__ import annotations

from datetime import UTC, date, datetime, timedelta

import numpy as np

from .model import World, days
from .spec import HIST_START, NOW, TODAY

N = days(HIST_START, TODAY) + 1
DATES = [HIST_START + timedelta(d) for d in range(N)]
IDX = {d: i for i, d in enumerate(DATES)}
ALARM_DAY = date(2026, 10, 16)

P101A_VIB = [2.0, 2.1, 2.1, 2.0, 2.2, 2.3, 2.5, 2.8, 3.1, 3.4, 3.7, 4.0, 4.3, 4.6]  # 3 .. 16 Oct (daily max)
P101A_SUCTION = [3.3, 3.2, 3.3, 3.3, 3.2, 3.3, 3.2, 3.3, 3.3, 3.2, 3.3, 3.2, 3.3, 3.2]
A07_MTR = [117, 118, 118, 117, 119, 120, 122, 124, 126, 128, 130, 132, 134, 136]  # 4 .. 17 Oct (daily max)
A07_PIP = [62.1, 62.0, 62.2, 61.9, 62.0, 62.1, 61.8, 62.0, 62.1, 61.9, 62.0, 62.2, 61.9, 62.0]


def _day(d: date) -> int:
    return IDX[d]


def _ramp(i0: int, i1: int, power: float = 2.0) -> np.ndarray:
    """0 before i0, rising to 1 at i1, 1 after."""
    s = np.clip((np.arange(N) - i0) / max(i1 - i0, 1), 0, 1)
    return s ** power


def _agg(mean: np.ndarray, spread: float, rng, floor: float = 0.0) -> dict[str, np.ndarray]:
    mx = mean * (1 + spread * (1 + 0.5 * rng.random(N)))
    mn = np.maximum(mean * (1 - spread * (1 + 0.5 * rng.random(N))), floor)
    n = np.full(N, 288)
    n[-1] = 72  # 17 Oct is a partial day
    return {"mean": mean, "min": mn, "max": mx, "n": n}


def _pair_duty(w: World, pairs: dict[tuple, tuple[str, str]]) -> dict[str, np.ndarray]:
    rng = w.rng
    run: dict[str, np.ndarray] = {}
    for key, (a, b) in pairs.items():
        duty = np.zeros(N, dtype=int)  # 0: A runs, 1: B runs
        t = int(rng.integers(20, 80))
        while t < N:
            L = int(rng.integers(7, 17))
            duty[t:t + L] = 1
            t += L + int(rng.integers(50, 90))
        if key == ("R1", 101):
            duty[_day(date(2026, 1, 1)):] = 0
            for s, e in ((date(2026, 3, 8), date(2026, 3, 11)), (date(2026, 6, 10), date(2026, 6, 24)), (date(2026, 9, 8), date(2026, 9, 22))):
                duty[_day(s):_day(e)] = 1
        ra, rb = duty == 0, duty == 1
        for fe in w.failures:
            if fe["pos"] in (a, b) and fe["on"] >= HIST_START:
                i = _day(fe["on"])
                out = 2 if fe["swapped"] else fe["repair_days"]
                if fe["pos"] == a:
                    ra[i:i + out] = False
                    rb[i:i + out] = True
                else:
                    rb[i:i + out] = False
                    ra[i:i + out] = True
        run[a], run[b] = ra, rb
    return run


def _unit_days(w: World, pos: str) -> list[str | None]:
    out: list[str | None] = [None] * N
    for inst in w.installs_at(pos):
        i0 = max(0, days(HIST_START, inst["from"]))
        i1 = N if inst["to"] is None else min(N, days(HIST_START, inst["to"]))
        for i in range(i0, max(i0, i1)):
            out[i] = inst["unit"]
    return out


def _health(w: World, unit: str | None, i: int) -> tuple[float, str]:
    """Vibration multiplier and defect kind for a unit on day index i."""
    if unit is None:
        return 1.0, "none"
    for ep in w.units[unit].get("episodes", []):
        i0 = days(HIST_START, ep["onset"])
        if ep["fail"] is not None:
            i1 = days(HIST_START, ep["fail"])
            if i0 <= i <= i1:
                s = (i - i0) / max(i1 - i0, 1)
                if ep["kind"] == "bpfo":
                    return 1 + 2.2 * s ** 2.5, "bpfo"
                return 1 + 1.8 * s ** 2, "generic"
        else:
            if i >= i0:
                if ep["kind"] == "bpfo_mild":
                    return 1 + min(0.25, 0.0015 * (i - i0)), "bpfo_mild"
                if ep["kind"] == "bpfo_alarm":
                    return 1.0, "bpfo_alarm"
    return 1.0, "none"


def refinery_series(w: World) -> None:
    rng = w.rng
    season = np.sin(2 * np.pi * (np.arange(N) - 30) / 365.0)
    ar = np.zeros(N)
    eps = rng.normal(0, 0.02, N)
    for k in range(1, N):
        ar[k] = 0.95 * ar[k - 1] + eps[k]  # slow process drift, so consecutive days resemble each other
    load = 1 + 0.03 * season + 0.015 * np.sin(2 * np.pi * np.arange(N) / 7.0) + ar
    amb = 22 + 10 * season
    pairs: dict[tuple, tuple[str, str]] = {}
    for pid, pos in w.positions.items():
        if pos["kind"] == "pump" and pos["letter"] == "A":
            sid = pos["site"].split(":")[1]
            pairs[(sid, pos["svc_no"])] = (pid, pid[:-1] + "B")
    run = _pair_duty(w, pairs)
    unit_off: dict[str, float] = {}
    for pid, pos in w.positions.items():
        if pos["kind"] != "pump":
            continue
        sid = pos["site"].split(":")[1]
        base = float(np.clip(rng.lognormal(np.log(2.0), 0.22), 1.2, 3.0))
        units = _unit_days(w, pid)
        vde = np.zeros(N)
        kinds = ["none"] * N
        for i in range(N):
            u = units[i]
            if u is not None and u not in unit_off:
                unit_off[u] = float(rng.normal(1.0, 0.07))
            hm, kd = _health(w, u, i)
            kinds[i] = kd
            if run[pid][i] and u is not None:
                vde[i] = base * unit_off.get(u, 1.0) * hm * load[i] * float(np.exp(rng.normal(0, 0.035)))
            else:
                vde[i] = 0.06 + 0.03 * float(rng.random())
        vnde = vde * 0.72 + rng.normal(0, 0.02, N)
        brg = np.where(run[pid], amb + 28 + 2.4 * vde, amb + 2) + rng.normal(0, 0.6, N)
        runv = run[pid].astype(float)
        suc = np.where(run[pid], 3.3 + rng.normal(0, 0.03, N), 3.6 + rng.normal(0, 0.02, N))
        is_a = pos["letter"] == "A"
        # planted last fortnight: the numbers the story depends on
        if pid == "pos:R1:10-P-101A":
            i0 = _day(date(2026, 10, 3))
            for k, v in enumerate(P101A_VIB):
                vde[i0 + k] = v / 1.045
                suc[i0 + k] = P101A_SUCTION[k]
            vde[-1] = 4.62 / 1.045
            vnde[i0:] = vde[i0:] * 0.7
            brg[i0:] = amb[i0:] + 28 + 2.4 * vde[i0:] - 2
        sigs = {s["quantity"]: sid_ for sid_, s in w.signals.items() if s["pos"] == pid and s["quantity"] in
                ("vibration_de", "vibration_nde", "bearing_temp", "run_status")}
        w.daily[sigs["vibration_de"]] = _agg(vde, 0.045, rng, 0.04)
        if pid == "pos:R1:10-P-101A":
            mxv = w.daily[sigs["vibration_de"]]["max"]
            mxv[_day(date(2026, 10, 3)):_day(date(2026, 10, 3)) + 14] = P101A_VIB
            mxv[-1] = 4.66
        w.daily[sigs["vibration_nde"]] = _agg(np.maximum(vnde, 0.04), 0.05, rng, 0.03)
        w.daily[sigs["bearing_temp"]] = _agg(brg, 0.02, rng, 0)
        w.daily[sigs["run_status"]] = {"mean": runv, "min": runv, "max": runv, "n": np.full(N, 288)}
        w.answer.setdefault("_kinds", {})[pid] = kinds
        if is_a:
            sp = next(s for s, v in w.signals.items() if v["quantity"] == "suction_pressure" and v["pos"] == pid)
            w.daily[sp] = _agg(suc, 0.004, rng, 0)
    # a stuck sensor: R3 50-P-503A drive-end vibration flat-lines at 4.7 mm/s for nine days
    sig = next(s for s, v in w.signals.items() if v["tag"] == "50P503A.VIB_DE")
    d = w.daily[sig]
    i0 = N - 9
    for k in ("mean", "min", "max"):
        d[k][i0:] = 4.70
    w.answer["flatline"] = {"signal": sig, "since": DATES[i0], "value": 4.70}
    w.answer.setdefault("_runs", run)


def esp_series(w: World) -> None:
    rng = w.rng
    for wl in [p for p in w.positions.values() if p["kind"] == "well"]:
        name = wl["tag"]
        esp = wl["lift"] == "esp"
        stub = name.replace("-", "")
        if not esp:
            thp = 14 + rng.normal(0, 0.4, N)
            w.daily[f"sig:FA:{stub}_THP"] = _agg(thp, 0.01, rng)
            w.daily[f"sig:FA:{stub}_GL_FLOW"] = _agg(np.full(N, 250.0) + rng.normal(0, 6, N), 0.03, rng)
            oil = 180 * np.exp(-np.arange(N) / 4000) + rng.normal(0, 3, N)
            w.daily[f"prod:{name}"] = {"oil": np.maximum(oil, 0)}
            continue
        pid = f"pos:FA:{name}-ESP"
        units = _unit_days(w, pid)
        hz0 = 58.0 if name == "A-07" else float(rng.integers(50, 60))
        mt0 = 117.0 if name == "A-07" else float(rng.normal(112, 5))
        pip0 = 62.0 if name == "A-07" else float(rng.normal(60, 12))
        amps0 = float(rng.normal(46, 6))
        q0 = 640.0 if name == "A-07" else float(rng.normal(520, 130))
        mt = np.full(N, np.nan); pip = np.full(N, np.nan); amps = np.full(N, np.nan); hz = np.full(N, np.nan)
        leak = np.full(N, np.nan); flow = np.full(N, np.nan); oil = np.zeros(N)
        for i in range(N):
            u = units[i]
            if u is None:
                continue
            ep = next((e for e in w.units[u].get("episodes", []) if (e["fail"] is None or days(HIST_START, e["onset"]) <= i <= days(HIST_START, e["fail"])) and days(HIST_START, e["onset"]) <= i), None)
            s = 0.0
            if ep and ep["fail"] is not None:
                s = (i - days(HIST_START, ep["onset"])) / max(days(HIST_START, ep["fail"]) - days(HIST_START, ep["onset"]), 1)
            elif ep and ep["kind"] in ("ingress_now", "ingress_slow"):
                s = min(0.25, (i - days(HIST_START, ep["onset"])) / 400.0)
            ing = ep is not None and ep["kind"].startswith("ingress")
            mt[i] = mt0 + (hz0 - 50) * 0.0 + (22 * s ** 1.5 if ing else 3 * s) + rng.normal(0, 0.5)
            pip[i] = pip0 + rng.normal(0, 0.25)
            amps[i] = amps0 * (1 - 0.06 * s) + rng.normal(0, 0.4)
            hz[i] = hz0 + (0.0 if name != "A-07" else 0.0)
            leak[i] = 0.2 + (5.5 * np.exp(3.2 * (s - 1)) if ing else 0.0) + abs(rng.normal(0, 0.05))
            flow[i] = q0 / 0.65 * (1 - 0.04 * s) * (1 + rng.normal(0, 0.012))
            oil[i] = q0 * (1 - 0.00012 * i) * (1 - 0.04 * s) * (1 + rng.normal(0, 0.012))
        if name == "A-07":
            i0 = _day(date(2026, 10, 4))
            for k, v in enumerate(A07_MTR):
                mt[i0 + k] = v - 1.2
                pip[i0 + k] = A07_PIP[k]
            leak[_day(date(2026, 10, 10)):] = np.array([0.8, 1.4, 1.9, 2.5, 3.0, 3.4, 3.7, 3.9][:N - _day(date(2026, 10, 10))])[:N - _day(date(2026, 10, 10))]
            oil[-30:] = 640 * (1 + rng.normal(0, 0.008, 30))
        stub_sigs = {k: f"sig:FA:{stub}_{k}" for k in ("MTR_T", "PIP", "AMPS", "VSD_HZ", "LEAK_I", "FLOW")}
        w.daily[stub_sigs["MTR_T"]] = _agg(mt, 0.0085, rng)
        w.daily[stub_sigs["PIP"]] = _agg(pip, 0.003, rng)
        w.daily[stub_sigs["AMPS"]] = _agg(amps, 0.02, rng)
        w.daily[stub_sigs["VSD_HZ"]] = _agg(hz, 0.0, rng)
        w.daily[stub_sigs["LEAK_I"]] = _agg(leak, 0.05, rng)
        w.daily[stub_sigs["FLOW"]] = _agg(flow, 0.02, rng)
        w.daily[f"prod:{name}"] = {"oil": oil}
    # pin the maxima that the story quotes
    i0 = _day(date(2026, 10, 4))
    mx = w.daily["sig:FA:A07_MTR_T"]["max"]
    mx[i0:i0 + 14] = A07_MTR
    mxp = w.daily["sig:FA:A07_PIP"]["max"]
    mxp[i0:i0 + 14] = np.maximum(mxp[i0:i0 + 14], A07_PIP)


def _lastday(keypts: list[tuple[float, float]], hours: float, rng, noise: float, cap_before: float | None = None) -> np.ndarray:
    """5-minute samples across the last day from piecewise-linear key points (hours, value)."""
    t = np.arange(0, hours * 60, 5) / 60.0
    xs, ys = zip(*keypts)
    v = np.interp(t, xs, ys) + rng.normal(0, noise, len(t))
    if cap_before is not None:
        v = np.where(t < keypts[1][0] - 0.05, np.minimum(v, cap_before), v)
    return v


def raw_windows(w: World) -> None:
    """5-minute samples for the stories (14 days; 30 days for the six-pump fleet)."""
    rng = w.rng
    end = NOW.replace(tzinfo=None)
    def span(nd: int) -> np.ndarray:
        n = nd * 288
        return np.array([end - timedelta(minutes=5 * (n - 1 - k)) for k in range(n)], dtype="datetime64[s]")
    # P-101A drive end vibration, 14 days; daily max pinned to the story
    span(14)
    def from_daily(sig: str, nd: int, spread: float = 0.045) -> np.ndarray:
        dd = w.daily[sig]
        out = []
        for k in range(nd):
            di = N - nd + k
            m = dd["mean"][di]
            cnt = 288 if di < N - 1 else 72
            tt = np.arange(cnt)
            val = m * (1 + spread * 0.5 * np.sin(2 * np.pi * (tt - 60) / 288) + rng.normal(0, spread * 0.25, cnt))
            val[int(rng.integers(0, cnt))] = dd["max"][di]
            val = np.minimum(val, dd["max"][di])
            out.append(val)
        return np.concatenate(out)
    for sig in [s for s, v in w.signals.items() if v["tag"] in
                ("10P101A.VIB_DE", "10P101A.VIB_NDE", "10P101A.BRG_T", "10P101A.RUN", "10P101B.VIB_DE", "10PI1003.PV")]:
        vals = from_daily(sig, 14)
        if w.signals[sig]["tag"] == "10P101A.VIB_DE":
            # the last two days: shape the approach to the alarm (crossing 4.5 at 07:10 UTC on 16 Oct)
            d15 = _lastday([(0, 4.12), (24, 4.30)], 24, rng, 0.012)
            d15 = np.minimum(d15, 4.3)
            d16 = _lastday([(0, 4.30), (7.0, 4.505), (12, 4.58), (24, 4.60)], 24, rng, 0.006)
            d16[:int(7.0 * 12)] = np.minimum(d16[:int(7.0 * 12)], 4.49)
            d16 = np.minimum(d16, 4.6)
            k0 = int(7.0 * 12)
            d16[k0:] = np.maximum(d16[k0:], 4.502)
            d16[int(15 * 12)] = 4.6
            d17 = _lastday([(0, 4.60), (6, 4.66)], 6, rng, 0.008)
            vals = np.concatenate([vals[:-(288 + 288 + 72)], d15, d16, d17])
        times = span(14)
        w.raw[sig] = (times[-len(vals):], vals)
    # the other five fleet pumps: 30 days of drive end vibration
    for tag in ("21P215A.VIB_DE", "21P215B.VIB_DE", "30P301A.VIB_DE", "30P301B.VIB_DE"):
        sig = next(s for s, v in w.signals.items() if v["tag"] == tag)
        vals = from_daily(sig, 30)
        w.raw[sig] = (span(30)[-len(vals):], vals)
    sig = "sig:R1:10P101A.VIB_DE"
    w.raw[sig + "~30"] = (span(30)[-30 * 288 + 0:][:0], np.array([]))
    del w.raw[sig + "~30"]
    # A-07 (14 days): motor temperature, intake pressure, current, frequency, leakage
    for k in ("MTR_T", "PIP", "AMPS", "VSD_HZ", "LEAK_I"):
        sig = f"sig:FA:A07_{k}"
        vals = from_daily(sig, 14, 0.004 if k != "LEAK_I" else 0.05)
        if k == "MTR_T":
            d16 = from_daily(sig, 14, 0.004)[-(72 + 288):-72]
            d17 = _lastday([(0, 134.3), (4.5, 135.05), (6, 136.0)], 6, rng, 0.04, cap_before=134.99)
            k0 = int(4.5 * 12)
            d17[:k0] = np.minimum(d17[:k0], 134.99)
            d17[k0:] = np.maximum(d17[k0:], 135.02)
            d17[-1] = 136.0
            vals = np.concatenate([vals[:-72], d17])
        w.raw[sig] = (span(14)[-len(vals):], vals)
    sig = w.answer["flatline"]["signal"]
    w.raw[sig] = (span(9)[-9 * 288:], np.full(9 * 288, 4.70))


def sync_daily_with_raw(w: World) -> None:
    """Where a raw window exists, the daily aggregate is computed from it, so the two never disagree."""
    for sig, (ts, vals) in w.raw.items():
        if sig not in w.daily:
            continue
        days_ = ts.astype("datetime64[D]")
        for dd in np.unique(days_):
            m = days_ == dd
            di = days(HIST_START, date.fromisoformat(str(dd)))
            if 0 <= di < N and m.sum() >= 24:
                d = w.daily[sig]
                d["mean"][di], d["min"][di], d["max"][di], d["n"][di] = vals[m].mean(), vals[m].min(), vals[m].max(), int(m.sum())


def spectra(w: World) -> None:
    rng = w.rng
    kinds = w.answer["_kinds"]
    runs = w.answer["_runs"]
    pairs = [(pid, pos) for pid, pos in w.positions.items() if pos["kind"] == "pump"]
    for pid, pos in pairs:
        dm = w.daily[next(s for s, v in w.signals.items() if v["pos"] == pid and v["quantity"] == "vibration_de")]["mean"]
        sig = next(v["tag"] for v in w.signals.values() if v["pos"] == pid and v["quantity"] == "vibration_de")
        units = _unit_days(w, pid)
        d = date(2024, 1, 15)
        dates = []
        while d <= date(2026, 10, 15):
            dates.append(d)
            d = (d.replace(day=1) + timedelta(days=32)).replace(day=15)
        dates.append(date(2026, 10, 15))
        for d in dates:
            i = _day(d)
            if not runs[pid][i] or units[i] is None:
                continue
            base = dm[i]
            kd = kinds[pid][i]
            hm, _ = _health(w, units[i], i)
            peaks = {"1x": 0.42 * base, "2x": 0.16 * base, "bpfo": 0.045 * base, "bpfi": 0.04 * base, "bsf": 0.035 * base}
            if kd == "bpfo":
                peaks["bpfo"] = 0.5 * base * (hm - 0.8)
            elif kd == "bpfo_mild":
                peaks["bpfo"] = 0.35 * base
            elif kd == "bpfo_alarm":
                eps = next(e for e in w.units[units[i]]["episodes"] if e["kind"] == "bpfo_alarm")
                s = min(1.0, (i - days(HIST_START, eps["onset"])) / 26.0)
                peaks["bpfo"] = base * (0.25 + 0.8 * s ** 1.5)
            elif kd == "generic":
                peaks["1x"] *= hm
                peaks["2x"] *= 0.6 * hm
            row = {"tag": sig, "pos": pid, "unit": units[i], "on": d,
                   **{k: round(float(v * (1 + rng.normal(0, 0.05))), 3) for k, v in peaks.items()}, "overall": round(float(base), 3)}
            w.spectra.append(row)


def alarms(w: World) -> list[dict]:
    out = []
    for sig, v in w.signals.items():
        lim = v.get("alarm_high")
        if lim is None:
            continue
        if sig in w.raw:
            ts, vals = w.raw[sig]
            active = False
            edges = []
            for k, x in enumerate(vals):
                if not active and x >= lim:
                    active = True
                    edges.append(k)
                elif active and x < lim - 0.03 * lim:
                    active = False
            for k in edges:
                out.append({"sig": sig, "ts": ts[k].astype("datetime64[s]").astype(datetime).replace(tzinfo=UTC), "value": float(vals[k]), "limit": lim, "state": "ALM"})
        elif sig in w.daily:
            dd = w.daily[sig]["max"]
            for i in np.nonzero(dd >= lim)[0]:
                if i > 0 and dd[i - 1] >= lim:
                    continue
                ts = datetime.combine(DATES[i], datetime.min.time(), tzinfo=UTC) + timedelta(minutes=int(w.rng.integers(0, 1440)))
                if ts < NOW:
                    out.append({"sig": sig, "ts": ts, "value": float(dd[i]), "limit": lim, "state": "ALM"})
    return out


def drive_events(w: World) -> list[dict]:
    ev = []
    for wl in [p["tag"] for p in w.positions.values() if p["kind"] == "esp_position"]:
        base = wl.replace(" ESP", "")
        for k in range(int(w.rng.integers(2, 6))):
            ev.append({"well": base, "ts": datetime(2025, 1, 1, tzinfo=UTC) + timedelta(days=int(w.rng.integers(0, 640))),
                       "type": "undervoltage_ride_through", "value": None, "note": "grid dip, drive recovered"})
    for k, (dd, val) in enumerate(((10, 0.8), (12, 1.9), (14, 3.0), (16, 3.7))):
        ev.append({"well": "A-07", "ts": datetime(2026, 10, dd, 11, 20, tzinfo=UTC), "type": "ground_leakage_warning",
                   "value": val, "note": "leakage current to ground rising"})
    ev.append({"well": "A-07", "ts": datetime(2026, 10, 17, 4, 35, tzinfo=UTC), "type": "motor_temperature_high", "value": 135.1, "note": "alarm limit 135"})
    return ev


def generate(w: World) -> None:
    refinery_series(w)
    esp_series(w)
    raw_windows(w)
    sync_daily_with_raw(w)
    spectra(w)
