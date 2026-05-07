"""OPC UA client demo stub.

See ``client.py`` for :class:`OpcUaClient` and ``examples.py`` for a
runnable demonstration. Registry id: ``conn.opc_ua``.
"""

from .client import OpcUaClient, OpcUaError, NodeValue

__all__ = ["OpcUaClient", "OpcUaError", "NodeValue"]
