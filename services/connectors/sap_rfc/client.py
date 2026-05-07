"""Demo SAP RFC / BAPI client.

This module emulates the surface area of an SAP NetWeaver RFC client
without making any real network calls. It is intentionally faithful to
the *shape* of real BAPI responses — STRUCTURE / TABLE parameters,
ABAP-style return codes, and the four-character RETURN.TYPE flag — but
the data is hand-built canned content suitable for tests and demos.

Production implementations should use the SAP NetWeaver RFC SDK via
`pyrfc <https://github.com/SAP/PyRFC>`_, e.g.::

    from pyrfc import Connection
    conn = Connection(ashost=host, sysnr=sysnr, client=client,
                      user=user, passwd=password)
    result = conn.call("BAPI_MATERIAL_GET_DETAIL", MATERIAL="000000000000000123")

The signature of :meth:`SapRfcClient.call_function` matches that
``Connection.call`` shape so callers can swap implementations without
changing their code.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


# -- canned data --------------------------------------------------------------

# These are illustrative responses, not real SAP data. Field names match
# the ABAP DDIC structure types referenced by each BAPI so callers see
# the right keys when iterating on real systems later.

_MATERIAL_MASTER: Dict[str, Dict[str, Any]] = {
    "000000000000000123": {
        "MATERIAL_GENERAL_DATA": {
            "MATERIAL": "000000000000000123",
            "IND_SECTOR": "M",
            "MATL_TYPE": "FERT",
            "MATL_GROUP": "00107",
            "BASE_UOM": "EA",
            "OLD_MAT_NO": "GEAR-23-A",
            "CREATED_ON": "2021-04-12",
            "CREATED_BY": "MM_LOAD",
            "MATL_DESC": "Helical reduction gear, 1:7 ratio",
            "GROSS_WT": 4.250,
            "NET_WEIGHT": 3.880,
            "UNIT_OF_WT": "KG",
        },
        "RETURN": {
            "TYPE": "S",
            "ID": "MM",
            "NUMBER": "001",
            "MESSAGE": "Material 000000000000000123 read successfully",
            "MESSAGE_V1": "000000000000000123",
        },
    },
    "000000000000000456": {
        "MATERIAL_GENERAL_DATA": {
            "MATERIAL": "000000000000000456",
            "IND_SECTOR": "M",
            "MATL_TYPE": "ROH",
            "MATL_GROUP": "00204",
            "BASE_UOM": "KG",
            "OLD_MAT_NO": "STEEL-A36",
            "CREATED_ON": "2019-09-30",
            "CREATED_BY": "MM_LOAD",
            "MATL_DESC": "Hot-rolled structural steel, ASTM A36",
            "GROSS_WT": 1.000,
            "NET_WEIGHT": 1.000,
            "UNIT_OF_WT": "KG",
        },
        "RETURN": {
            "TYPE": "S",
            "ID": "MM",
            "NUMBER": "001",
            "MESSAGE": "Material 000000000000000456 read successfully",
            "MESSAGE_V1": "000000000000000456",
        },
    },
}

_CUSTOMER_LIST: List[Dict[str, Any]] = [
    {
        "CUSTOMER": "0000010001",
        "NAME": "Acme Industrial GmbH",
        "CITY": "Stuttgart",
        "COUNTRY": "DE",
        "POSTL_CODE": "70173",
        "ACCNT_GRP": "Z001",
    },
    {
        "CUSTOMER": "0000010002",
        "NAME": "Northwind Manufacturing Inc.",
        "CITY": "Cleveland",
        "COUNTRY": "US",
        "POSTL_CODE": "44114",
        "ACCNT_GRP": "Z001",
    },
    {
        "CUSTOMER": "0000010003",
        "NAME": "Sakura Logistics K.K.",
        "CITY": "Osaka",
        "COUNTRY": "JP",
        "POSTL_CODE": "5300001",
        "ACCNT_GRP": "Z002",
    },
]

# Tiny canned table for RFC_READ_TABLE demonstrations.
_TABLES: Dict[str, Dict[str, Any]] = {
    "T001": {
        "FIELDS": [
            {"FIELDNAME": "BUKRS", "OFFSET": 0, "LENGTH": 4, "TYPE": "C"},
            {"FIELDNAME": "BUTXT", "OFFSET": 4, "LENGTH": 25, "TYPE": "C"},
            {"FIELDNAME": "WAERS", "OFFSET": 29, "LENGTH": 5, "TYPE": "C"},
            {"FIELDNAME": "LAND1", "OFFSET": 34, "LENGTH": 3, "TYPE": "C"},
        ],
        "DATA": [
            {"WA": "1000Acme Industrial Holdings   EUR  DE "},
            {"WA": "2000Northwind Mfg               USD  US "},
            {"WA": "3000Sakura Logistics            JPY  JP "},
        ],
    },
}


# -- public API ---------------------------------------------------------------


@dataclass
class SapRfcClient:
    """A minimal demo SAP RFC / BAPI client.

    The constructor parameters mirror the connection options taken by
    ``pyrfc.Connection``. Nothing is validated and no network is opened —
    this is a stub.
    """

    host: str
    sysnr: str
    client: str
    user: str
    password: str = field(repr=False)
    _connected: bool = field(default=False, init=False, repr=False)

    # --- lifecycle ---

    def connect(self) -> None:
        """Open the RFC connection. No-op in the stub."""
        self._connected = True

    def disconnect(self) -> None:
        """Close the RFC connection. No-op in the stub."""
        self._connected = False

    def __enter__(self) -> "SapRfcClient":
        self.connect()
        return self

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        self.disconnect()

    @property
    def is_connected(self) -> bool:
        return self._connected

    # --- BAPI dispatch ---

    def call_function(self, fn_name: str, **params: Any) -> Dict[str, Any]:
        """Invoke a remote BAPI / RFC function.

        Three function modules are recognised:

        * ``BAPI_MATERIAL_GET_DETAIL`` — read a material master record
          by ``MATERIAL`` (18-char SAP material number).
        * ``BAPI_CUSTOMER_GETLIST`` — list customers, optionally
          filtered by ``IDRANGE`` (a list of ``{SIGN, OPTION, LOW,
          HIGH}`` row dicts in real ABAP, simplified here to a list of
          customer numbers via ``CUSTOMER_IDS``).
        * ``RFC_READ_TABLE`` — read raw rows from a transparent table
          named in ``QUERY_TABLE``. Currently only ``T001`` is canned.

        Any other ``fn_name`` raises ``NotImplementedError``.
        """
        if not self._connected:
            # Mirror pyrfc behaviour: implicit connect on first call.
            self.connect()

        if fn_name == "BAPI_MATERIAL_GET_DETAIL":
            return self._bapi_material_get_detail(params)
        if fn_name == "BAPI_CUSTOMER_GETLIST":
            return self._bapi_customer_getlist(params)
        if fn_name == "RFC_READ_TABLE":
            return self._rfc_read_table(params)

        raise NotImplementedError(
            f"Function module {fn_name!r} is not canned in this demo stub. "
            "Add a handler in SapRfcClient or use a real pyrfc.Connection."
        )

    # --- handlers ---

    def _bapi_material_get_detail(self, params: Dict[str, Any]) -> Dict[str, Any]:
        material = str(params.get("MATERIAL", "")).rjust(18, "0")
        if material in _MATERIAL_MASTER:
            return _MATERIAL_MASTER[material]
        return {
            "MATERIAL_GENERAL_DATA": {},
            "RETURN": {
                "TYPE": "E",
                "ID": "MM",
                "NUMBER": "326",
                "MESSAGE": f"Material {material} does not exist",
                "MESSAGE_V1": material,
            },
        }

    def _bapi_customer_getlist(self, params: Dict[str, Any]) -> Dict[str, Any]:
        ids: Optional[List[str]] = params.get("CUSTOMER_IDS")
        rows = (
            [c for c in _CUSTOMER_LIST if c["CUSTOMER"] in ids]
            if ids
            else list(_CUSTOMER_LIST)
        )
        return {
            "ADDRESSDATA": rows,
            "RETURN": [
                {
                    "TYPE": "S",
                    "ID": "F2",
                    "NUMBER": "000",
                    "MESSAGE": f"{len(rows)} customer(s) returned",
                }
            ],
        }

    def _rfc_read_table(self, params: Dict[str, Any]) -> Dict[str, Any]:
        table_name = params.get("QUERY_TABLE", "")
        if table_name not in _TABLES:
            return {
                "FIELDS": [],
                "DATA": [],
                "OPTIONS": params.get("OPTIONS", []),
            }
        rowcount = int(params.get("ROWCOUNT", 0)) or None
        rows = _TABLES[table_name]["DATA"]
        if rowcount is not None:
            rows = rows[:rowcount]
        return {
            "FIELDS": list(_TABLES[table_name]["FIELDS"]),
            "DATA": list(rows),
            "OPTIONS": params.get("OPTIONS", []),
        }
