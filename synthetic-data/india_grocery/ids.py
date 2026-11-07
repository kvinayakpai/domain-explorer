"""GS1 identifiers with valid check digits.

All numbers use GS1 prefix 29. GS1 sets aside prefixes 02 and 20-29 for restricted
circulation within a company or a region (GSCN 23-006), so these codes cannot be mistaken
for globally issued product, location or pallet numbers.
"""
from __future__ import annotations

PREFIX = "29"
COMPANY = "00001"  # fictional company reference under the restricted prefix


def check_digit(body: str) -> str:
    """GS1 mod-10 check digit: weights 3,1,3,... from the rightmost digit of the body."""
    total = sum(int(ch) * (3 if i % 2 == 0 else 1) for i, ch in enumerate(reversed(body)))
    return str((10 - total % 10) % 10)


def is_valid(code: str) -> bool:
    return code.isdigit() and len(code) in (13, 14, 18) and check_digit(code[:-1]) == code[-1]


def gtin13(item_ref: int) -> str:
    body = f"{PREFIX}{COMPANY}{item_ref:05d}"
    return body + check_digit(body)


def gln13(location_ref: int) -> str:
    body = f"{PREFIX}{COMPANY}{location_ref:05d}"
    return body + check_digit(body)


def sscc18(serial: int, extension: int = 0) -> str:
    body = f"{extension}{PREFIX}{COMPANY}{serial:09d}"
    return body + check_digit(body)
