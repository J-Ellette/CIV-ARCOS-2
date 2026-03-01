"""Custom web framework built on http.server."""

import json
import logging
import os
import re
import time
import traceback
import uuid
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any, Callable, Dict, List, Optional, Tuple
from urllib.parse import parse_qs, urlparse

# Module-level structured logger (JSON lines to stderr).
_logger = logging.getLogger("civ_arcos.web")


def _default_security_headers() -> Dict[str, str]:
    """Return baseline secure HTTP response headers.

    The values are intentionally conservative and can be extended via
    environment configuration where needed.
    """
    headers = {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "Referrer-Policy": "no-referrer",
        "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
        "Content-Security-Policy": (
            "default-src 'self'; frame-ancestors 'none'; "
            "base-uri 'self'; object-src 'none'"
        ),
    }
    if os.environ.get("CIV_ENABLE_HSTS", "false").lower() == "true":
        headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return headers


def _cors_allow_origin() -> str:
    """Resolve CORS allow-origin policy from environment."""
    return os.environ.get("CIV_CORS_ALLOW_ORIGIN", "*").strip() or "*"


def _make_correlation_id() -> str:
    """Generate a short, unique correlation ID for a request."""
    return uuid.uuid4().hex[:16]


def _log_request(
    correlation_id: str,
    method: str,
    path: str,
    status_code: int,
    duration_ms: float,
) -> None:
    """Emit a single structured JSON log line per HTTP request.

    Parameters
    ----------
    correlation_id:
        Unique ID for this request (propagated via X-Correlation-ID header).
    method:
        HTTP verb (GET, POST, …).
    path:
        Request path (without query string).
    status_code:
        HTTP response status.
    duration_ms:
        Wall-clock duration in milliseconds.
    """
    record = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "correlation_id": correlation_id,
        "method": method,
        "path": path,
        "status": status_code,
        "duration_ms": round(duration_ms, 2),
    }
    _logger.info(json.dumps(record))


class Request:
    """HTTP request wrapper."""

    def __init__(
        self,
        method: str,
        path: str,
        query_params: Dict[str, List[str]],
        body: bytes,
        headers: Dict[str, str],
    ) -> None:
        self.method = method
        self.path = path
        self.query_params = query_params
        self.body = body
        self.headers = headers
        self._json: Any = None
        # Correlation ID injected by the HTTP handler layer; may also be set
        # explicitly in tests.
        self.correlation_id: str = ""

    def json(self) -> Any:
        if self._json is None and self.body:
            self._json = json.loads(self.body.decode())
        return self._json

    def query(self, key: str, default: str = "") -> str:
        vals = self.query_params.get(key, [default])
        return vals[0] if vals else default


class Response:
    """HTTP response wrapper."""

    def __init__(
        self,
        body: Any = None,
        status_code: int = 200,
        content_type: str = "application/json",
        headers: Optional[Dict[str, str]] = None,
    ) -> None:
        self.status_code = status_code
        self.content_type = content_type
        self.headers = headers or {}
        if isinstance(body, (dict, list)):
            self.body = json.dumps(body).encode()
            self.content_type = "application/json"
        elif isinstance(body, str):
            self.body = body.encode()
        elif isinstance(body, bytes):
            self.body = body
        else:
            self.body = b""


class Router:
    """URL router with path parameter extraction."""

    def __init__(self) -> None:
        self._routes: List[Tuple[str, re.Pattern, Callable, List[str]]] = []

    def add_route(self, method: str, pattern: str, handler: Callable) -> None:
        param_names: List[str] = []

        def _replace(m: re.Match) -> str:
            param_names.append(m.group(1))
            return r"([^/]+)"

        regex = re.sub(r"\{(\w+)\}", _replace, pattern)
        self._routes.append(
            (method.upper(), re.compile(f"^{regex}$"), handler, param_names)
        )

    def match(
        self, method: str, path: str
    ) -> Tuple[Optional[Callable], Dict[str, str]]:
        for route_method, pattern, handler, param_names in self._routes:
            if route_method != method.upper():
                continue
            m = pattern.match(path)
            if m:
                params = dict(zip(param_names, m.groups()))
                return handler, params
        return None, {}


