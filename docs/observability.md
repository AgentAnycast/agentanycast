# Observability & Monitoring

## Overview

AgentAnycast provides three pillars of observability for production deployments:

- **Metrics** -- Prometheus-compatible metrics exposed via HTTP endpoints on both the node daemon and relay server.
- **Distributed Tracing** -- OpenTelemetry-based tracing with OTLP export and W3C Trace Context propagation across A2A messages.
- **Audit Logging** -- JSON Lines audit trail of all access control decisions for compliance and security analysis.

Both the node daemon (`agentanycastd`) and relay server (`agentanycast-relay`) expose health endpoints for liveness and readiness probes.

## Metrics (Prometheus)

### Node Daemon Metrics

The node daemon exposes Prometheus metrics at `/metrics` when the metrics server is enabled. All metrics use the `agentanycast_` namespace.

**Connection Metrics:**

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `agentanycast_connected_peers` | Gauge | -- | Number of currently connected peers |
| `agentanycast_connections_total` | Counter | `direction` (inbound/outbound) | Total peer connections established |
| `agentanycast_connections_by_transport` | Counter | `transport` (tcp/quic/webtransport) | Connections by transport type |

**Task Metrics:**

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `agentanycast_tasks_total` | Counter | `direction` (sent/received), `status` | Total tasks processed |
| `agentanycast_task_duration_seconds` | Histogram | `direction` | Task processing duration |

**Routing Metrics:**

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `agentanycast_route_resolutions_total` | Counter | `result` (hit/miss/error) | Anycast route resolution attempts |

**Bridge Metrics:**

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `agentanycast_bridge_requests_total` | Counter | `direction` (inbound/outbound), `status` | HTTP bridge requests |

**Streaming Metrics:**

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `agentanycast_stream_chunks_total` | Counter | `direction` | Stream chunks processed |

**Message Metrics:**

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `agentanycast_messages_total` | Counter | `type` | A2A messages by envelope type |
| `agentanycast_offline_queue_size` | Gauge | -- | Messages in the offline queue |

**MCP Metrics:**

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `agentanycast_mcp_tool_calls_total` | Counter | `tool`, `status` (ok/error) | MCP tool invocations |

#### Enabling Metrics on the Node Daemon

Via config file (`~/.agentanycast/config.toml`):

```toml
[metrics]
enabled = true
listen = ":9090"
```

Via environment variable:

```bash
AGENTANYCAST_METRICS_LISTEN=":9090" agentanycastd
```

### Relay Server Metrics

The relay server exposes Prometheus metrics at `/metrics` on the health/metrics listen address (default: `:9090`). In addition to standard Go and process metrics, the relay provides registry-specific data through the `/health` endpoint.

#### Relay Health Response

The `/health` endpoint returns a JSON object with registry statistics:

```json
{
  "status": "healthy",
  "version": "0.8.0",
  "peer_id": "12D3KooW...",
  "uptime_seconds": 3600.5,
  "registry": {
    "total_agents": 42,
    "total_skills": 78
  },
  "federation": {
    "peers": 2,
    "healthy_peers": 2,
    "synced_skills": 156
  },
  "libp2p": {
    "connected_peers": 15
  }
}
```

The `status` field can be:
- `healthy` -- All systems operational.
- `degraded` -- The relay is running but one or more federation peers are unhealthy.
- `unhealthy` -- The relay cannot serve requests.

### Scrape Configuration

Example Prometheus scrape configuration for both daemon and relay:

```yaml
scrape_configs:
  # Node daemon metrics
  - job_name: agentanycast-node
    scrape_interval: 15s
    static_configs:
      - targets: ["localhost:9090"]
        labels:
          instance: "node-1"

  # Relay server metrics
  - job_name: agentanycast-relay
    scrape_interval: 15s
    static_configs:
      - targets: ["relay.example.com:9090"]
        labels:
          instance: "relay-us-east"

  # Multiple relay federation
  - job_name: agentanycast-relay-federation
    scrape_interval: 15s
    static_configs:
      - targets:
          - "relay-us-east.example.com:9090"
          - "relay-eu-west.example.com:9090"
          - "relay-ap-south.example.com:9090"
```

## Distributed Tracing (OpenTelemetry)

AgentAnycast uses OpenTelemetry for distributed tracing, with OTLP gRPC as the export protocol.

### Setup

