"""Demo ODBC adapter.

Emulates the surface area of pyodbc / SQLAlchemy ODBC for read-heavy
workloads: ``connect``, parameterised ``execute``, ``executemany``, and
chunked ``fetch_iter`` for streaming large result sets.

The stub recognises a single canned query against
``dbo.Customer`` and returns a 30k-row "result set" via a generator so
the demo can exercise pagination without materialising everything in
memory.

Production swap-out::

    # pyodbc:
    import pyodbc
    conn = pyodbc.connect(
        "DRIVER={ODBC Driver 18 for SQL Server};"
        "SERVER=tcp:db.example.internal,1433;"
        "DATABASE=ops;UID=etl;PWD=...;Encrypt=yes;TrustServerCertificate=no"
    )
    cur = conn.cursor()
    cur.execute("SELECT * FROM dbo.Customer WHERE region = ?", ("EMEA",))
    rows = cur.fetchmany(10000)

    # SQLAlchemy:
    from sqlalchemy import create_engine
    engine = create_engine("mssql+pyodbc:///?odbc_connect=" + urllib.parse.quote_plus(dsn))
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Dict, Iterator, List, Optional, Sequence, Tuple


# -- exceptions ---------------------------------------------------------------


class OdbcError(Exception):
    """Mirrors pyodbc.Error."""


# -- canned data --------------------------------------------------------------


_CUSTOMER_COLUMNS = (
    ("customer_id", "VARCHAR"),
    ("region",      "VARCHAR"),
    ("country",     "VARCHAR"),
    ("segment",     "VARCHAR"),
    ("annual_rev",  "DECIMAL(14,2)"),
    ("active",      "BIT"),
)


def _row(i: int) -> Tuple[Any, ...]:
    """Generate one canned customer row deterministically."""
    region = ("EMEA", "AMER", "APAC")[i % 3]
    country = {"EMEA": "DE", "AMER": "US", "APAC": "JP"}[region]
    segment = ("enterprise", "midmarket", "smb")[i % 3]
    rev = round(10_000 + (i * 137.13) % 1_000_000, 2)
    active = (i % 17) != 0
    return (f"CUST{i:07d}", region, country, segment, rev, active)


def _generate_rows(predicate: str) -> Iterator[Tuple[Any, ...]]:
    """Generate up to 30,000 rows, optionally filtered by a tiny WHERE clause."""
    region_match = re.search(r"region\s*=\s*\?", predicate, re.IGNORECASE)
    country_match = re.search(r"country\s*=\s*\?", predicate, re.IGNORECASE)
    for i in range(30_000):
        row = _row(i)
        if region_match and i >= 0:
            # Filtered region applied externally via param substitution; we
            # only generate the row, the cursor filters.
            pass
        if country_match:
            pass
        yield row


# -- cursor ------------------------------------------------------------------


@dataclass
class OdbcCursor:
    """Subset of a pyodbc.Cursor."""

    description: List[Tuple[str, str]] = field(default_factory=list)
    rowcount: int = -1
    _generator: Optional[Iterator[Tuple[Any, ...]]] = field(default=None, init=False, repr=False)
    _filter: Dict[str, Any] = field(default_factory=dict, init=False, repr=False)

    def execute(self, sql: str, params: Optional[Sequence[Any]] = None) -> "OdbcCursor":
        sql_norm = " ".join(sql.split()).strip().rstrip(";")
        params = list(params or [])

        if re.match(r"select\s+\*\s+from\s+dbo\.customer", sql_norm, re.IGNORECASE):
            self.description = [(c[0], c[1]) for c in _CUSTOMER_COLUMNS]
            self._filter = {}
            # Look for WHERE clauses with a single positional placeholder.
            m = re.search(r"where\s+(.*)", sql_norm, re.IGNORECASE)
            if m:
                where = m.group(1)
                tokens = re.split(r"\s+and\s+", where, flags=re.IGNORECASE)
                for tok, val in zip(tokens, params):
                    col_match = re.match(r"(\w+)\s*=\s*\?", tok.strip(), re.IGNORECASE)
                    if col_match:
                        self._filter[col_match.group(1).lower()] = val
            self._generator = self._iter_filtered()
            self.rowcount = -1  # streaming, unknown until exhausted
            return self
        raise OdbcError(f"stub does not recognise SQL: {sql_norm!r}")

    def executemany(self, sql: str, seq_of_params: Sequence[Sequence[Any]]) -> int:
        # Stub: count the params, no real write happens.
        n = len(list(seq_of_params))
        self.rowcount = n
        return n

    def _iter_filtered(self) -> Iterator[Tuple[Any, ...]]:
        col_index = {c[0]: i for i, c in enumerate(_CUSTOMER_COLUMNS)}
        for row in _generate_rows(""):
            ok = True
            for col, val in self._filter.items():
                idx = col_index.get(col.lower())
                if idx is None or row[idx] != val:
                    ok = False
                    break
            if ok:
                yield row

    def fetchone(self) -> Optional[Tuple[Any, ...]]:
        if self._generator is None:
            return None
        return next(self._generator, None)

    def fetchmany(self, size: int) -> List[Tuple[Any, ...]]:
        if self._generator is None or size <= 0:
            return []
        out: List[Tuple[Any, ...]] = []
        for _ in range(size):
            row = next(self._generator, None)
            if row is None:
                break
            out.append(row)
        return out

    def fetchall(self) -> List[Tuple[Any, ...]]:
        if self._generator is None:
            return []
        rows = list(self._generator)
        self._generator = iter([])
        return rows


# -- client ------------------------------------------------------------------


@dataclass
class OdbcClient:
    """Minimal demo ODBC client.

    ``connect`` accepts either a DSN name (``DSN=ProductionERP``) or a full
    connection string (``DRIVER={ODBC Driver 18 ...};SERVER=...``). Nothing
    is validated.
    """

    dsn: Optional[str] = None
    connection_string: Optional[str] = None
    autocommit: bool = False
    _connected: bool = field(default=False, init=False, repr=False)

    def connect(self, dsn: Optional[str] = None,
                connection_string: Optional[str] = None) -> "OdbcClient":
        if dsn:
            self.dsn = dsn
        if connection_string:
            self.connection_string = connection_string
        if not (self.dsn or self.connection_string):
            raise OdbcError("connect requires either dsn or connection_string")
        self._connected = True
        return self

    def cursor(self) -> OdbcCursor:
        if not self._connected:
            self.connect()
        return OdbcCursor()

    def execute(self, sql: str, params: Optional[Sequence[Any]] = None) -> OdbcCursor:
        cur = self.cursor()
        cur.execute(sql, params)
        return cur

    def executemany(self, sql: str, seq_of_params: Sequence[Sequence[Any]]) -> int:
        cur = self.cursor()
        return cur.executemany(sql, seq_of_params)

    def fetch_iter(
        self,
        sql: str,
        params: Optional[Sequence[Any]] = None,
        batch_size: int = 10_000,
    ) -> Iterator[List[Tuple[Any, ...]]]:
        """Yield batches of rows of size ``batch_size`` until the cursor
        is exhausted. Pattern mirrors how production ETL drives big
        SELECTs without buffering the whole result set."""
        cur = self.execute(sql, params)
        while True:
            batch = cur.fetchmany(batch_size)
            if not batch:
                return
            yield batch

    def close(self) -> None:
        self._connected = False

    def __enter__(self) -> "OdbcClient":
        if not self._connected:
            self.connect()
        return self

    def __exit__(self, *exc: Any) -> None:
        self.close()
