"""Operator side, upstream: Field A, twelve ESP wells (plus gas-lift wells), string runs, failures, DIFA reports."""
from __future__ import annotations

from datetime import date, timedelta

from .gen_factory import build_esp_string, new_lot
from .model import World, days
from .spec import (
    A07_NEW,
    A07_NEW_SEAL,
    A07_NEW_START,
    A07_OLD,
    A07_OLD_FAIL,
    A07_OLD_SEAL,
    A07_OLD_START,
    FIELD,
    LOT_ELASTOMER,
    NEW_FAILED,
    NEW_RUNNING,
    OLD_LIVES,
    OPERATOR,
    TODAY,
)

ESP_WELLS = [f"A-{i:02d}" for i in range(1, 13)]
GL_WELLS = [f"B-{i:02d}" for i in range(1, 11)]
PAD_OF = {w: f"P{(i // 3) + 1}" for i, w in enumerate(ESP_WELLS)}
PAD_OF.update({w: f"P{(i % 4) + 1}" for i, w in enumerate(GL_WELLS)})

OLD_FAIL_TEXT = [("BRD", "Motor burnout, scale on housing"), ("BRD", "Cable splice failure at 900 m"), ("OHE", "Motor overheating, sand cut"),
                 ("PDE", "Pump worn, loss of head"), ("BRD", "Thrust bearing failure"), ("BRD", "Shaft break at coupling"),
                 ("OHE", "Gas lock, motor overheated"), ("BRD", "Motor insulation breakdown")]


def _floc(well: str, esp: bool = False) -> str:
    return f"FA-{PAD_OF[well]}-{well.replace('-', '')}" + ("-ESP" if esp else "")


