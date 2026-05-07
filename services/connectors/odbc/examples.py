"""Runnable demonstration of :class:`OdbcClient`.

::

    python -m services.connectors.odbc.examples

Connects to a canned SQL Server-style DSN, runs a parameterised query,
and paginates through 30k rows in 10k-row batches.
"""

from __future__ import annotations

from .client import OdbcClient


def _banner(title: str) -> None:
    bar = "=" * len(title)
    print(f"\n{bar}\n{title}\n{bar}")


CONNECTION_STRING = (
    "DRIVER={ODBC Driver 18 for SQL Server};"
    "SERVER=tcp:erp-prod.example.internal,1433;"
    "DATABASE=ops;UID=etl_reader;PWD=<not-used>;"
    "Encrypt=yes;TrustServerCertificate=no"
)


def main() -> None:
    with OdbcClient(connection_string=CONNECTION_STRING) as client:

        _banner("Parameterised SELECT — region = 'EMEA'")
        cur = client.execute(
            "SELECT * FROM dbo.Customer WHERE region = ?",
            ("EMEA",),
        )
        print("columns:")
        for col, ctype in cur.description:
            print(f"  - {col:14s} {ctype}")
        first = cur.fetchmany(5)
        print("first 5 rows:")
        for r in first:
            print(f"  {r}")

        _banner("Paginated fetch_iter — 30k rows in 10k-row batches")
        total = 0
        for batch_idx, batch in enumerate(
            client.fetch_iter("SELECT * FROM dbo.Customer", batch_size=10_000), start=1
        ):
            total += len(batch)
            print(f"  batch {batch_idx}: {len(batch):>5,} rows  cumulative={total:>6,}")
        print(f"final row count: {total:,}")

        _banner("Composite predicate — region = 'AMER' AND country = 'US'")
        cur = client.execute(
            "SELECT * FROM dbo.Customer WHERE region = ? AND country = ?",
            ("AMER", "US"),
        )
        rows = cur.fetchall()
        print(f"  matched {len(rows):,} rows")
        for r in rows[:3]:
            print(f"  {r}")

        _banner("executemany — bulk write (no real writes happen)")
        rowcount = client.executemany(
            "INSERT INTO dbo.Customer_Staging (customer_id, region) VALUES (?, ?)",
            [("CUST1234567", "EMEA"), ("CUST1234568", "AMER")],
        )
        print(f"  pretended to insert {rowcount} rows")


if __name__ == "__main__":
    main()
