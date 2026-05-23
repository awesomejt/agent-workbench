from __future__ import annotations

import time
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from flask import Flask

try:
    import prometheus_client as _prom

    _AVAILABLE = True
except ImportError:
    _prom = None  # type: ignore[assignment]
    _AVAILABLE = False

# Lazily created on first setup_metrics() call; shared across app instances.
_registry: dict = {}


def setup_metrics(app: Flask) -> None:
    """Register Prometheus metrics collection and /metrics route on app.

    Guarded by PROMETHEUS_ENABLED config; no-op (with a warning) if
    prometheus-client is not installed.
    """
    from flask import Response, g, request

    if not _AVAILABLE:
        app.logger.warning("prometheus_client not installed; install agent-workbench[prometheus]")

        @app.get("/metrics")
        def metrics_unavailable() -> Response:
            return Response(
                "# prometheus_client not installed\n", status=503, mimetype="text/plain"
            )

        return

    if not _registry:
        _registry["request_count"] = _prom.Counter(
            "http_requests_total",
            "Total HTTP requests",
            ["method", "endpoint", "status"],
        )
        _registry["request_latency"] = _prom.Histogram(
            "http_request_duration_seconds",
            "HTTP request latency in seconds",
            ["method", "endpoint"],
        )

    request_count = _registry["request_count"]
    request_latency = _registry["request_latency"]

    @app.before_request
    def _start_timer() -> None:
        g._prom_start = time.monotonic()

    @app.after_request
    def _record_request(response):
        endpoint = request.endpoint or "unknown"
        elapsed = time.monotonic() - getattr(g, "_prom_start", time.monotonic())
        request_count.labels(request.method, endpoint, response.status_code).inc()
        request_latency.labels(request.method, endpoint).observe(elapsed)
        return response

    @app.get("/metrics")
    def metrics() -> Response:
        return Response(_prom.generate_latest(), mimetype=_prom.CONTENT_TYPE_LATEST)
