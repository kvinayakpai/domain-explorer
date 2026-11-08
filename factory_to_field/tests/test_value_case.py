"""The value-case report must keep measured and assumed numbers apart and honour overridden assumptions."""
from factory_to_field.eval.value import load_assumptions, report


def _row(seed):
    ok = {"correct": True, "seconds": 0.5, "tool_calls": 44, "drafts": 3, "citations_verify": True,
          "constraints_surfaced": ["open_work_on_position", "bearing_stock", "next_window", "spare_unit"], "false_alarm_called": False, "machinery_action": True}
    fa = dict(ok, drafts=1, false_alarm_called=True, machinery_action=False, constraints_surfaced=[])
    return {"seed": seed, "real_alarm": ok, "false_alarm": fa}


def test_report_separates_measured_from_assumed_and_uses_overrides(tmp_path):
    p = tmp_path / "mine.yaml"
    p.write_text("vibration_alarms_per_month: 10\nloaded_cost_per_hour: 100\n")
    A = load_assumptions(p)
    txt = report([_row(1), _row(2)], A)
    assert "## Measured" in txt and "## Assumed (NOT measured" in txt
    assert "vibration_alarms_per_month: 10" in txt and "At 10 alarms a month" in txt and "$100/hour" in txt
    assert "2 of 2" in txt
