"""Generic REST/JSON client demo stub.

Emulates the most common surface area of a production REST client
without making real network calls:

* `get` / `post` / `put` / `patch` / `delete` returning `RestResponse`.
* OAuth2 client-credentials helper (`OAuth2ClientCredentials`).
* `RetryPolicy` decorator for exponential-backoff retries (no actual
  `tenacity` dependency).
* `paginate(...)` iterator for cursor- and page-style pagination.
* JSON-Schema validation hook (lightweight in-process implementation —
  not full Draft 2020-12, but enough to demonstrate the wiring).

Production swap-out::

    import httpx
    from tenacity import retry, stop_after_attempt, wait_exponential
    from jsonschema import Draft202012Validator

    @retry(stop=stop_after_attempt(5),
           wait=wait_exponential(multiplier=0.5, max=8))
    def fetch(client, url):
        r = client.get(url)
        r.raise_for_status()
        return r.json()
"""

from __future__ import annotations

import copy
import time
from dataclasses import dataclass, field
from typing import (
    Any,
    Callable,
    Dict,
    Iterator,
    List,
    Mapping,
    Optional,
    Tuple,
)


# -- exceptions ---------------------------------------------------------------


class RestError(Exception):
    """Base error for the demo REST client."""

    def __init__(self, status: int, body: Any, url: str = "") -> None:
        self.status = status
        self.body = body
        self.url = url
        super().__init__(f"REST {status} on {url or '<no-url>'}: {body}")


# -- response container ------------------------------------------------------


@dataclass
class RestResponse:
    """Returned from every HTTP-method call. Mirrors httpx.Response shape."""

    status: int
    headers: Dict[str, str]
    body: Any
    url: str = ""

    @property
    def ok(self) -> bool:
        return 200 <= self.status < 300

    def raise_for_status(self) -> None:
        if not self.ok:
            raise RestError(self.status, self.body, self.url)


# -- OAuth2 client-credentials helper ----------------------------------------


@dataclass
class OAuth2ClientCredentials:
    """Trivial client_credentials grant helper.

    The real flow POSTs ``grant_type=client_credentials`` to the token
    endpoint and exchanges client id/secret for a bearer token. This
    stub returns a synthetic token signed with a counter so the demo
    can show "refresh" behaviour deterministically.
    """

    token_url: str
    client_id: str
    client_secret: str = field(repr=False)
    scope: Optional[str] = None
    _token: Optional[str] = field(default=None, init=False, repr=False)
    _expires_at: float = field(default=0.0, init=False, repr=False)
    _refresh_counter: int = field(default=0, init=False, repr=False)

    def access_token(self, force_refresh: bool = False) -> str:
        if force_refresh or self._token is None or time.time() >= self._expires_at:
            self._refresh_counter += 1
            scope = (self.scope or "default").replace(" ", "_")
            self._token = (
                f"stub.{self.client_id}.{scope}.v{self._refresh_counter}"
            )
            # Pretend tokens last 1 hour.
            self._expires_at = time.time() + 3600
        return self._token

    def auth_header(self) -> Dict[str, str]:
        return {"Authorization": f"Bearer {self.access_token()}"}


# -- retry policy ------------------------------------------------------------


@dataclass
class RetryPolicy:
    """Exponential-backoff retry decorator. Inspired by tenacity, no dep."""

    max_attempts: int = 3
    initial_delay_s: float = 0.0
    backoff_factor: float = 2.0
    retry_on: Tuple[int, ...] = (429, 500, 502, 503, 504)

    def __call__(self, fn: Callable[..., RestResponse]) -> Callable[..., RestResponse]:
        def wrapper(*args: Any, **kwargs: Any) -> RestResponse:
            delay = self.initial_delay_s
            last_error: Optional[BaseException] = None
            for attempt in range(1, self.max_attempts + 1):
                try:
                    response = fn(*args, **kwargs)
                except RestError as exc:
                    last_error = exc
                    if exc.status not in self.retry_on or attempt == self.max_attempts:
                        raise
                else:
                    if response.status not in self.retry_on or attempt == self.max_attempts:
                        return response
                if delay > 0:
                    time.sleep(delay)
                delay = max(self.initial_delay_s, delay * self.backoff_factor)
            assert last_error is not None  # for type checkers
            raise last_error
        return wrapper


