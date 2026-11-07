"""Connector configuration and credentials for pointing the agents at real systems.

The agents read through `agents.sources.HttpSource`, which already speaks the real dialects (PI Web API,
SAP OData v2, OSDU search and storage, REST for PLM/MES/QMS) and handles their behaviour: retries with
back-off, token refresh, server-driven paging, SAP CSRF tokens and OSDU data partitions. What changes for a
pilot is configuration and credentials, kept here:

- `ClientCredentials`: an OAuth2 client-credentials client (the agent's service identity) that caches the
  access token and refreshes it before expiry or when a system answers 401;
- `SystemConfig` and `load_config()`: one entry per system in a YAML file (base URL, token URL, client id,
  the environment variable that holds the secret, OSDU data partition);
- `source_for()`: the configured `HttpSource` for one system.

Secrets never live in the file: each entry names the environment variable that holds them.
"""
from __future__ import annotations

import json
import os
import time
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import jwt
import yaml

from ..agents.sources import HttpSource

EXAMPLE_CONFIG = Path(__file__).resolve().parent / "connectors.example.yaml"


class ClientCredentials:
    """OAuth2 client-credentials token provider with caching and refresh."""

    def __init__(self, token_url: str, client_id: str, secret: str, scope: str = "plant.read", skew_s: int = 60) -> None:
        self.token_url, self.client_id, self.secret, self.scope, self.skew_s = token_url, client_id, secret, scope, skew_s
        self._token: str | None = None
        self._exp = 0.0
        self.fetches = 0

    def _fetch(self) -> None:
        data = urllib.parse.urlencode({"grant_type": "client_credentials", "client_id": self.client_id,
                                       "client_secret": self.secret, "scope": self.scope}).encode()
        req = urllib.request.Request(self.token_url, data=data, headers={"Content-Type": "application/x-www-form-urlencoded"})
        with urllib.request.urlopen(req, timeout=15) as r:
            body = json.loads(r.read())
        self._token = body["access_token"]
        claims = jwt.decode(self._token, options={"verify_signature": False})
        self._exp = float(claims.get("exp", time.time() + int(body.get("expires_in", 300))))
        self.fetches += 1

    def token(self) -> str:
        if self._token is None or time.time() > self._exp - self.skew_s:
            self._fetch()
        assert self._token is not None
        return self._token

    def refresh(self) -> None:
        self._fetch()


@dataclass(frozen=True)
class SystemConfig:
    name: str
    base_url: str
    token_url: str
    client_id: str
    secret_env: str
    scope: str = "plant.read"
    partition: str = "aurelia"

    def secret(self) -> str:
        v = os.environ.get(self.secret_env)
        if not v:
            raise RuntimeError(f"{self.name}: set {self.secret_env} to the client secret (secrets are never stored in the config file)")
        return v


def load_config(path: Path = EXAMPLE_CONFIG) -> dict[str, SystemConfig]:
    raw: dict[str, Any] = yaml.safe_load(path.read_text())
    return {name: SystemConfig(name=name, **entry) for name, entry in raw["systems"].items()}


def source_for(cfg: SystemConfig) -> HttpSource:
    auth = ClientCredentials(cfg.token_url, cfg.client_id, cfg.secret(), cfg.scope)
    return HttpSource(cfg.base_url, token=auth, partition=cfg.partition)