def generate(w: World) -> None:
    rng = w.rng
    site, name, tz = FIELD
    w.sites["site:FA"] = {"id": "site:FA", "name": name, "kind": "field", "tz": tz, "operator": OPERATOR}
    new_lot(w, "E-23-207", "elastomer compound", "org:veyron", date(2023, 10, 2), 120)
    for wl in ESP_WELLS + GL_WELLS:
        esp = wl in ESP_WELLS
        wid = f"pos:FA:{wl}"
        w.positions[wid] = {"id": wid, "tag": wl, "floc": _floc(wl), "site": "site:FA", "kind": "well", "pad": PAD_OF[wl],
                            "lift": "esp" if esp else "gas_lift", "service": "Producing well", "area": PAD_OF[wl]}
        if esp:
            pid = f"pos:FA:{wl}-ESP"
            w.positions[pid] = {"id": pid, "tag": f"{wl} ESP", "floc": _floc(wl, True), "site": "site:FA", "kind": "esp_position",
                                "pad": PAD_OF[wl], "parent": wid, "service": "lift", "area": PAD_OF[wl],
                                "setting_depth_m": 1850.0 if wl == "A-07" else float(rng.integers(1500, 2200))}
        tags = ["MTR_T", "PIP", "AMPS", "VSD_HZ", "LEAK_I", "FLOW"] if esp else ["THP", "GL_FLOW"]
        qty = {"MTR_T": ("motor_temperature", "degC"), "PIP": ("intake_pressure", "bar"), "AMPS": ("motor_current", "A"),
               "VSD_HZ": ("drive_frequency", "Hz"), "LEAK_I": ("leakage_current", "mA"), "FLOW": ("flow", "bbl/d"),
               "THP": ("tubing_head_pressure", "bar"), "GL_FLOW": ("gas_lift_rate", "Mscf/d")}
        for t in tags:
            sig = f"sig:FA:{wl.replace('-', '')}_{t}"
            w.signals[sig] = {"id": sig, "tag": f"{wl.replace('-', '')}_{t}", "site": "site:FA", "pos": f"pos:FA:{wl}-ESP" if esp else wid,
                              "quantity": qty[t][0], "eng_unit": qty[t][1], "alarm_high": 135.0 if t == "MTR_T" else None,
                              "desc": f"{wl} {qty[t][0].replace('_', ' ')}", "system": "SCADA", "sample_s": 300}
    # --- plan the 12 new-seal runs -------------------------------------------------------------------
    others = [x for x in ESP_WELLS if x != "A-07"]
    run_lives = [l for l in NEW_RUNNING if l != 276]
    rng.shuffle(others)
    plan: dict[str, dict] = {"A-07": {"life": 276, "failed": False, "install": A07_NEW_START}}
    for wl, life in zip(others[:4], run_lives):
        plan[wl] = {"life": life, "failed": False, "install": TODAY - timedelta(days=life)}
    for wl, life in zip(others[4:], NEW_FAILED):
        hi = date(2026, 9, 30) - timedelta(days=life)
        lo = date(2025, 9, 1)
        inst = lo + timedelta(days=int(rng.integers(0, (hi - lo).days + 1)))
        plan[wl] = {"life": life, "failed": True, "install": inst}
    # --- old runs: 18 lives, A-07's last is 688 ----------------------------------------------------------
    rest = [l for l in OLD_LIVES if l != 688]
    rng.shuffle(rest)
    two_run = ["A-07"] + [x for x in others if x in others[:5]][:5]
    old_runs: dict[str, list[int]] = {}
    pos_i = 0
    for wl in ESP_WELLS:
        if wl == "A-07":
            old_runs[wl] = [rest[pos_i], 688]
            pos_i += 1
        elif wl in two_run:
            old_runs[wl] = [rest[pos_i], rest[pos_i + 1]]
            pos_i += 2
        else:
            old_runs[wl] = [rest[pos_i]]
            pos_i += 1
    assert pos_i == len(rest), (pos_i, len(rest))
    # --- build strings and installations -----------------------------------------------------------------
    for wl in ESP_WELLS:
        pid = f"pos:FA:{wl}-ESP"
        pl = plan[wl]
        chain: list[dict] = []
        # old runs, working backwards from the new install
        end = A07_OLD_FAIL if wl == "A-07" else pl["install"] - timedelta(days=int(rng.integers(3, 16)))
        for life in reversed(old_runs[wl]):
            start = A07_OLD_START if (wl == "A-07" and life == 688) else end - timedelta(days=life)
            chain.insert(0, {"start": start, "end": end, "life": life, "old": True})
            end = start - timedelta(days=int(rng.integers(4, 20)))
        chain.append({"start": pl["install"], "end": pl["install"] + timedelta(days=pl["life"]) if pl["failed"] else None,
                      "life": pl["life"], "old": False})
        if pl["failed"]:
            rig = int(rng.integers(8, 31))
            re_inst = chain[-1]["end"] + timedelta(days=rig)
            if re_inst <= TODAY - timedelta(days=3):
                chain.append({"start": re_inst, "end": None, "life": days(re_inst, TODAY), "old": True, "stock": True})
        for k, run in enumerate(chain):
            if wl == "A-07" and run["old"] and run["life"] == 688:
                sser, kser = build_esp_string(w, A07_OLD, run["start"] - timedelta(days=96), "cust:aurelia", elastomer_lot="E-23-207",
                                              seal_serial=A07_OLD_SEAL, shipped=run["start"] - timedelta(days=60))
            elif wl == "A-07" and not run["old"]:
                sser, kser = build_esp_string(w, A07_NEW, date(2025, 10, 14), "cust:aurelia", elastomer_lot=LOT_ELASTOMER,
                                              seal_serial=A07_NEW_SEAL, shipped=date(2025, 11, 20))
            elif not run["old"]:
                built = max(date(2025, 8, 12), run["start"] - timedelta(days=int(rng.integers(25, 70))))
                sser, kser = build_esp_string(w, None, built, "cust:aurelia", elastomer_lot=LOT_ELASTOMER,
                                              shipped=min(built + timedelta(days=int(rng.integers(8, 20))), run["start"] - timedelta(days=3)))
            elif run.get("stock"):
                built = date(2025, 3, 1) + timedelta(days=int(rng.integers(0, 140)))
                sser, kser = build_esp_string(w, None, built, "cust:aurelia", shipped=built + timedelta(days=21))
            else:
                built = run["start"] - timedelta(days=int(rng.integers(60, 150)))
                sser, kser = build_esp_string(w, None, built, "cust:aurelia", shipped=built + timedelta(days=int(rng.integers(14, 35))))
            u = f"unit:{sser}"
            run["unit"] = u
            run["seal"] = f"unit:{kser}"
            inst = {"id": w.nid("inst:"), "pos": pid, "unit": u, "from": run["start"], "to": run["end"]}
            w.installs.append(inst)
            ended = run["end"] is not None
            end_state = "failed" if ended else "running"
            new_seal = (not run["old"])
            w.runs.append({"id": w.nid("run:"), "well": wl, "unit": u, "start": run["start"], "end": run["end"], "state": end_state,
                           "days": ((run["end"] or TODAY) - run["start"]).days, "new_seal": new_seal,
                           "pull_reason": ("motor failure" if ended else None)})
            if ended:
                if new_seal:
                    mode, desc = "BRD", "Motor failure, well fluid in motor oil"
                else:
                    mode, desc = OLD_FAIL_TEXT[int(rng.integers(0, len(OLD_FAIL_TEXT)))]
                if wl == "A-07" and run["life"] == 688:
                    mode, desc = "BRD", "Motor failure"
                fe = {"id": w.nid("fe:"), "unit": u, "pos": pid, "inst": inst["id"], "on": run["end"], "mode": mode, "desc": desc,
                      "planted": new_seal, "repair_days": 0, "swapped": True}
                w.failures.append(fe)
                ep = {"onset": run["end"] - timedelta(days=int(rng.integers(25, 55) if new_seal else rng.integers(5, 20))),
                      "fail": run["end"], "kind": "ingress" if new_seal else "generic"}
                w.units[u]["episodes"] = [ep]
            elif new_seal:
                kind = "ingress_now" if wl == "A-07" else "ingress_slow"
                w.units[u]["episodes"] = [{"onset": date(2026, 8, 14) if wl == "A-07" else TODAY - timedelta(days=60),
                                           "fail": None, "kind": kind}]
        pl["chain"] = chain
    # a spare string in the field store (old stock, good seal)
    sser, kser = build_esp_string(w, None, date(2025, 6, 10), "cust:aurelia", shipped=date(2025, 7, 1))
    w.stock.append({"site": "site:FA", "store": "FA field store", "material": f"ESP string {sser}", "desc": "ESP string KE-ESP-540", "qty": 1, "lead_days": 0})
    w.answer["field_spare_string"] = sser
    # DIFA reports: five of the seven failed new-seal strings; some of the old failures
    failed_new = [r for r in w.runs if r["new_seal"] and r["state"] == "failed"]
    for r in failed_new[:5]:
        w.difa.append({"id": w.nid("difa:"), "unit": r["unit"], "well": r["well"], "on": r["end"] + timedelta(days=int(rng.integers(12, 35))),
                       "standard": "API RP 11S1", "finding": "Seal section elastomers swollen and cracked; well fluid found in motor oil; no mechanical damage to pump stages."})
    failed_old = [r for r in w.runs if (not r["new_seal"]) and r["state"] == "failed"]
    for r in failed_old[:9]:
        txt = str(rng.choice(["Cable insulation breakdown at splice; motor oil clean.", "Scale deposits on pump stages; motor winding burnt from overload.",
                              "Thrust washer worn through; seal section intact, elastomers serviceable.", "Sand erosion of stages 14 to 22; seal section intact."]))
        w.difa.append({"id": w.nid("difa:"), "unit": r["unit"], "well": r["well"], "on": r["end"] + timedelta(days=int(rng.integers(12, 35))),
                       "standard": "API RP 11S1", "finding": txt})
    # documents
    for wl in ESP_WELLS:
        a07 = wl == "A-07"
        w.documents.append({"no": f"CS-{wl.replace('-', '')}", "kind": "completion schematic", "rev": "4" if a07 else str(rng.integers(1, 6)),
                            "site": "site:FA", "title": f"Completion schematic {wl}, ESP at {w.positions[f'pos:FA:{wl}-ESP']['setting_depth_m']:.0f} m, motor design limit 150 degC",
                            "applies": [wl], "rated_m3h": None, "design_limit_motor_c": 150.0})
        w.documents.append({"no": f"FL-{wl.replace('-', '')}", "kind": "fluid analysis", "rev": "1", "site": "site:FA",
                            "title": f"Produced fluid analysis {wl}: CO2 {'3.2' if a07 else '1.1'} mol%, H2S {'12' if a07 else '2'} ppm",
                            "applies": [wl], "rated_m3h": None})
    # rigs and windows
    w.rigs += [{"site": "site:FA", "rig": "Rig 1", "free_from": date(2026, 11, 5), "note": "on well B-04 recompletion"},
               {"site": "site:FA", "rig": "Rig 2", "free_from": date(2026, 10, 24), "note": "free from 24 Oct"}]
    # notifications and orders for the string failures
    for fe in [f for f in w.failures if f["pos"].startswith("pos:FA")]:
        wl = fe["pos"].split(":")[-1].replace("-ESP", "")
        n = {"id": w.nid("nt:"), "type": "M2", "on": fe["on"], "pos": fe["pos"], "unit": fe["unit"], "text": f"{wl} ESP down - {fe['desc'].lower()}",
             "mode": fe["mode"], "fail": fe["id"], "prio": 1, "status": "closed", "long": ""}
        w.notifications.append(n)
        w.workorders.append({"id": w.nid("wo:"), "type": "PM02", "start": fe["on"] + timedelta(days=8), "end": fe["on"] + timedelta(days=14),
                             "pos": fe["pos"], "unit": fe["unit"], "text": f"Workover {wl} - pull and replace ESP string", "notif": n["id"]})
    w.answer["field_plan"] = {wl: {k: v for k, v in pl.items() if k != "chain"} for wl, pl in plan.items()}
