"""Runnable demonstration of :class:`OpcUaClient`.

::

    python -m services.connectors.opc_ua.examples

Reads 5 MES tags one-shot and then subscribes to ``ns=2;s=Boiler.Temp``
with a 250 ms sample interval for 5 samples.
"""

from __future__ import annotations

from .client import OpcUaClient, NodeValue


def _banner(title: str) -> None:
    bar = "=" * len(title)
    print(f"\n{bar}\n{title}\n{bar}")


def main() -> None:
    with OpcUaClient(
        endpoint_url="opc.tcp://plc-floor1.example.internal:4840",
        security_policy="Basic256Sha256",
        username="opc-reader",
        password="<not-used>",
    ) as client:

        _banner("Browse namespace")
        ns = client.browse_namespace()
        for node_id, dtype, unit in ns:
            unit_str = f" [{unit}]" if unit else ""
            print(f"  {node_id:30s}  {dtype:8s}{unit_str}")

        _banner("Read 5 tags")
        for tag in (
            "ns=2;s=Boiler.Temp",
            "ns=2;s=Boiler.Pressure",
            "ns=2;s=ConveyorSpeed",
            "ns=2;s=Oven.Actual",
            "ns=2;s=PackerStatus",
        ):
            v = client.read_node(tag)
            print(f"  {v.node_id:30s} = {v.value!r:>10}  ({v.data_type})  ts={v.source_timestamp_ms}")

        _banner("Subscribe to ns=2;s=Boiler.Temp @ 250 ms (5 samples)")
        received: list[NodeValue] = []

        def on_data(value: NodeValue) -> None:
            received.append(value)
            print(f"  sample {len(received)}: {value.value:6.2f} {value.data_type}")

        client.subscribe(
            node_id="ns=2;s=Boiler.Temp",
            interval_ms=250,
            callback=on_data,
            max_samples=5,
        )
        print(f"  total samples received: {len(received)}")


if __name__ == "__main__":
    main()
