# Production Checklist

A comprehensive checklist for deploying AgentAnycast in production environments. Work through each section before going live. For detailed configuration options, see the [Configuration Reference](configuration.md). For monitoring setup, see [Observability & Monitoring](observability.md).

## Pre-Deployment

- [ ] Verify the daemon binary version matches your SDK version: `agentanycastd --version`
- [ ] Verify the relay binary version: `agentanycast-relay --version`
- [ ] Confirm proto compatibility across all components (see [versioning](versioning.md))
- [ ] Generate and persist the Ed25519 identity key (`~/.agentanycast/key`)
- [ ] Back up the identity key to a secure location (loss means a new Peer ID)
- [ ] Set identity key file permissions to `600`: `chmod 600 ~/.agentanycast/key`
- [ ] Set identity key directory permissions to `700`: `chmod 700 ~/.agentanycast`
- [ ] Test relay connectivity from the agent machine:
  ```bash
  agentanycastd --bootstrap-peers "/ip4/<RELAY_IP>/tcp/4001/p2p/<RELAY_PEER_ID>" --log-level debug
  # Look for "connected to relay" in logs
  ```
- [ ] Verify skill registration by querying the relay registry:
  ```bash
  curl -s http://<RELAY_IP>:9090/health | jq '.registry'
  ```

## Security

- [ ] Confirm Noise_XX encryption is active (no plaintext transport path exists in the codebase; verify with debug logs showing `noise` in connection establishment)
- [ ] Open only the required firewall ports:
  - Port **4001 TCP + UDP** -- relay circuit traffic (P2P + QUIC)
  - Port **50051 TCP** -- daemon gRPC (localhost only, never expose externally)
  - Port **50052 TCP** -- skill registry gRPC (relay server only)
- [ ] Verify the gRPC socket listens on localhost or Unix socket only (default: `unix://~/.agentanycast/daemon.sock`)
- [ ] If using Docker, run the relay as a non-root user:
  ```dockerfile
  FROM agentanycast/relay:latest
  USER 1000:1000
  ```
- [ ] If the HTTP bridge is enabled, configure TLS:
  ```toml
  [bridge]
  enabled = true
  listen = ":8443"
  tls_cert = "/etc/agentanycast/cert.pem"
  tls_key = "/etc/agentanycast/key.pem"
  ```
- [ ] Restrict CORS origins on the HTTP bridge (`cors_origins`) to known domains
- [ ] Disable mDNS if LAN discovery is not needed: `enable_mdns = false`
- [ ] Define ACL rules for production agents (default-deny when rules are configured)
- [ ] Configure per-source rate limits for known high-volume or untrusted clients
- [ ] Enable audit logging to a persistent path:
  ```toml
  [policy]
  audit_log_path = "/var/log/agentanycast/audit.jsonl"
  ```
- [ ] If using NATS transport, use `tls://` broker URLs and configure mutual TLS

## Reliability

- [ ] Configure automatic restart with systemd:
  ```ini
  # /etc/systemd/system/agentanycastd.service
  [Unit]
  Description=AgentAnycast Daemon
  After=network-online.target
  Wants=network-online.target

  [Service]
  Type=simple
  ExecStart=/usr/local/bin/agentanycastd
  Restart=on-failure
  RestartSec=5
  LimitNOFILE=65536

  [Install]
  WantedBy=multi-user.target
  ```
- [ ] Or configure Docker restart policy:
  ```yaml
  services:
    relay:
      image: agentanycast/relay:latest
      restart: unless-stopped
  ```
- [ ] Ensure sufficient disk space for BoltDB at `store_path` (default: `~/.agentanycast/data`)
- [ ] Set `offline_queue_ttl` appropriately for your use case (default: `24h`)
- [ ] Configure log rotation for daemon logs (e.g., `logrotate` or Docker log driver):
  ```
  # /etc/logrotate.d/agentanycast
  /var/log/agentanycast/*.log {
      daily
      rotate 14
      compress
      missingok
      notifempty
  }
  ```
