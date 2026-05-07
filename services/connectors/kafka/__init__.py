"""Kafka producer / consumer demo stub.

See ``client.py`` for :class:`KafkaProducer` and :class:`KafkaConsumer` and
``examples.py`` for a runnable demonstration. Registry id: ``conn.cdc_kafka``.
"""

from .client import KafkaProducer, KafkaConsumer, KafkaMessage, KafkaError

__all__ = ["KafkaProducer", "KafkaConsumer", "KafkaMessage", "KafkaError"]
