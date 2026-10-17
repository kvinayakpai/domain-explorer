from __future__ import annotations

import sqlite3

from factory_to_field.world import realism


def test_realism_checks(world, world_dir):
    res = realism.checks(world, world_dir)
    failed = [r for r in res if not r[1]]
    assert not failed, "\n" + realism.report(res)


def test_story_numbers_match_the_demo(key):
    c1, c2, oem = key["CASE-1042"], key["CASE-2077"], key["OEM"]
    assert c1["current_unit"] == "OEM-25-1187" and c1["current_unit_since"] == "2026-03-10"
    assert len(c1["fleet"]) == 6
    assert c2["current_string_days"] == 276
    assert c2["km_median_new"] == 290 and c2["km_median_old"] == 780
    assert (c2["strings_new"], c2["strings_new_failed"], c2["strings_new_running"]) == (12, 7, 5)
    assert (oem["lot_pumps"], oem["lot_pump_customers"]) == (38, 9)
    assert (oem["lot_sections"], oem["lot_section_operators"]) == (61, 4)
    assert oem["also_waived"] == ["ECO-25-0112", "ECO-26-0057"]


def test_alarm_events_are_in_the_historians(world_dir):
    con = sqlite3.connect(world_dir / "historian_pi.sqlite")
    ts, = con.execute("SELECT a.ts FROM alarms a JOIN tags t USING(tag_id) WHERE t.name='10P101A.VIB_DE' ORDER BY a.ts DESC LIMIT 1").fetchone()
    assert ts.startswith("2026-10-16 07:0")  # 02:0x local, minutes before the case opened
    con = sqlite3.connect(world_dir / "scada_fielda.sqlite")
    ts, = con.execute("SELECT a.ts FROM alarms a JOIN tags t USING(tag_id) WHERE t.name='A07_MTR_T' ORDER BY a.ts DESC LIMIT 1").fetchone()
    assert ts.startswith("2026-10-17 04:3")


def test_p101_trend_matches_story(world_dir):
    con = sqlite3.connect(world_dir / "historian_pi.sqlite")
    rows = con.execute("SELECT d.max FROM daily d JOIN tags t USING(tag_id) WHERE t.name='10P101A.VIB_DE' AND d.day BETWEEN '2026-10-03' AND '2026-10-16' ORDER BY d.day").fetchall()
    assert [round(r[0], 1) for r in rows] == [2.0, 2.1, 2.1, 2.0, 2.2, 2.3, 2.5, 2.8, 3.1, 3.4, 3.7, 4.0, 4.3, 4.6]


def test_deterministic(tmp_path):
    from factory_to_field.world.build import build
    build(tmp_path / "a")
    build(tmp_path / "b")
    for name in ("truth.json", "answer_key.json"):
        assert (tmp_path / "a" / name).read_bytes() == (tmp_path / "b" / name).read_bytes()
