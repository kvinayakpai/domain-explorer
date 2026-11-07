"""Generic REST/JSON client demo stub.

See ``client.py`` for :class:`RestJsonClient` and ``examples.py`` for a
runnable demonstration. Registry id: ``conn.rest``.
"""

from .client import (
    OAuth2ClientCredentials,
    RestError,
    RestJsonClient,
    RestResponse,
    RetryPolicy,
)

__all__ = [
    "OAuth2ClientCredentials",
    "RestError",
    "RestJsonClient",
    "RestResponse",
    "RetryPolicy",
]
