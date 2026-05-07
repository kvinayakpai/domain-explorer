"""MQTT publisher/subscriber demo stub (Sparkplug B-aware).

See ``client.py`` for :class:`MqttClient` and ``examples.py`` for a
runnable demonstration. Registry ids: ``conn.mqtt`` and
``conn.sparkplug_b``.
"""

from .client import MqttClient, MqttMessage, MqttError, SparkplugBPayload

__all__ = ["MqttClient", "MqttMessage", "MqttError", "SparkplugBPayload"]
