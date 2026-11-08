"""Identity provider simulator (OIDC-style) for approvers, reviewers and the agent's service client.

A real pilot points at the company's identity provider (Entra ID, Okta, Ping) with the authorization-code
flow and PKCE; this simulator issues the same kind of artefact, an RS256-signed JWT, so the rest of the code
is written against signatures and claims rather than typed names:

- people sign in with a username and password and get a token whose claims carry their name and roles;
- the agent's service client gets a token with scope `plant.read` only (client credentials grant);
- resource servers (the plant-system simulators, the console) verify tokens against `/oauth2/jwks`.

The directory and passwords are demo data. Keys are generated per process.
"""
from __future__ import annotations

import json
import threading
import time
import urllib.parse
import uuid
from dataclasses import dataclass, field
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

import jwt
from cryptography.hazmat.primitives.asymmetric import rsa

AUDIENCE = "factory-to-field"


@dataclass(frozen=True)
class Person:
    name: str
    roles: tuple[str, ...]
    password: str
    tenant: str = "operator"     # which organisation employs them: the refinery/field operator (primary) or the pump maker (secondary)


DIRECTORY: dict[str, Person] = {
    "a.rao": Person("A. Rao", ("maintenance_planner",), "demo-a.rao"),
    "s.iyer": Person("S. Iyer", ("materials_planner",), "demo-s.iyer"),
    "m.das": Person("M. Das", ("quality_engineer",), "demo-m.das", tenant="maker"),
    "r.menon": Person("R. Menon", ("quality_manager", "quality_engineer"), "demo-r.menon", tenant="maker"),
    "k.nair": Person("K. Nair", ("production_engineer",), "demo-k.nair"),
    "t.fernandes": Person("T. Fernandes", ("shift_supervisor",), "demo-t.fernandes"),
    "p.kulkarni": Person("P. Kulkarni", ("data_steward",), "demo-p.kulkarni"),
}
CLIENTS: dict[str, dict[str, Any]] = {
    # legacy all-systems reader, kept for older tests and demos; new work should use one of the two tenant agents
    "ftf-agent": {"secret": "demo-agent-secret", "scopes": ("plant.read",), "tenant": "operator"},
    # primary: the operator's agent reads the operator's systems (SAP PM, historian, SCADA, OSDU, P&ID, production) and nothing of the maker's
    "ftf-operator-agent": {"secret": "demo-operator-agent-secret", "scopes": ("operator.read",), "tenant": "operator"},
    # secondary: the pump maker's own agent reads the maker's systems (PLM, MES, QMS) and nothing of the operator's
    "ftf-maker-agent": {"secret": "demo-maker-agent-secret", "scopes": ("maker.read",), "tenant": "maker"},
}


@dataclass
class IdentityProvider:
    issuer: str = "https://idp.aurelia.example"
    ttl_s: int = 900
    directory: dict[str, Person] = field(default_factory=lambda: dict(DIRECTORY))
    clients: dict[str, dict[str, Any]] = field(default_factory=lambda: dict(CLIENTS))

    def __post_init__(self) -> None:
        self._key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        self.kid = uuid.uuid4().hex[:16]

    # -- issuing
    def _sign(self, claims: dict[str, Any]) -> str:
        now = int(time.time())
        body = {"iss": self.issuer, "aud": AUDIENCE, "iat": now, "nbf": now, "exp": now + self.ttl_s, "jti": uuid.uuid4().hex, **claims}
        return jwt.encode(body, self._key, algorithm="RS256", headers={"kid": self.kid})

    def login(self, username: str, password: str) -> str:
        p = self.directory.get(username)
        if p is None or password != p.password:
            raise PermissionError("unknown user or wrong password")
        return self._sign({"sub": username, "name": p.name, "roles": list(p.roles), "scope": "drafts.decide", "tenant": p.tenant})

    def client_credentials(self, client_id: str, secret: str, scope: str = "plant.read") -> str:
        c = self.clients.get(client_id)
        if c is None or secret != c["secret"]:
            raise PermissionError("unknown client or wrong secret")
        wanted = set(scope.split())
        if not wanted <= set(c["scopes"]):
            raise PermissionError(f"client {client_id} may not request {sorted(wanted - set(c['scopes']))}")
        return self._sign({"sub": client_id, "client_id": client_id, "scope": " ".join(sorted(wanted)), "tenant": c.get("tenant", "operator")})

    # -- verifying (resource servers do the same with the JWKS)
    def jwks(self) -> dict[str, Any]:
        jwk = json.loads(jwt.algorithms.RSAAlgorithm.to_jwk(self._key.public_key()))
        jwk.update({"kid": self.kid, "alg": "RS256", "use": "sig"})
        return {"keys": [jwk]}

    def verify(self, token: str) -> dict[str, Any]:
        return verify_with_jwks(token, self.jwks(), self.issuer)


