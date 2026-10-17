"""Small statistical helpers shared by the world builder (answer keys) and the agents (live answers)."""
from __future__ import annotations


def km_median(runs: list[tuple[int, bool]]) -> float | None:
    """Kaplan-Meier median of run life. runs: (days, failed). Strings still running are censored, not dropped.

    S(t) steps down at each failure by (n-1)/n, n being the number still at risk. The median is the first time
    S(t) <= 0.5; when S lands exactly on 0.5 the midpoint to the next failure is used (as in R's survfit summary).
    """
    ev = sorted(runs, key=lambda r: (r[0], -int(r[1])))
    n, s = len(ev), 1.0
    for i, (t, failed) in enumerate(ev):
        if failed:
            s *= (n - 1) / n
            if abs(s - 0.5) < 1e-9:
                nxt = next((e for e in ev[i + 1:] if e[1]), None)
                return (t + nxt[0]) / 2 if nxt else float(t)
            if s < 0.5:
                return float(t)
        n -= 1
    return None