# -- JSON Schema validation (tiny subset) ------------------------------------


def validate_json_schema(payload: Any, schema: Mapping[str, Any]) -> List[str]:
    """Return a list of validation errors. Empty list = valid.

    Supports just enough of JSON Schema (Draft 2020-12) to demonstrate
    the integration shape: ``type``, ``required``, ``properties``,
    ``items``. Real production code should call out to ``jsonschema``.
    """
    errors: List[str] = []
    _walk(payload, schema, "", errors)
    return errors


_TYPE_MAP = {
    "object": dict,
    "array": list,
    "string": str,
    "number": (int, float),
    "integer": int,
    "boolean": bool,
    "null": type(None),
}


def _walk(value: Any, schema: Mapping[str, Any], path: str, errors: List[str]) -> None:
    expected = schema.get("type")
    if expected is not None:
        py = _TYPE_MAP.get(expected)
        if py is not None and not isinstance(value, py):
            errors.append(f"{path or '<root>'}: expected {expected}, got {type(value).__name__}")
            return
    if expected == "object" or isinstance(value, dict):
        required = schema.get("required") or []
        props = schema.get("properties") or {}
        if isinstance(value, dict):
            for r in required:
                if r not in value:
                    errors.append(f"{path or '<root>'}: missing required key {r!r}")
            for k, v in value.items():
                if k in props:
                    _walk(v, props[k], f"{path}.{k}" if path else k, errors)
    if expected == "array" or isinstance(value, list):
        items_schema = schema.get("items")
        if items_schema and isinstance(value, list):
            for i, item in enumerate(value):
                _walk(item, items_schema, f"{path}[{i}]", errors)


# -- canned routes -----------------------------------------------------------


# A tiny "Customer 360" REST API. Three pages of customers, plus a single
# customer endpoint and an idempotent POST /customers that returns a body
# echoing the input plus a server-assigned id.
_CUSTOMERS = [
    {"id": f"C{n:05d}", "name": f"Customer {n}", "tier": ("gold" if n % 7 == 0 else "silver"),
     "country": ("US" if n % 2 == 0 else "GB")}
    for n in range(1, 31)
]


def _route_get_customer(path: str, query: Dict[str, str]) -> RestResponse:
    parts = path.split("/")
    if len(parts) >= 3 and parts[1] == "customers":
        if len(parts) == 2 or (len(parts) == 3 and parts[2] == ""):
            return _route_list_customers(query)
        cid = parts[2]
        for c in _CUSTOMERS:
            if c["id"] == cid:
                return RestResponse(200, {"Content-Type": "application/json"}, dict(c))
        return RestResponse(404, {}, {"error": "not_found", "id": cid})
    if path == "/health":
        return RestResponse(200, {"Content-Type": "application/json"}, {"status": "ok"})
    return RestResponse(404, {}, {"error": "no_route", "path": path})


def _route_list_customers(query: Mapping[str, str]) -> RestResponse:
    page_size = int(query.get("page_size", "10"))
    page = int(query.get("page", "1"))
    start = (page - 1) * page_size
    end = start + page_size
    items = [dict(c) for c in _CUSTOMERS[start:end]]
    next_page = page + 1 if end < len(_CUSTOMERS) else None
    body = {
        "items": items,
        "page": page,
        "page_size": page_size,
        "total": len(_CUSTOMERS),
        "next_page": next_page,
    }
    return RestResponse(200, {"Content-Type": "application/json"}, body)


# -- client ------------------------------------------------------------------


