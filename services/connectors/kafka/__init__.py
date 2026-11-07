"""Kafka producer / consumer demo stub.

See ``client.py`` for :class:`KafkaProducer` and :class:`KafkaConsumer` and
``examples.py`` for a runnable demonstration. Registry id: ``conn.cdc_kafka``.
"""

from .client import KafkaConsumer, KafkaError, KafkaMessage, KafkaProducer

__all__ = ["KafkaConsumer", "KafkaError", "KafkaMessage", "KafkaProducer"]
