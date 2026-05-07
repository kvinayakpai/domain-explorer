"""Runnable demonstration of :class:`RestJsonClient`.

::

    python -m services.connectors.rest_json.examples

Exercises the client against a canned "Customer 360" REST API:

1. OAuth2 client-credentials token negotiation.
2. Paginating through 3 pages of customers.
3. Forcing a token refresh between calls.
4. JSON Schema validation against a typed customer schema.
"""

from __future__ import annotations

import json

from .client import (
    OAuth2ClientCredentials,
    RestJsonClient,
    RetryPolicy,
    validate_json_schema,
)


def _banner(title: str) -> None:
    bar = "=" * len(title)
    print(f"\n{bar}\n{title}\n{bar}")


CUSTOMER_SCHEMA = {
    "type": "object",
    "required": ["id", "name", "tier", "country"],
    "properties": {
        "id":      {"type": "string"},
        "name":    {"type": "string"},
        "tier":    {"type": "string"},
        "country": {"type": "string"},
    },
}


def main() -> None:
    oauth = OAuth2ClientCredentials(
        token_url="https://auth.example.org/oauth2/token",
        client_id="customer-360-client",
        client_secret="<not-used>",
        scope="customers.read customers.write",
    )

    client = RestJsonClient(
        base_url="https://api.customer360.example.org/v1",
        oauth2=oauth,
        default_headers={"X-Tenant-Id": "demo-tenant"},
        retry=RetryPolicy(max_attempts=3, initial_delay_s=0.0, backoff_factor=2.0),
    )

    _banner("Initial token")
    print(f"  bearer = {oauth.access_token()}")

    _banner("Health check")
    resp = client.get("/health")
    print(f"  status={resp.status}  body={resp.body}")

    _banner("Paginate /customers (page_size=10) across 3 pages")
    seen = []
    for c in client.paginate("/customers", query={"page_size": 10}, items_key="items",
                              next_key="next_page", max_pages=10):
        seen.append(c)
    print(f"  total customers received: {len(seen)}")
    for c in seen[:3]:
        print(f"  - {c['id']}  {c['name']:30s}  tier={c['tier']:6s}  country={c['country']}")
    print("  ...")
    for c in seen[-2:]:
        print(f"  - {c['id']}  {c['name']:30s}  tier={c['tier']:6s}  country={c['country']}")

    _banner("Force OAuth token refresh, then GET /customers/C00001")
    new_token = oauth.access_token(force_refresh=True)
    print(f"  new bearer = {new_token}")
    resp = client.get("/customers/C00001")
    resp.raise_for_status()
    print(json.dumps(resp.body, indent=2))

    _banner("JSON Schema validation against the customer payload")
    errors = validate_json_schema(resp.body, CUSTOMER_SCHEMA)
    print(f"  validation errors: {errors!r}")

    _banner("Validation should flag a missing required key")
    bad = {"id": "C99999", "name": "Missing Tier"}
    print(f"  payload: {bad}")
    errors = validate_json_schema(bad, CUSTOMER_SCHEMA)
    for e in errors:
        print(f"  - {e}")


if __name__ == "__main__":
    main()
