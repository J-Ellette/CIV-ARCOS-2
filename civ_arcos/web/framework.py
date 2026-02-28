"""Custom web framework built on http.server."""
import json
import re
import traceback
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any, Callable, Dict, List, Optional, Tuple
from urllib.parse import parse_qs, urlparse


class Request:
    """HTTP request wrapper."""
    def __init__(self, method: str, path: str, query_params: Dict[str, List[str]],
                 body: bytes, headers: Dict[str, str]) -> None:
        self.method = method
        self.path = path
        self.query_params = query_params
        self.body = body
        self.headers = headers
        self._json: Any = None

    def json(self) -> Any:
        if self._json is None and self.body:
            self._json = json.loads(self.body.decode())
        return self._json

    def query(self, key: str, default: str = "") -> str:
        vals = self.query_params.get(key, [default])
        return vals[0] if vals else default


class Response:
    """HTTP response wrapper."""
    def __init__(self, body: Any = None, status_code: int = 200,
                 content_type: str = "application/json",
                 headers: Optional[Dict[str, str]] = None) -> None:
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
        regex = re.sub(r"\{(\w+)\}", lambda m: (param_names.append(m.group(1)) or "") + r"([^/]+)", pattern)
        self._routes.append((method.upper(), re.compile(f"^{regex}$"), handler, param_names))

    def match(self, method: str, path: str) -> Tuple[Optional[Callable], Dict[str, str]]:
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

    def handle(self, method: str, path: str, query_params: Dict[str, List[str]],
               body: bytes, headers: Dict[str, str]) -> Response:
        handler, path_params = self._router.match(method, path)
        if handler is None:
            return Response({"error": "Not Found"}, status_code=404)
        try:
            req = Request(method, path, query_params, body, headers)
            req.path_params = path_params  # type: ignore[attr-defined]
            result = handler(req, **path_params)
            if isinstance(result, Response):
                return result
            return Response(result)
        except Exception as exc:
            traceback.print_exc()
            return Response({"error": str(exc)}, status_code=500)

    def create_handler(self) -> type:
        app = self

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self): self._handle("GET")
            def do_POST(self): self._handle("POST")
            def do_PUT(self): self._handle("PUT")
            def do_DELETE(self): self._handle("DELETE")

            def _handle(self, method: str) -> None:
                parsed = urlparse(self.path)
                query_params = parse_qs(parsed.query)
                length = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(length) if length else b""
                headers = {k: v for k, v in self.headers.items()}
                response = app.handle(method, parsed.path, query_params, body, headers)
                self.send_response(response.status_code)
                self.send_header("Content-Type", response.content_type)
                self.send_header("Access-Control-Allow-Origin", "*")
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