- [ ] Configure log rotation for the audit log file
- [ ] Set log level to `info` or `warn` for production
- [ ] Set log format to `json` for structured logging
- [ ] Monitor the health endpoint:
  ```bash
  # Node daemon (requires metrics to be enabled)
  curl -sf http://localhost:9090/health | jq .status

  # Relay server
  curl -sf http://relay.example.com:9090/health | jq .status
  ```
- [ ] Configure Kubernetes liveness and readiness probes if applicable:
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

## Observability

- [ ] Enable Prometheus metrics on the daemon:
  ```toml
  [metrics]
  enabled = true
  listen = ":9090"
  ```
- [ ] Add Prometheus scrape configuration:
  ```yaml
  scrape_configs:
    - job_name: agentanycast-node
      scrape_interval: 15s
      static_configs:
        - targets: ["localhost:9090"]
          labels:
            instance: "node-1"

    - job_name: agentanycast-relay
      scrape_interval: 15s
      static_configs:
        - targets: ["relay.example.com:9090"]
          labels:
            instance: "relay-1"
  ```
- [ ] Set up OpenTelemetry tracing (optional but recommended):
  ```toml
  [telemetry]
  enabled = true
  otlp_endpoint = "localhost:4317"
  sample_rate = 0.1    # 10% sampling for production
  insecure = true      # Set to false if collector uses TLS
  ```
- [ ] Deploy an OTLP-capable collector (Jaeger, Grafana Tempo, or OpenTelemetry Collector):
  ```yaml
  # otel-collector-config.yaml
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
- [ ] Configure alerts on key metrics:
  - `agentanycast_connected_peers == 0` for 5 minutes -- node is isolated
  - `histogram_quantile(0.99, rate(agentanycast_task_duration_seconds_bucket[5m])) > 10` -- task p99 latency above 10 seconds
  - `agentanycast_offline_queue_size > 100` for 10 minutes -- offline queue is growing
  - `rate(agentanycast_tasks_total{status="failed"}[5m]) / rate(agentanycast_tasks_total[5m]) > 0.1` -- task failure rate above 10%
  - `rate(agentanycast_mcp_tool_calls_total{status="error"}[5m]) > 1` -- MCP tool errors above 1/s
- [ ] Set up a Grafana dashboard (see [Observability](observability.md) for a sample dashboard JSON)

## Scaling

- [ ] Tune relay `--max-reservations` based on expected agent count (default: 128)
- [ ] Review relay resource limits (per-peer: 4 reservations, per-IP: 8, per-connection: 128 KiB / 2 min)
- [ ] For multi-relay federation, configure `--federation-peers` on each relay:
  ```bash
  # Relay 1 (US East)
  ./agentanycast-relay \
      --key /data/relay1.key \
      --federation-peers "relay-eu.example.com:50052,relay-ap.example.com:50052"

  # Relay 2 (EU West)
  ./agentanycast-relay \
      --key /data/relay2.key \
      --federation-peers "relay-us.example.com:50052,relay-ap.example.com:50052"
  ```
- [ ] Monitor federation health via the relay health endpoint:
  ```bash
  curl -s http://relay.example.com:9090/health | jq '.federation'
  ```
- [ ] Consider geographic relay placement to reduce latency for distributed agents
- [ ] Monitor skill registry capacity (max 4096 registrations per relay)

## SDK Deployment

- [ ] Verify daemon auto-download works in the deployment environment:
  ```python
  # Python
  from agentanycast import Node
  # Node() auto-downloads the daemon on first use
  ```
  ```typescript
  // TypeScript -- auto-download runs at npm install
  // Skip with: AGENTANYCAST_SKIP_DOWNLOAD=1 npm install
  ```
- [ ] If auto-download is not possible (air-gapped environments), pre-install the daemon binary and set `AGENTANYCAST_DAEMON_PATH`
- [ ] Verify gRPC socket permissions allow the application user to connect:
  ```bash
  ls -la ~/.agentanycast/daemon.sock
  # Should be accessible by the user running the SDK
  ```
- [ ] When running multiple agents on one machine, use separate `home` directories to avoid socket and key conflicts
- [ ] Set `AGENTANYCAST_BOOTSTRAP_PEERS` in the application environment for cross-network deployments
