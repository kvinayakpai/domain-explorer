"""SWIFT MT message parser.

Parses raw FIN MT messages — the legacy SWIFT format that ISO 20022
``pacs.008`` / ``pacs.009`` are gradually replacing — into a structured
dictionary of named blocks. Targets the cross-border payments and
correspondent banking subdomains; in particular MT103 (single customer
credit transfer) and MT202 (general financial institution transfer) /
MT202COV (cover payment) messages.

The parser is *not* a full FIN validator. It implements the structural
layer of the standard:

* The five message blocks: ``{1: basic header}{2: application
  header}{3: user header}{4: text block}{5: trailer}``.
* Tag-based dissection of block 4 (``:20:``, ``:32A:``, ``:50K:``,
  ``:59:``, ``:71A:``, …) including the ``:32A:`` value-date / currency
  / amount triple.

It does **not** perform character-set checks, currency/amount sanity
checks, or any of the network-level validations that the actual SWIFT
network does. For production use, reach for a maintained library such
as `swift-parser
<https://github.com/anchormarine/swift-parser>`_ or `mt-940
<https://pypi.org/project/mt-940/>`_, or commercial offerings like
SmartStream TLM.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple


class SwiftMtParseError(ValueError):
    """Raised when the input does not look like a SWIFT MT message."""


# Each block header is "{N:" where N is 1-5. Block 4 is the only one
# that contains ``:tag:`` style fields; the others are flat strings.
_BLOCK_RE = re.compile(r"\{(?P<id>[1-5]):(?P<body>.*?)\}", re.DOTALL)

# Field tags inside block 4 look like ``:20:`` or ``:32A:``. They are
# left-anchored and the value runs until the next tag or the closing
# ``-}`` of block 4.
_TAG_RE = re.compile(r"(?ms)^:(?P<tag>[0-9]{2}[A-Z]?):(?P<value>.*?)(?=^:[0-9]{2}[A-Z]?:|\Z)")


@dataclass
class SwiftMtParser:
    """Parser for SWIFT FIN MT messages."""

    strict: bool = True

    # -- public API ---------------------------------------------------

    def parse(self, raw: str) -> Dict[str, object]:
        """Parse a raw MT message into a dict of named blocks.

        The returned dict has these top-level keys when present:

        * ``message_type`` — three-digit MT type (e.g. ``"103"``).
        * ``basic_header`` — block 1 fields (``application_id``, ``service_id``,
          ``logical_terminal``, ``session_number``, ``sequence_number``).
        * ``application_header`` — block 2 fields, including ``input_output``
          (``"I"`` or ``"O"``), ``message_type``, and direction-specific
          fields (``destination_address`` / ``sender_address``, priority,
          delivery monitoring).
        * ``user_header`` — block 3 sub-tags as a flat dict.
        * ``text`` — block 4 fields keyed by tag (e.g. ``"20"``, ``"32A"``).
          Tag ``32A`` is additionally split into ``value_date``,
          ``currency``, and ``amount``.
        * ``trailer`` — block 5 sub-tags.
        """
        if not raw:
            raise SwiftMtParseError("empty input")
        normalised = raw.replace("\r\n", "\n").strip()
        blocks = self._split_blocks(normalised)
        if 1 not in blocks or 2 not in blocks or 4 not in blocks:
            raise SwiftMtParseError(
                "MT message must contain blocks 1, 2, and 4 — got "
                f"{sorted(blocks)}"
            )

        out: Dict[str, object] = {
            "basic_header": self._parse_basic_header(blocks[1]),
            "application_header": self._parse_application_header(blocks[2]),
        }
        if 3 in blocks:
            out["user_header"] = self._parse_subtags(blocks[3])
        out["text"] = self._parse_text_block(blocks[4])
        if 5 in blocks:
            out["trailer"] = self._parse_subtags(blocks[5])

        # Convenience: surface the message type at the top level.
        ah = out["application_header"]
        if isinstance(ah, dict):
            mt = ah.get("message_type")
            if isinstance(mt, str):
                out["message_type"] = mt
        return out

    # -- block splitting ---------------------------------------------

    def _split_blocks(self, raw: str) -> Dict[int, str]:
        """Return a dict mapping block id -> body. Handles nested ``{...}``
        in block 3 (sub-tags) and block 4's ``-}`` close marker."""
        blocks: Dict[int, str] = {}
        i = 0
        n = len(raw)
        while i < n:
            if raw[i] != "{":
                # Skip any framing whitespace.
                i += 1
                continue
            # Block 4 specifically ends with ``-}`` because its body
            # contains its own ``:tag:`` lines that may include ``}``
            # characters in URLs etc. We special-case it.
            close = self._find_block_end(raw, i)
            if close == -1:
                if self.strict:
                    raise SwiftMtParseError(f"unterminated block at offset {i}")
                break
            body = raw[i + 1 : close]
            colon = body.find(":")
            if colon < 1 or not body[:colon].isdigit():
                if self.strict:
                    raise SwiftMtParseError(f"malformed block header: {body[:8]!r}")
                i = close + 1
                continue
            block_id = int(body[:colon])
            block_body = body[colon + 1 :]
            # Block 4 ends ``...-`` (then ``}``). Strip the trailer dash.
            if block_id == 4 and block_body.endswith("-"):
                block_body = block_body[:-1]
            blocks[block_id] = block_body
            i = close + 1
        return blocks

    @staticmethod
    def _find_block_end(raw: str, start: int) -> int:
        """Find the matching ``}`` for the ``{`` at ``start``, accounting
        for nested braces (block 3 sub-tags can themselves be ``{...}``)."""
        depth = 0
        for j in range(start, len(raw)):
            ch = raw[j]
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    return j
        return -1

    # -- block 1: basic header --------------------------------------

    @staticmethod
    def _parse_basic_header(body: str) -> Dict[str, str]:
        """Block 1 is fixed-width: F01BANKBEBBAXXX0000000000."""
        b = body.strip()
        if len(b) < 25:
            return {"raw": b}
        return {
            "application_id": b[0:1],            # F=FIN, A=GPA, L=GPA login
            "service_id": b[1:3],                # 01=FIN
            "logical_terminal": b[3:15],         # 12-char LT address (BIC + branch + terminal)
            "session_number": b[15:19],          # 4-digit session number
            "sequence_number": b[19:25],         # 6-digit ISN
            "raw": b,
        }

    # -- block 2: application header --------------------------------

    @staticmethod
    def _parse_application_header(body: str) -> Dict[str, str]:
        """Block 2 has Input/Output variants:

        * Input  : ``I`` MTtype DestinationLT [Priority] [DeliveryMonitoring] [Obsolescence]
        * Output : ``O`` MTtype InputTime SenderInputRefDate SenderInputRefLT SenderInputRefSession SenderInputRefSeq OutputDate OutputTime Priority
        """
        b = body.strip()
        if not b or b[0] not in ("I", "O"):
            return {"raw": b}
        io = b[0]
        message_type = b[1:4]
        out: Dict[str, str] = {
            "input_output": io,
            "message_type": message_type,
            "raw": b,
        }
        if io == "I":
            # 4..16 = destination LT (12 chars). Anything after = priority + opt fields.
            out["destination_address"] = b[4:16]
            out["priority"] = b[16:17] or ""
            if len(b) > 17:
                out["delivery_monitoring"] = b[17:18]
            if len(b) > 18:
                out["obsolescence_period"] = b[18:21]
        else:
            # Output: 4-digit input time, 6-digit MIR date, 12 LT, 4-digit session, 6-digit seq,
            # then 6 output date, 4 output time, priority.
            out["input_time"] = b[4:8]
            out["sender_input_ref"] = b[8:36]  # 6 + 12 + 4 + 6
            out["output_date"] = b[36:42]
            out["output_time"] = b[42:46]
            if len(b) > 46:
                out["priority"] = b[46:47]
        return out

    # -- generic { tag : value } sub-block parser -------------------

    @staticmethod
    def _parse_subtags(body: str) -> Dict[str, str]:
        """Used for block 3 (user header) and block 5 (trailer). Sub-tags
        look like ``{108:REF12345}{121:uuid}``."""
        out: Dict[str, str] = {}
        for m in re.finditer(r"\{(\d{3}):([^}]*)\}", body):
            out[m.group(1)] = m.group(2)
        return out

    # -- block 4: text block ----------------------------------------

    def _parse_text_block(self, body: str) -> Dict[str, object]:
        """Extract ``:tag:`` fields from block 4. Values that span
        multiple lines (e.g. ``:50K:`` ordering customer with name and
        address) are kept as multi-line strings."""
        b = body.strip("\n").strip()
        out: Dict[str, object] = {}
        for m in _TAG_RE.finditer(b):
            tag = m.group("tag")
            value = m.group("value").rstrip("\n").rstrip()
            out[tag] = value
        # 32A is high-value enough to warrant structured access.
        if "32A" in out and isinstance(out["32A"], str):
            parsed_32a = self._parse_32a(out["32A"])
            if parsed_32a is not None:
                out["32A_parsed"] = parsed_32a
        return out

    @staticmethod
    def _parse_32a(value: str) -> Optional[Dict[str, object]]:
        """``:32A:YYMMDDCCCN,NN`` — value date (6), ISO currency (3),
        amount with comma decimal."""
        s = value.strip().replace("\n", "")
        m = re.fullmatch(r"(\d{6})([A-Z]{3})([\d,]+)", s)
        if not m:
            return None
        amount = float(m.group(3).replace(",", "."))
        return {
            "value_date": _yymmdd_to_iso(m.group(1)),
            "currency": m.group(2),
            "amount": amount,
        }


def _yymmdd_to_iso(s: str) -> str:
    """SWIFT YYMMDD → ISO 8601 date. Two-digit year resolves to 2000-2099."""
    yy, mm, dd = s[0:2], s[2:4], s[4:6]
    return f"20{yy}-{mm}-{dd}"


# Convenience helpers ---------------------------------------------------------


def parse_message(raw: str, *, strict: bool = True) -> Dict[str, object]:
    """Module-level helper: ``SwiftMtParser(strict=strict).parse(raw)``."""
    return SwiftMtParser(strict=strict).parse(raw)


def list_block_4_tags(parsed: Dict[str, object]) -> List[Tuple[str, str]]:
    """Return a flat ``[(tag, value), ...]`` list from the parsed text
    block, in declaration order."""
    text = parsed.get("text")
    if not isinstance(text, dict):
        return []
    return [(k, v) for k, v in text.items() if isinstance(v, str)]
