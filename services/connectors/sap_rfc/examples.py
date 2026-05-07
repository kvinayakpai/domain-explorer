"""Runnable demonstration of :class:`SapRfcClient`.

::

    python -m services.connectors.sap_rfc.examples

The script opens a (fake) RFC connection, fetches a material master
record, lists customers, reads a few rows from table ``T001``, and
prints the canned response payloads. It exercises the same call shape
that production ``pyrfc`` users employ.
"""

from __future__ import annotations

import json
from pprint import pprint

from .client import SapRfcClient


def _banner(title: str) -> None:
    bar = "=" * len(title)
    print(f"\n{bar}\n{title}\n{bar}")


def main() -> None:
    # The connection arguments mirror what you'd pass to pyrfc.Connection
    # in production. None of them are validated in the demo stub.
    with SapRfcClient(
        host="sap-erp.example.internal",
        sysnr="00",
        client="100",
        user="DEMO_RFC",
        password="<not-used>",
    ) as conn:

        _banner("BAPI_MATERIAL_GET_DETAIL — known material")
        result = conn.call_function(
            "BAPI_MATERIAL_GET_DETAIL", MATERIAL="000000000000000123"
        )
        pprint(result, sort_dicts=False)

        _banner("BAPI_MATERIAL_GET_DETAIL — unknown material")
        result = conn.call_function("BAPI_MATERIAL_GET_DETAIL", MATERIAL="999")
        pprint(result["RETURN"], sort_dicts=False)

        _banner("BAPI_CUSTOMER_GETLIST — first page")
        result = conn.call_function("BAPI_CUSTOMER_GETLIST")
        print(f"customer rows returned: {len(result['ADDRESSDATA'])}")
        for row in result["ADDRESSDATA"]:
            print(f"  - {row['CUSTOMER']}  {row['NAME']:30s}  {row['COUNTRY']}")

        _banner("BAPI_CUSTOMER_GETLIST — filtered")
        result = conn.call_function(
            "BAPI_CUSTOMER_GETLIST", CUSTOMER_IDS=["0000010002"]
        )
        print(json.dumps(result["ADDRESSDATA"], indent=2))

        _banner("RFC_READ_TABLE — T001 (Company codes)")
        result = conn.call_function(
            "RFC_READ_TABLE",
            QUERY_TABLE="T001",
            ROWCOUNT=5,
            OPTIONS=[],
        )
        for f in result["FIELDS"]:
            print(
                f"  field {f['FIELDNAME']:10s} offset={f['OFFSET']:>3d} "
                f"len={f['LENGTH']:>3d} type={f['TYPE']}"
            )
        for row in result["DATA"]:
            print(f"    {row['WA']!r}")


if __name__ == "__main__":
    main()
