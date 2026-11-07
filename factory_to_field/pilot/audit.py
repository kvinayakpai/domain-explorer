"""Tamper-evident audit log: every approval, release, refusal and review decision, hash-chained.

Each record carries the SHA-256 of the previous record, so editing or deleting a line breaks the chain
from that point and `verify()` reports where. Records are JSON lines on disk (default
factory_to_field/build/audit/audit.jsonl) and survive restarts of the console.
"""
from __future__ import annotations

import hashlib
import json
import threading
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

GENESIS = "0" * 64
DEFAULT_PATH = Path(__file__).resolve().parents[1] / "build" / "audit" / "audit.jsonl"


def _digest(rec: dict[str, Any]) -> str:
    body = {k: v for k, v in rec.items() if k != "hash"}
    return hashlib.sha256(json.dumps(body, sort_keys=True, default=str).encode()).hexdigest()


class AuditLog:
    def __init__(self, path: Path | None = DEFAULT_PATH) -> None:
        """`path=None` keeps the log in memory (tests)."""
        self.path = path
        self._lock = threading.Lock()
        self._records: list[dict[str, Any]] = []
        if path is not None:
            path.parent.mkdir(parents=True, exist_ok=True)
            if path.exists():
                self._records = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]

    def append(self, actor: str, role: str | None, action: str, obj: str, detail: dict[str, Any] | None = None) -> dict[str, Any]:
        with self._lock:
            prev = self._records[-1]["hash"] if self._records else GENESIS
            rec: dict[str, Any] = {
                "seq": len(self._records) + 1,
                "at": datetime.now(UTC).isoformat(timespec="seconds"),
                "actor": actor,
                "role": role,
                "action": action,
                "object": obj,
                "detail": detail or {},
                "prev": prev,
            }
            rec["hash"] = _digest(rec)
            self._records.append(rec)
            if self.path is not None:
                with self.path.open("a") as fh:
                    fh.write(json.dumps(rec, sort_keys=True, default=str) + "\n")
            return rec

    def records(self) -> list[dict[str, Any]]:
        with self._lock:
            return list(self._records)

    def verify(self) -> tuple[bool, int | None]:
        """(True, None) when the chain is intact; otherwise (False, seq of the first bad record)."""
        prev = GENESIS
        for i, rec in enumerate(self.records(), start=1):
            if rec.get("seq") != i or rec.get("prev") != prev or rec.get("hash") != _digest(rec):
                return False, i
            prev = rec["hash"]
        return True, None
