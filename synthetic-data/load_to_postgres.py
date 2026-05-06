"""
Standalone Postgres loader.

Reads existing CSV files from ``synthetic-data/output/<subdomain>/`` and
loads them into Postgres, one schema per subdomain. Use this when you've
already run ``generate_all.py`` (or unzipped the portable bundle) and just
want to populate a Postgres database without re-generating.

    python synthetic-data/load_to_postgres.py \\
        --postgres-url postgresql://explorer:explorer@localhost:5432/domain_explorer

If ``--postgres-url`` is omitted, ``DATABASE_URL`` is used.

Requires: psycopg[binary], sqlalchemy, pandas.
"""
from __future__ import annotations

import argparse
import os

from generate_all import load_into_postgres


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument(
        "--postgres-url",
        default=os.environ.get("DATABASE_URL"),
        help="Postgres URL (defaults to DATABASE_URL env var)",
    )
    args = p.parse_args()

    if not args.postgres_url:
        raise SystemExit(
            "Provide --postgres-url or set the DATABASE_URL env var.\n"
            "Example: postgresql://explorer:explorer@localhost:5432/domain_explorer"
        )

    print(f"Loading CSVs into Postgres at {args.postgres_url}")
    load_into_postgres(args.postgres_url)
    print("done.")


if __name__ == "__main__":
    main()
