# odbc — demo ODBC adapter

Demonstrates the **ODBC** integration pattern that backs SQL Server,
DB2, Oracle, Snowflake, and most of the other database-warehouse
connectors that production ELT pipelines reach for. Aligns with the
generic database/file-feed patterns in
[`data/connectors/connectors.yaml`](../../../data/connectors/connectors.yaml).

## What's here

```
odbc/
├── __init__.py    # re-exports OdbcClient, OdbcCursor, OdbcError
├── client.py      # the demo client + canned dbo.Customer cursor
├── examples.py    # runnable: python -m services.connectors.odbc.examples
└── README.md      # you are here
```

## What it does

| Surface                                   | Notes                                                       |
| ----------------------------------------- | ----------------------------------------------------------- |
| `connect(dsn=..., connection_string=...)` | Accepts either a DSN name or full connection string.        |
| `execute(sql, params)`                    | Parameterised query. Returns a cursor.                      |
| `executemany(sql, seq_of_params)`         | Bulk write surface. The stub counts but does not persist.   |
| `cursor.fetchone / fetchmany / fetchall`  | Same shape as pyodbc.                                       |
| `client.fetch_iter(sql, batch_size=N)`    | Streaming generator for big result sets.                    |
| `cursor.description`                      | List of `(name, type)` pairs.                               |

The stub recognises one canned table — `dbo.Customer` — with 30,000
deterministically generated rows. Single-column predicates
(`WHERE region = ?`) and two-column predicates joined by `AND` are
honoured. Anything else raises `OdbcError`.

## Production swap-out

Two production paths:

- **`pyodbc`** — the standard, low-level ODBC binding.
  ```python
  import pyodbc
  conn = pyodbc.connect(
      "DRIVER={ODBC Driver 18 for SQL Server};"
      "SERVER=tcp:db.example.internal,1433;"
      "DATABASE=ops;UID=etl;PWD=...;Encrypt=yes"
  )
  cur = conn.cursor()
  cur.execute("SELECT * FROM dbo.Customer WHERE region = ?", ("EMEA",))
  for row in iter(lambda: cur.fetchmany(10_000), []):
      ...
  ```
- **`SQLAlchemy`** with `mssql+pyodbc` / `db2+ibm_db_sa` / `oracle+oracledb`
  — when you want connection pooling, ORM, or migration tools.

The `execute` / `cursor.fetchmany` shape matches pyodbc exactly so
swap-out is mechanical for the read path. For the write path,
`executemany` becomes a real round-trip.

## Why this is a stub

ODBC is the most common bridge between modern data platforms and the
on-prem SQL Server / DB2 / Oracle estates that still hold a lot of
operational data. This stub gives subdomain demos something to point
their pipelines at without needing a real driver or DSN.
