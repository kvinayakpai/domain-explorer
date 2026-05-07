"""Runnable demonstration of :class:`SwiftMtParser`.

::

    python -m services.connectors.swift_mt.examples

Two illustrative messages are parsed: an MT103 single customer credit
transfer and an MT202 financial-institution transfer. Field tags follow
the SWIFT FIN standard (e.g. 20=Sender's Reference, 32A=Value
Date/Currency/Amount, 50K=Ordering Customer, 59=Beneficiary, 71A=Charge
Bearer).
"""

from __future__ import annotations

import json

from .parser import SwiftMtParser


SAMPLE_MT103 = """\
{1:F01ACMEUS33AXXX0000000000}\
{2:I103DEUTDEFFXXXXN}\
{3:{108:MT103REF000123}{121:7c4f6dfa-1b3b-4e02-9aab-d3f9c2e2e7af}}\
{4:
:20:RFQ-INV-19284
:23B:CRED
:32A:260507USD15750,00
:33B:USD15750,00
:50K:/123456789012
ACME WIDGETS INC
500 MAIN ST
CLEVELAND OH 44114 US
:52A:ACMEUS33XXX
:53A:CITIUS33XXX
:57A:DEUTDEFFXXX
:59:/DE89370400440532013000
NORTHWIND IMPORT GMBH
KOENIGSALLEE 14
40212 DUSSELDORF DE
:70:/INV/19284 SHIPMENT 2026-Q2
:71A:SHA
-}\
{5:{CHK:0CFE0FB0F1A1}}"""


SAMPLE_MT202 = """\
{1:F01CITIUS33AXXX0000000000}\
{2:I202DEUTDEFFXXXXN}\
{3:{108:MT202REF555}{121:b1b1b1b1-2222-3333-4444-555555555555}}\
{4:
:20:CITISETT260507A
:21:RFQ-INV-19284
:32A:260507USD15750,00
:52A:CITIUS33XXX
:57A:DEUTDEFFXXX
:58A:DEUTDEFFXXX
:72:/INS/ACMEUS33XXX
-}\
{5:{CHK:1A2B3C4D5E6F}}"""


def _banner(title: str) -> None:
    bar = "=" * len(title)
    print(f"\n{bar}\n{title}\n{bar}")


def main() -> None:
    parser = SwiftMtParser()

    _banner("MT103 — Single Customer Credit Transfer")
    parsed = parser.parse(SAMPLE_MT103)
    print(f"message type        : {parsed['message_type']}")
    bh = parsed["basic_header"]
    ah = parsed["application_header"]
    text = parsed["text"]
    assert isinstance(bh, dict)
    assert isinstance(ah, dict)
    assert isinstance(text, dict)
    print(f"sender LT (block 1) : {bh['logical_terminal']}")
    print(f"destination (block 2): {ah.get('destination_address')}")
    print()
    print(":20:  Sender's Reference     :", text["20"])
    print(":23B: Bank Operation Code    :", text["23B"])
    print(":32A: Value Date/CCY/Amount  :", text["32A_parsed"])
    print(":50K: Ordering Customer      :")
    for line in str(text["50K"]).splitlines():
        print(f"        {line}")
    print(":52A: Ordering Institution   :", text.get("52A"))
    print(":59:  Beneficiary            :")
    for line in str(text["59"]).splitlines():
        print(f"        {line}")
    print(":70:  Remittance Info        :", text.get("70"))
    print(":71A: Charge Bearer          :", text.get("71A"))

    _banner("MT202 — General Financial Institution Transfer")
    parsed = parser.parse(SAMPLE_MT202)
    text = parsed["text"]
    assert isinstance(text, dict)
    print(f"message type        : {parsed['message_type']}")
    print(":20:  Transaction Reference  :", text["20"])
    print(":21:  Related Reference      :", text["21"])
    print(":32A: Value Date/CCY/Amount  :", text["32A_parsed"])
    print(":58A: Beneficiary Institution:", text["58A"])
    print(":72:  Sender to Receiver     :", text["72"])

    _banner("Full parsed MT103 (JSON dump)")
    # Strip the multi-line raw values to keep the dump readable.
    print(json.dumps(parser.parse(SAMPLE_MT103), indent=2, default=str))


if __name__ == "__main__":
    main()
