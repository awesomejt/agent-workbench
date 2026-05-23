# Prometheus Metrics

Optional metrics endpoint for Agent Workbench API.

## Status

**Planned — not yet implemented.** The endpoint and dependencies described here are the intended design. Track implementation progress in [TODO.md](../TODO.md) under "Scaffolding".

## Planned Design

When enabled, the API exposes a `/metrics` endpoint in Prometheus exposition format. All existing HTTP and database instrumentation will be opt-in via environment variable.

### Enabling

```bash
PROMETHEUS_ENABLED=true
```

Add to `api/.env` (local) or inject at runtime (non-local). The default is `false` — the endpoint is not registered unless explicitly enabled.

### Dependencies (planned)

```toml
# api/pyproject.toml additions
prometheus-flask-exporter = ">=0.23"
```

### Default Metrics

Once enabled, the endpoint will expose standard Flask and WSGI metrics:

| Metric | Description |
|---|---|
| `flask_http_request_duration_seconds` | Request latency by method, path, status |
| `flask_http_request_total` | Request count by method, path, status |
| `flask_http_request_exceptions_total` | Unhandled exception count |

Custom metrics planned for agent coordination visibility:

| Metric | Description |
|---|---|
| `awb_task_claims_total` | Task claims by project, agent |
| `awb_task_completions_total` | Task completions by project, agent |
| `awb_active_leases` | Tasks with an unexpired lease |
| `awb_run_duration_seconds` | Run duration histogram |

## Prometheus Scrape Config

Jason's Prometheus instance is at `prometheus.taylor.lan`. When the endpoint is deployed, add this scrape job:

```yaml
scrape_configs:
  - job_name: agent-workbench
    static_configs:
      - targets: ['<api-host>:8000']
    metrics_path: /metrics
    scrape_interval: 30s
```

Replace `<api-host>` with the Docker Compose VM hostname or IP.

## Grafana

No dashboard is planned yet. After the endpoint is deployed, a Grafana panel on the existing `grafana.taylor.lan` instance can visualize active leases, claim rates, and run durations.

## Security Note

The `/metrics` endpoint exposes operational data and should not be publicly accessible. Restrict it via Nginx or Traefik to the internal network or Prometheus scrape subnet only.