def verify_with_jwks(token: str, jwks: dict[str, Any], issuer: str) -> dict[str, Any]:
    """Check signature, issuer, audience and expiry. Raises PermissionError with a readable reason."""
    try:
        kid = jwt.get_unverified_header(token).get("kid")
        key = next(k for k in jwks["keys"] if k["kid"] == kid)
        public = jwt.algorithms.RSAAlgorithm.from_jwk(json.dumps(key))
        return jwt.decode(token, public, algorithms=["RS256"], audience=AUDIENCE, issuer=issuer)
    except StopIteration as e:
        raise PermissionError("token signed with an unknown key") from e
    except jwt.ExpiredSignatureError as e:
        raise PermissionError("token expired") from e
    except jwt.PyJWTError as e:
        raise PermissionError(f"invalid token: {e}") from e


class JwksVerifier:
    """What a resource server holds: the issuer and its published keys, refreshed on an unknown kid."""

    def __init__(self, idp_url: str, issuer: str) -> None:
        self.idp_url, self.issuer = idp_url.rstrip("/"), issuer
        self._jwks: dict[str, Any] | None = None

    def _fetch(self) -> dict[str, Any]:
        import urllib.request
        with urllib.request.urlopen(f"{self.idp_url}/oauth2/jwks", timeout=10) as r:
            return json.loads(r.read())

    def verify(self, token: str) -> dict[str, Any]:
        if self._jwks is None:
            self._jwks = self._fetch()
        try:
            return verify_with_jwks(token, self._jwks, self.issuer)
        except PermissionError as e:
            if "unknown key" not in str(e):
                raise
            self._jwks = self._fetch()
            return verify_with_jwks(token, self._jwks, self.issuer)


def make_handler(idp: IdentityProvider):
    class H(BaseHTTPRequestHandler):
        def log_message(self, *a: Any) -> None:
            pass

        def _send(self, code: int, body: dict[str, Any]) -> None:
            raw = json.dumps(body).encode()
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)

        def do_GET(self) -> None:
            if self.path == "/.well-known/openid-configuration":
                base = f"http://{self.headers.get('Host')}"
                return self._send(200, {"issuer": idp.issuer, "jwks_uri": f"{base}/oauth2/jwks", "token_endpoint": f"{base}/oauth2/token",
                                        "grant_types_supported": ["password", "client_credentials"], "id_token_signing_alg_values_supported": ["RS256"]})
            if self.path == "/oauth2/jwks":
                return self._send(200, idp.jwks())
            self._send(404, {"error": "not found"})

        def do_POST(self) -> None:
            if self.path != "/oauth2/token":
                return self._send(404, {"error": "not found"})
            n = int(self.headers.get("Content-Length") or 0)
            form = {k: v[0] for k, v in urllib.parse.parse_qs(self.rfile.read(n).decode()).items()}
            try:
                if form.get("grant_type") == "password":
                    tok = idp.login(form.get("username", ""), form.get("password", ""))
                elif form.get("grant_type") == "client_credentials":
                    tok = idp.client_credentials(form.get("client_id", ""), form.get("client_secret", ""), form.get("scope", "plant.read"))
                else:
                    return self._send(400, {"error": "unsupported_grant_type"})
            except PermissionError as e:
                return self._send(401, {"error": "invalid_grant", "error_description": str(e)})
            self._send(200, {"access_token": tok, "token_type": "Bearer", "expires_in": idp.ttl_s})
    return H


def serve_in_thread(idp: IdentityProvider | None = None, port: int = 0) -> tuple[ThreadingHTTPServer, str, IdentityProvider]:
    idp = idp or IdentityProvider()
    srv = ThreadingHTTPServer(("127.0.0.1", port), make_handler(idp))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, f"http://127.0.0.1:{srv.server_address[1]}", idp
