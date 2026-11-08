"""A deliberately naive agent: it answers from the current state of each record, the way a plain lookup or keyword search over
the CMMS would. It uses the same tools and the same graph as the real agent but none of its time logic.

It exists to put a number on what the as-of logic buys: it is a baseline I wrote, a strawman by construction, not a competing
product. It overrides only the question families where a current-state shortcut exists; every other family uses the real playbook.
"""
from __future__ import annotations

import re

from .agent import Agent


class NaiveAgent(Agent):
    def pb_as_of_unit(self, c, s, rep) -> None:
        pos = c.position
        on = re.search(r"as of (\d{4}-\d\d-\d\d)", c.question).group(1)
        r = s.call("kg.unit_at", position=pos)  # today's unit, whatever date was asked
        rep.answer.update(position=pos.split(":", 1)[1], date=on, unit=r.data["serial"])
        self._add(rep, "asset", f"{r.data['serial']} is installed at {pos.split(':', 2)[-1]}.", r.evidence)
        rep.summary = f"{r.data['serial']} is the unit at {pos.split(':', 2)[-1]}"

    def _month_failures(self, s, pos: str, prefix: str) -> int:
        cur = s.call("kg.unit_at", position=pos).data["unit"]
        if not cur:
            return 0
        tr = s.call("kg.unit_trace", unit=cur)
        return sum(1 for r in tr.data if r.get("fe") and r["on"].startswith(prefix))  # the equipment's failures, wherever they happened

    def pb_position_vs_unit(self, c, s, rep) -> None:
        import calendar
        mm = re.search(r"in ([A-Za-z]+) (\d{4})", c.question)
        month = list(calendar.month_name).index(mm.group(1).title())
        prefix = f"{mm.group(2)}-{month:02d}"
        sister = c.position[:-1] + ("A" if c.position.endswith("B") else "B")
        rep.answer.update(failures_in_month_at_position=self._month_failures(s, c.position, prefix), failures_in_month_at_sister=self._month_failures(s, sister, prefix))
        rep.summary = "Failures on the equipment now at that location"

    def pb_lot_suspicion(self, c, s, rep) -> None:
        well = re.search(r"\b([AB]-\d\d)\b", c.question).group(1)
        rl = s.call("kg.run_life", since_built="2025-08-01")
        cur = s.call("kg.unit_at", position=f"pos:FA:{well}-ESP")
        in_lot = any(m["well"].startswith(well) for m in rl.data["new_members"])  # the well has had a suspect-lot string at some point
        rep.answer.update(well=well, in_lot=in_lot, current_string=cur.data["serial"])
        rep.recommendation = "Include it in the containment list." if in_lot else "Do not attribute a problem to lot E-25-031."
        rep.summary = f"{well} is {'' if in_lot else 'not '}exposed"