class Application:
    """WSGI-like application wrapping http.server."""

    def __init__(self) -> None:
        self._router = Router()

    def route(self, path: str, methods: Optional[List[str]] = None):
        """Decorator for route registration."""
        if methods is None:
            methods = ["GET"]

        def decorator(func: Callable) -> Callable:
            for method in methods:
                self._router.add_route(method, path, func)
            return func

        return decorator

    def handle(
        self,
        method: str,
        path: str,
        query_params: Dict[str, List[str]],
        body: bytes,
        headers: Dict[str, str],
        correlation_id: Optional[str] = None,
    ) -> Response:
        """Dispatch a request through the router.

        Parameters
        ----------
        correlation_id:
            Optional pre-assigned correlation ID (used in tests).  When
            omitted a new one is generated automatically.
        """
        corr_id = (
            correlation_id
            or headers.get("X-Correlation-ID")
            or headers.get("x-correlation-id")
            or _make_correlation_id()
        )
        t_start = time.monotonic()
        handler, path_params = self._router.match(method, path)
        if handler is None:
            duration = (time.monotonic() - t_start) * 1000
            _log_request(corr_id, method, path, 404, duration)
            resp = Response({"error": "Not Found"}, status_code=404)
            resp.headers.update(_default_security_headers())
            resp.headers["X-Correlation-ID"] = corr_id
            return resp
        try:
            req = Request(method, path, query_params, body, headers)
            req.path_params = path_params  # type: ignore[attr-defined]
            req.correlation_id = corr_id
            result = handler(req, **path_params)
            resp = result if isinstance(result, Response) else Response(result)
        except Exception as exc:
            traceback.print_exc()
            resp = Response({"error": str(exc)}, status_code=500)
        duration = (time.monotonic() - t_start) * 1000
        _log_request(corr_id, method, path, resp.status_code, duration)
        resp.headers.update(_default_security_headers())
        resp.headers["X-Correlation-ID"] = corr_id
        return resp

    def create_handler(self) -> type:
        app = self

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                self._handle("GET")

            def do_POST(self):
                self._handle("POST")

            def do_PUT(self):
                self._handle("PUT")

            def do_DELETE(self):
                self._handle("DELETE")

            def do_OPTIONS(self):
                self._handle_options()

            def _handle_options(self) -> None:
                """Handle CORS preflight requests."""
                self.send_response(204)
                self.send_header("Access-Control-Allow-Origin", _cors_allow_origin())
                self.send_header(
                    "Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS"
                )
                self.send_header(
                    "Access-Control-Allow-Headers",
                    "Content-Type, Authorization, X-Correlation-ID, "
                    "X-Tenant-ID, Idempotency-Key",
                )
                for k, v in _default_security_headers().items():
                    self.send_header(k, v)
                self.end_headers()

            def _handle(self, method: str) -> None:
                parsed = urlparse(self.path)
                query_params = parse_qs(parsed.query)
                length = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(length) if length else b""
                headers = {k: v for k, v in self.headers.items()}
                # Honour a correlation ID from the caller; otherwise generate one.
                incoming_corr = headers.get("X-Correlation-ID") or headers.get(
                    "x-correlation-id"
                )
                response = app.handle(
                    method,
                    parsed.path,
                    query_params,
                    body,
                    headers,
                    correlation_id=incoming_corr or None,
                )
                self.send_response(response.status_code)
                self.send_header("Content-Type", response.content_type)
                self.send_header("Access-Control-Allow-Origin", _cors_allow_origin())
                for k, v in response.headers.items():
                    self.send_header(k, v)
                self.end_headers()
                self.wfile.write(response.body)

            def log_message(self, fmt: str, *args: Any) -> None:
                pass  # suppress default logging

        return Handler

    def run(self, host: str = "0.0.0.0", port: int = 8080) -> None:
        handler = self.create_handler()
        server = HTTPServer((host, port), handler)
        print(f"CIV-ARCOS API running on http://{host}:{port}")
        server.serve_forever()


def create_app() -> Application:
    """Factory function for Application."""
    return Application()