Enable tracing on the node daemon:

```bash
agentanycastd --otlp-endpoint localhost:4317
```

Or via config file:

```toml
[telemetry]
enabled = true
otlp_endpoint = "localhost:4317"
sample_rate = 1.0     # 0.0-1.0, fraction of traces to sample
insecure = true       # Use plaintext gRPC (default for localhost)
```

Or via environment variables:

```bash
AGENTANYCAST_OTLP_ENDPOINT="localhost:4317" agentanycastd
AGENTANYCAST_SAMPLE_RATE="0.5" agentanycastd  # Sample 50% of traces
```

Enable tracing on the relay server:

```bash
agentanycast-relay --otlp-endpoint localhost:4317
```

### Trace Propagation

Traces are propagated across agent boundaries using W3C Trace Context. The daemon automatically:

1. Creates spans for outbound A2A messages and task operations.
2. Injects `traceparent` and `tracestate` into outbound requests.
3. Extracts trace context from inbound messages to continue the trace.
4. Propagates context through gRPC calls between the SDK and daemon.

The relay server instruments gRPC service handlers with `otelgrpc`, so registry operations (RegisterSkills, DiscoverBySkill, Heartbeat) are automatically traced.

Service names in traces:
- `agentanycast-node` -- The daemon process.
- `agentanycast-relay` -- The relay server.

### Viewing Traces

AgentAnycast traces are compatible with any OTLP-capable backend:

- **Jaeger** -- Deploy the Jaeger all-in-one collector with OTLP support:
  ```bash
  docker run -d --name jaeger \
    -p 4317:4317 \
    -p 16686:16686 \
    jaegertracing/all-in-one:latest
  ```
  Then open `http://localhost:16686` and search for service `agentanycast-node`.

- **Grafana Tempo** -- Configure Tempo as an OTLP receiver and use Grafana to explore traces.

- **OpenTelemetry Collector** -- Deploy the OTel Collector as a pipeline between AgentAnycast and your backend:
  ```yaml
  receivers:
    otlp:
      protocols:
        grpc:
          endpoint: "0.0.0.0:4317"
  exporters:
    otlp:
      endpoint: "tempo.example.com:4317"
  service:
    pipelines:
      traces:
        receivers: [otlp]
        exporters: [otlp]
  ```

## Health Endpoints

### Node Daemon `/health`

Available when the metrics server is enabled. Returns JSON:

```json
{
  "status": "healthy",
  "version": "0.8.0",
  "uptime_seconds": 1234.56
}
```

- **200 OK** -- The node is healthy (connected to peers or no bootstrap peers configured).
- **503 Service Unavailable** -- The node is unhealthy (configured with bootstrap peers but has no active connections).

Use in Kubernetes:

```yaml
livenessProbe:
  httpGet:
    path: /health
    port: 9090
  initialDelaySeconds: 10
  periodSeconds: 15
readinessProbe:
  httpGet:
    path: /health
    port: 9090
  initialDelaySeconds: 5
  periodSeconds: 10
```

### Relay `/health`

Always available on the health/metrics listen address (default: `:9090`). Returns a richer JSON response including registry statistics, federation health, and libp2p peer count (see the Relay Health Response section above).

Use for monitoring:

```bash
# Quick health check
curl -sf http://relay.example.com:9090/health | jq .status

# Detailed health with registry stats
curl -s http://relay.example.com:9090/health | jq '{status, agents: .registry.total_agents, peers: .libp2p.connected_peers}'
```

## Grafana Dashboards

### Relay Overview Dashboard

A sample Grafana dashboard for monitoring an AgentAnycast relay deployment. Save as a JSON provisioning file:

```json
{
  "dashboard": {
    "title": "AgentAnycast Relay Overview",
    "panels": [
      {
        "title": "Connected Peers",
        "type": "stat",
        "targets": [{"expr": "agentanycast_connected_peers"}]
      },
      {
        "title": "Tasks per Second",
        "type": "graph",
        "targets": [{"expr": "rate(agentanycast_tasks_total[5m])"}]
      },
      {
        "title": "Task Duration (p99)",
        "type": "graph",
        "targets": [{"expr": "histogram_quantile(0.99, rate(agentanycast_task_duration_seconds_bucket[5m]))"}]
      },
      {
        "title": "Route Resolution Hit Rate",
        "type": "gauge",
        "targets": [{"expr": "rate(agentanycast_route_resolutions_total{result='hit'}[5m]) / rate(agentanycast_route_resolutions_total[5m])"}]
      },
      {
        "title": "Offline Queue Depth",
        "type": "stat",
        "targets": [{"expr": "agentanycast_offline_queue_size"}]
      },
      {
        "title": "MCP Tool Errors",
        "type": "graph",
        "targets": [{"expr": "rate(agentanycast_mcp_tool_calls_total{status='error'}[5m])"}]
      }
    ]
  }
}
```

