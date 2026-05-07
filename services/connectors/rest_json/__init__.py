"""Generic REST/JSON client demo stub.

See ``client.py`` for :class:`RestJsonClient` and ``examples.py`` for a
runnable demonstration. Registry id: ``conn.rest``.
"""

from .client import (
    RestJsonClient,
    OAuth2ClientCredentials,
    RetryPolicy,
    RestError,
    RestResponse,
)

__all__ = [
    "RestJsonClient",
    "OAuth2ClientCredentials",
    "RetryPolicy",
    "RestError",
    "RestResponse",
]
