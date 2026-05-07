"""FHIR R4 REST client demo stub.

See ``client.py`` for :class:`FhirRestClient` and ``examples.py`` for a
runnable demonstration. References the FHIR R4 standard (HL7 FHIR
4.0.1).
"""

from .client import FhirRestClient, FhirAuth, FhirError

__all__ = ["FhirRestClient", "FhirAuth", "FhirError"]
