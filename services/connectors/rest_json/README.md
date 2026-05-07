# rest_json — generic REST/JSON client demo

Demonstrates the **generic REST/JSON** integration pattern from the
registry (`conn.rest` in
[`data/connectors/connectors.yaml`](../../../data/connectors/connectors.yaml)).
This is the most common way modern SaaS APIs are integrated — Stripe,
Salesforce, HubSpot, Snowflake, and most homegrown services all sit
behind this shape.

## What's here

```
rest_json/
├── __init__.py    # re-exports RestJsonClient, OAuth2ClientCredentials, RetryPolicy
├── client.py      # client + OAuth helper + retry + pagination + JSON Schema
├── examples.py    # runnable: python -m services.connectors.rest_json.examples
└── README.md      # you are here
```

## What it does

| Surface                                    | Notes                                              |
| ------------------------------------------ | -------------------------------------------------- |
| `client.get/post/put/patch/delete(...)`    | Returns a `RestResponse` with `.status`, `.body`.  |
| `OAuth2ClientCredentials`                  | client_credentials grant + auto-refresh.           |
| `RetryPolicy(max_attempts, backoff_factor)`| Tenacity-style decorator on retryable status codes.|
| `client.paginate(path, ...)`               | Yields items across pages (cursor or numeric).     |
| `validate_json_schema(payload, schema)`    | Lightweight JSON Schema validation hook.           |

The canned API behind `RestJsonClient` is a tiny "Customer 360" service
with 30 records, paginated 10 per page. Use it to sanity-check your
pagination loop, OAuth token refresh, and schema validation wiring.

## Production swap-out

The expected production stack is:

- **`httpx`** — async-friendly modern HTTP client.
  ```python
  import httpx
  with httpx.Client(base_url="https://api.example.org/v1",
                    headers={"Authorization": "Bearer ..."}) as c:
      r = c.get("/customers")
      r.raise_for_status()
      data = r.json()
  ```
- **`tenacity`** — battle-tested retry library with a similar decorator
  shape:
  ```python
  from tenacity import retry, stop_after_attempt, wait_exponential
  @retry(stop=stop_after_attempt(5),
         wait=wait_exponential(multiplier=0.5, max=8))
  def fetch_page(...): ...
  ```
- **`jsonschema`** (or `pydantic` for typed models) — full JSON Schema
  Draft 2020-12 validation.

The shape of `client.get()` and `client.paginate()` matches the
ergonomic surface of httpx + tenacity, so swap-out is mostly mechanical.

## Why this is a stub

Every payer/provider, fintech, and SaaS connector built on REST starts
with the same skeleton: auth → retry → paginate → validate. This stub
exists to give that skeleton concrete code that other subdomain demos
can import and exercise without standing up a real auth server.