Grafana provisioning directory setup:

```bash
mkdir -p /etc/grafana/provisioning/dashboards
# Place the JSON file in this directory and configure the provisioning YAML:
```

```yaml
# /etc/grafana/provisioning/dashboards/agentanycast.yaml
apiVersion: 1
providers:
  - name: AgentAnycast
    folder: AgentAnycast
    type: file
    options:
      path: /etc/grafana/provisioning/dashboards
```

## Alerting

### Recommended Alert Rules

Prometheus alerting rules for critical AgentAnycast conditions:

```yaml
groups:
  - name: agentanycast
    rules:
      # No connected peers for 5 minutes
      - alert: AgentAnycastNoPeers
        expr: agentanycast_connected_peers == 0
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "AgentAnycast node has no connected peers"
          description: "Node {{ $labels.instance }} has had zero peers for 5 minutes."

      # High task failure rate
      - alert: AgentAnycastHighTaskFailureRate
        expr: >
          rate(agentanycast_tasks_total{status="failed"}[5m])
          / rate(agentanycast_tasks_total[5m]) > 0.1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High task failure rate (>10%)"

      # Task latency exceeding threshold
      - alert: AgentAnycastHighTaskLatency
        expr: >
          histogram_quantile(0.99, rate(agentanycast_task_duration_seconds_bucket[5m])) > 10
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Task p99 latency exceeds 10 seconds"

      # Offline queue growing
      - alert: AgentAnycastOfflineQueueGrowing
        expr: agentanycast_offline_queue_size > 100
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "Offline message queue has >100 pending messages"

      # Relay health degraded
      - alert: AgentAnycastRelayDegraded
        expr: >
          agentanycast_relay_health_status != 1
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Relay server health is degraded"

      # MCP tool errors spike
      - alert: AgentAnycastMCPErrors
        expr: >
          rate(agentanycast_mcp_tool_calls_total{status="error"}[5m]) > 1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "MCP tool error rate exceeds 1/s"
```

## Audit Logging

### Configuration

Enable audit logging in the daemon config:

```toml
[policy]
audit_log_path = "/var/log/agentanycast/audit.jsonl"
```

Or pass via the config file. The audit log path must be writable by the daemon process.

### Log Format

Each line in the audit log is a JSON object with the following fields:

```json
{
  "timestamp": "2026-03-21T19:30:00.123456789Z",
  "source": "did:key:z6Mkf5rGMoatrSj1f4...",
  "target": "did:key:z6MkpTHR8VNs59XYG...",
  "skill": "echo",
  "action": "allow",
  "transport": "libp2p",
  "envelope_id": "env-abc123"
}
```

**Fields:**

| Field | Description |
|-------|-------------|
| `timestamp` | RFC 3339 timestamp with nanosecond precision (UTC) |
| `source` | DID of the requesting agent |
| `target` | DID of the target agent |
| `skill` | Skill ID being accessed (if applicable) |
| `action` | Decision: `allow`, `deny`, or `rate_limit` |
| `transport` | Transport used: `libp2p`, `http`, `nats` |
| `envelope_id` | A2A envelope identifier for correlation |

### Analysis

Query audit logs with standard JSON tools:

```bash
# Count denied requests in the last hour
cat /var/log/agentanycast/audit.jsonl | \
  jq -r 'select(.action == "deny") | .source' | sort | uniq -c | sort -rn

# Find all rate-limited sources
grep '"rate_limit"' /var/log/agentanycast/audit.jsonl | jq -r .source | sort -u

# Correlate with a specific envelope ID
grep 'env-abc123' /var/log/agentanycast/audit.jsonl | jq .
```

For production deployments, consider forwarding audit logs to a centralized log management system (e.g., Elasticsearch, Loki, Splunk) for long-term retention and analysis.
