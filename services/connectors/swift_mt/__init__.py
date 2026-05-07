"""SWIFT MT message parser demo stub.

See ``parser.py`` for :class:`SwiftMtParser` and ``examples.py`` for
runnable demonstrations against MT103 and MT202 messages. Registry id:
``conn.swift_iso20022``.
"""

from .parser import SwiftMtParser, SwiftMtParseError

__all__ = ["SwiftMtParser", "SwiftMtParseError"]
