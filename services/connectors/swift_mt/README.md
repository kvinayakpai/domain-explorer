# swift_mt — demo SWIFT MT message parser

Demonstrates the **SWIFT MT / ISO 20022** connector pattern from the
registry (`conn.swift_iso20022` in
[`data/connectors/connectors.yaml`](../../../data/connectors/connectors.yaml)).

## What's here

```
swift_mt/
├── __init__.py    # re-exports SwiftMtParser, SwiftMtParseError
├── parser.py      # the structural parser
├── examples.py    # runnable: python -m services.connectors.swift_mt.examples
└── README.md      # you are here
```

## What it does

`SwiftMtParser` takes a raw FIN message and decomposes it into the five
canonical SWIFT blocks:

| Block | Name                | Contents                                                   |
| ----- | ------------------- | ----------------------------------------------------------- |
| 1     | Basic header         | Application id, service id, sender LT, session/sequence     |
| 2     | Application header   | I/O direction, message type (MT103/MT202/…), destination LT |
| 3     | User header (opt.)   | Sub-tags: `108` (MUR), `121` (UETR), etc.                   |
| 4     | Text block           | The message body — `:20:`, `:32A:`, `:50K:`, `:59:`, …      |
| 5     | Trailer              | Checksum (`CHK`) and other authentication trailers          |

For block 4, each `:tag:` line is broken out as a key in the returned
dict. `:32A:` (Value Date / Currency / Amount) is additionally split
into a `value_date` (ISO 8601), `currency`, and `amount` for
convenience.

## Why MT103 and MT202

The two messages exercised in `examples.py` are the most common in
cross-border payments and correspondent banking:

- **MT103** — Single Customer Credit Transfer. Carries the actual
  customer-to-customer payment instruction (debtor, creditor, amount,
  remittance info).
- **MT202** / **MT202COV** — General Financial Institution Transfer.
  The "cover" leg between correspondents that funds the underlying
  MT103.

These are the messages that are migrating to ISO 20022 `pacs.008` and
`pacs.009` under the SWIFT MT-to-MX programme — same business meaning,
richer XML structure, much longer message length.

## What it doesn't do

- **No FIN validation** — character set rules (`x`, `y`, `z`, `n`,
  `c`), mandatory/optional field flags, network rules, and CBPR+
  guidelines are out of scope.
- **No MX / ISO 20022.** A real production gateway parses both formats
  and translates between them; this stub only handles MT.
- **No authentication.** SWIFT's MAC, SHA, and trailer validation are
  network-level concerns.

## Production swap-out

For real ELT pipelines you'd reach for a maintained library:

- [`mt-940`](https://pypi.org/project/mt-940/) — focused on MT940/MT942
  bank statements.
- [`swift-parser`](https://github.com/anchormarine/swift-parser) —
  broader FIN coverage.
- Commercial MT/MX translators: SmartStream TLM, IBM Sterling B2B
  Integrator, Volante, Bottomline.

The parsed dict shape `SwiftMtParser` returns is compatible with the
common "block 1/2/3/4/5" convention those libraries also use, so a
swap typically only changes the constructor.