@dataclass
class RestJsonClient:
    """Minimal demo REST/JSON client.

    Constructor parameters mirror httpx.Client's ergonomics. ``oauth2``
    is optional; if supplied, every outbound request gets a Bearer token
    refreshed automatically when expired.
    """

    base_url: str
    oauth2: Optional[OAuth2ClientCredentials] = None
    default_headers: Dict[str, str] = field(default_factory=dict)
    retry: Optional[RetryPolicy] = None
    timeout_s: float = 10.0

    # --- low-level helpers ---

    def _request_headers(self, extra: Optional[Mapping[str, str]] = None) -> Dict[str, str]:
        h = {"Accept": "application/json", "User-Agent": "domain-explorer-stub/0.1"}
        if self.oauth2:
            h.update(self.oauth2.auth_header())
        h.update(self.default_headers)
        if extra:
            h.update(extra)
        return h

    def _absolute(self, path: str) -> str:
        if path.startswith(("http://", "https://")):
            return path
        return self.base_url.rstrip("/") + "/" + path.lstrip("/")

    def _dispatch(
        self,
        method: str,
        path: str,
        query: Optional[Mapping[str, Any]] = None,
        body: Optional[Any] = None,
        headers: Optional[Mapping[str, str]] = None,
    ) -> RestResponse:
        url = self._absolute(path)
        # Force header build so the auth path is exercised.
        _ = self._request_headers(headers)
        path_only = "/" + url.split("//", 1)[-1].split("/", 1)[-1] if "//" in url else url
        if not path_only.startswith("/"):
            path_only = "/" + path_only
        q = {k: str(v) for k, v in (query or {}).items()}

        if method == "GET":
            resp = _route_get_customer(path_only, q)
        elif method in ("POST", "PUT", "PATCH"):
            if path_only == "/customers":
                if not isinstance(body, dict):
                    return RestResponse(422, {}, {"error": "body_must_be_object"})
                created = copy.deepcopy(body)
                created["id"] = f"C{len(_CUSTOMERS) + 1:05d}"
                return RestResponse(201, {"Content-Type": "application/json"}, created)
            resp = RestResponse(404, {}, {"error": "no_route", "path": path_only})
        elif method == "DELETE":
            resp = RestResponse(204, {}, None)
        else:
            resp = RestResponse(405, {}, {"error": "method_not_allowed", "method": method})
        resp.url = url
        return resp

    # --- public API ---

    def get(self, path: str, query: Optional[Mapping[str, Any]] = None,
            headers: Optional[Mapping[str, str]] = None) -> RestResponse:
        fn = self._dispatch
        if self.retry is not None:
            fn = self.retry(fn)
        return fn("GET", path, query=query, headers=headers)

    def post(self, path: str, body: Any,
             headers: Optional[Mapping[str, str]] = None) -> RestResponse:
        return self._dispatch("POST", path, body=body, headers=headers)

    def put(self, path: str, body: Any,
            headers: Optional[Mapping[str, str]] = None) -> RestResponse:
        return self._dispatch("PUT", path, body=body, headers=headers)

    def patch(self, path: str, body: Any,
              headers: Optional[Mapping[str, str]] = None) -> RestResponse:
        return self._dispatch("PATCH", path, body=body, headers=headers)

    def delete(self, path: str,
               headers: Optional[Mapping[str, str]] = None) -> RestResponse:
        return self._dispatch("DELETE", path, headers=headers)

    # --- pagination ---

    def paginate(
        self,
        path: str,
        query: Optional[Mapping[str, Any]] = None,
        items_key: str = "items",
        next_key: str = "next_page",
        page_param: str = "page",
        max_pages: int = 100,
    ) -> Iterator[Dict[str, Any]]:
        """Yield items across pages until ``next_page`` is null or
        ``max_pages`` is reached. Honours either cursor-style or numeric
        page-style pagination depending on what the server returns."""
        q = dict(query or {})
        page = q.get(page_param, 1)
        for _ in range(max_pages):
            q[page_param] = page
            r = self.get(path, query=q)
            r.raise_for_status()
            payload = r.body if isinstance(r.body, dict) else {}
            for item in payload.get(items_key, []):
                yield item
            nxt = payload.get(next_key)
            if nxt is None:
                return
            page = nxt
