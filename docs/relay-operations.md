# Relay Operations Runbook

This runbook covers day-to-day operational procedures for running AgentAnycast relay servers in production. For initial deployment instructions, see the [Deployment Guide](deployment.md).

## Key Management

### Key Storage Locations

| Environment | Default Path | Notes |
|---|---|---|
| Docker | `/data/key` | Persisted via `relay-data` named volume |
| Host (binary) | `~/.agentanycast/key` or path passed to `--key` | Must be a persistent filesystem path |
| No `--key` flag | In-memory (ephemeral) | **Not recommended** — Peer ID changes on every restart |

The identity key is an Ed25519 private key that determines the relay's Peer ID. All agents referencing this relay by its multiaddr embed the Peer ID, so key stability is critical.

### Key Backup

```bash
# Docker: copy key out of the named volume
docker cp $(docker compose ps -q relay):/data/key ./relay-key-backup

# Host: copy the key file directly
cp ~/.agentanycast/key ./relay-key-backup

# Verify the backup is valid (non-empty, correct size ~64-68 bytes)
ls -la ./relay-key-backup
```

Store backups in a secure location (e.g., encrypted cloud storage or a secrets manager). The key file should have `600` permissions at rest.

### Key Rotation

Key rotation changes the relay's Peer ID. All agents must update their `bootstrap_peers` configuration afterward.

```bash
# 1. Stop the relay
docker compose down
# or: kill -SIGTERM <relay-pid>

# 2. Back up the current key
cp /data/key /data/key.bak.$(date +%Y%m%d)

# 3. Remove the old key (a new one is generated on next start)
rm /data/key

# 4. Start the relay — it generates a fresh Ed25519 key
docker compose up -d

# 5. Retrieve the new Peer ID from logs
docker compose logs relay | grep RELAY_ADDR

# 6. Update bootstrap_peers in all agent configurations with the new multiaddr
```

> **Warning:** Key rotation is a disruptive operation. All connected peers lose their relay reservation and must reconnect using the new Peer ID. Plan a maintenance window.

### Key Restore

```bash
# 1. Stop the relay
docker compose down

# 2. Copy the backup key into the volume
docker cp ./relay-key-backup $(docker compose ps -q relay):/data/key
# If the container is stopped, mount the volume manually:
docker run --rm -v relay-data:/data -v $(pwd):/backup alpine \
  cp /backup/relay-key-backup /data/key

# 3. Set correct permissions
docker run --rm -v relay-data:/data alpine chmod 600 /data/key

# 4. Start the relay
docker compose up -d

# 5. Verify the Peer ID matches the expected value
docker compose logs relay | grep peer_id
```

## Health Monitoring

### Health Endpoint

The relay exposes health and metrics on the `--metrics-listen` address (default `:9090`):

```bash
# JSON health status
curl -s http://localhost:9090/health | jq .
```

Example response:

```json
{
  "status": "healthy",
  "version": "0.3.0",
  "peer_id": "12D3KooWExample...",
  "uptime_seconds": 86421.5,
  "registry": {
    "local_count": 42,
    "federated_count": 15,
    "skill_count": 28,
    "fed_skill_count": 10
  },
  "federation": {
    "peers": 2,
    "healthy_peers": 2
  },
  "libp2p": {
    "connected_peers": 37
  }
}
```

Health status values:

| Status | Meaning |
|---|---|
| `healthy` | All subsystems operating normally |
| `degraded` | Federation peer(s) unreachable, but local operations continue |
| `unhealthy` | Critical failure (not currently emitted; reserved for future use) |

### Prometheus Metrics

The relay exposes Prometheus metrics at `/metrics` on the same `--metrics-listen` port.

**Registry metrics:**

| Metric | Type | Description |
|---|---|---|
| `registry_local_count` | Gauge | Active local skill registrations |
| `registry_federated_count` | Gauge | Active federated skill registrations |
| `registry_discover_duration_seconds` | Histogram | Latency of discovery queries |
| `registry_evictions_total` | Counter | Expired registrations evicted by TTL sweeper |

**Federation metrics:**

| Metric | Type | Description |
|---|---|---|
| `federation_sync_duration_seconds` | Histogram | Duration of sync per federation peer |
| `federation_sync_errors_total` | Counter | Total federation sync errors |
| `federation_push_duration_seconds` | Histogram | Duration of federation push operations |

### Prometheus Scrape Configuration

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'agentanycast-relay'
    scrape_interval: 15s
    static_configs:
      - targets: ['relay.example.com:9090']
```

### Alerting Thresholds

| Condition | Suggested Threshold | Severity |
|---|---|---|
| Health status != `healthy` | Any occurrence for > 2 min | Warning |
| `registry_local_count` near max (4096) | > 3500 | Warning |
| `registry_evictions_total` rate spike | > 100/min sustained | Info |
| `federation_sync_errors_total` increasing | > 5 errors in 5 min | Warning |
| Connected peers drops to 0 | Any occurrence for > 1 min | Critical |
| Process memory > container limit | > 400 MiB (of 512 MiB limit) | Warning |
| Uptime resets unexpectedly | `uptime_seconds` drops | Critical |

## Capacity Planning

### Relay Reservations

The `--max-reservations` flag controls the global maximum concurrent relay circuit reservations (default: 128).

**When to increase:**

- Logs show `resource limit exceeded` for relay reservations
- The relay serves more than ~100 concurrently connected peers that need relaying
- Agents report connection failures with `NO_RESERVATION` errors

**Sizing guidance:**

| Deployment Size | Agents | `--max-reservations` | Notes |
|---|---|---|---|
| Small / Dev | < 50 | 128 (default) | Default is sufficient |
| Medium | 50 - 500 | 256 - 512 | Monitor reservation utilization |
| Large | 500+ | 1024+ | Consider multiple relays with federation |

### Memory Usage

The relay is lightweight. Primary memory consumers:

| Component | Approximate Memory | Scales With |
|---|---|---|
| libp2p host + connections | 50-100 MiB baseline | Number of connected peers |
| Skill registry (in-memory) | < 1 MiB per 1000 registrations | Number of registered agents |
| Relay circuit buffers | 4 KiB per active circuit | `--max-reservations` |
| gRPC server overhead | ~20 MiB | Concurrent registry RPCs |

The default Docker memory limit of 512 MiB is suitable for most deployments. For large-scale relays (1000+ concurrent peers), increase to 1 GiB.

### Disk Usage

The relay has minimal disk requirements:

- **Identity key file:** ~68 bytes
- **No database or persistent storage:** The skill registry is entirely in-memory and rebuilt from agent heartbeats after a restart
- **Log output:** Goes to stderr (Docker captures this); rotate with Docker's log driver or external log shipper

### Network Bandwidth

Bandwidth depends on relay circuit traffic and registry gRPC calls:

| Traffic Type | Estimate |
|---|---|
| Relay circuit data | Up to 128 KiB per relayed connection (hard limit), 2 min max duration |
| Registry heartbeats | ~200 bytes per heartbeat, every `registry-ttl` interval per agent |
| Federation sync | Proportional to registry size, every `federation-sync-interval` |
| Health/metrics scrapes | Negligible |

For a relay serving 200 agents with moderate relay traffic, expect 5-20 Mbps sustained bandwidth.

## Common Operations

### Graceful Restart

The relay handles `SIGTERM` and `SIGINT` for graceful shutdown. The gRPC server drains in-flight requests before stopping.

```bash
# Docker Compose (sends SIGTERM, waits for graceful shutdown)
docker compose restart relay

# Host binary
kill -SIGTERM $(pgrep -f agentanycast-relay)
# Then restart the process
```

Connected peers experience a brief disconnection. Agents with `enable_relay_client = true` automatically reconnect and re-reserve within seconds.

### Updating the Relay Binary

**Single relay:**

```bash
# Pull the latest image and recreate the container
docker compose pull relay
docker compose up -d relay
```

**Multi-relay rolling update:**

```bash
# Update one relay at a time, waiting for it to become healthy
for relay in relay1 relay2 relay3; do
  ssh $relay "cd /opt/relay && docker compose pull && docker compose up -d"
  echo "Waiting for $relay to become healthy..."
  until curl -sf "http://$relay:9090/health" | jq -e '.status == "healthy"' > /dev/null; do
    sleep 2
  done
  echo "$relay is healthy"
done
```

### Viewing Connected Peers and Registered Skills

```bash
# Health endpoint shows connected peer count and registry stats
curl -s http://localhost:9090/health | jq '{
  connected_peers: .libp2p.connected_peers,
  local_registrations: .registry.local_count,
  federated_registrations: .registry.federated_count,
  unique_skills: .registry.skill_count
}'

# REST API (if --api-listen is enabled) provides detailed agent directory
curl -s http://localhost:8081/agents | jq .
```

### Registry Entry Lifecycle

Registry entries are managed automatically:

- **Registration:** Agents call `RegisterSkills` via gRPC when they start (or when `auto_register = true`)
- **Heartbeat:** Agents send periodic heartbeats to refresh the TTL (default: every 30 seconds)
- **Expiration:** Entries that miss their TTL deadline are evicted by the background sweeper
- **Disconnection:** When a peer disconnects from libp2p, its registrations are removed immediately

No manual intervention is needed to clear stale entries.

## Disaster Recovery

### Single-Relay Failure

**Impact:**

- Agents behind NAT lose relay connectivity until they reconnect to another relay (if configured) or the relay recovers
- Skill discovery queries to this relay fail; agents using DHT discovery or multi-registry configuration continue operating
- Agents on the same LAN continue communicating via mDNS (unaffected)
- All end-to-end encrypted connections are between peers, not through the relay — no data is lost

**Recovery:**

```bash
# 1. Restart the relay
docker compose up -d

# 2. Verify health
curl -s http://localhost:9090/health | jq .status

# 3. Agents automatically reconnect and re-register skills
# No manual agent-side action required if the Peer ID is unchanged
```

### Multi-Relay Federation Recovery

When one relay in a federation goes down:

- The remaining relays report `degraded` health status
- Federation sync errors increment (`federation_sync_errors_total`)
- Agents registered only on the failed relay become undiscoverable via federation peers until they reconnect or the relay recovers
- Agents configured with `registry_addrs` pointing to multiple relays can re-register on a healthy relay

**Recovery procedure:**

```bash
# 1. Restore the failed relay (same key to preserve Peer ID)
# See "Key Restore" section above

# 2. Verify federation re-syncs
curl -s http://localhost:9090/health | jq .federation
# Expected: {"peers": N, "healthy_peers": N}

# 3. Monitor sync metrics for convergence
curl -s http://localhost:9090/metrics | grep federation_sync
```

### Restoring from Backup

If the relay host is completely lost:

1. Provision a new host with the same public IP (or update DNS)
2. Install Docker and clone the relay repository
3. Restore the identity key from backup (see [Key Restore](#key-restore))
4. Start the relay: `docker compose up -d`
5. Verify the Peer ID matches the original
6. If the IP changed, update agent `bootstrap_peers` configurations

### Network Partition Handling

During a network partition between federated relays:

- Each relay continues serving its local agents independently
- Federation sync errors accumulate but do not affect local operations
- When the partition heals, federation sync resumes automatically
- Conflicting registrations are resolved using Last-Writer-Wins with version counters

No manual intervention is required. Monitor `federation_sync_errors_total` to detect partitions.

## Troubleshooting

### Relay Not Reachable

| Symptom | Check | Fix |
|---|---|---|
| Agents cannot connect | Firewall rules | Open port 4001 TCP + UDP, 50052 TCP |
| Relay unreachable from internet | NAT / port forwarding | Relay must have a public IP or proper port forwarding; use `ForceReachabilityPublic` (set by default) |
| DNS resolution fails | DNS records | Verify A/AAAA records point to the relay host IP |
| Connection refused | Process not running | Check `docker compose ps` or `pgrep agentanycast-relay` |
| TLS/certificate errors | Clock skew | Ensure the relay host clock is synchronized (NTP) |

```bash
# Test TCP connectivity from a remote machine
nc -zv relay.example.com 4001

# Test QUIC/UDP connectivity
nc -zuv relay.example.com 4001

# Test gRPC registry port
nc -zv relay.example.com 50052

# Check listening ports on the relay host
ss -tlnp | grep -E '4001|50052|9090|8080'
```

### High Memory Usage

```bash
# Check container memory usage
docker stats --no-stream $(docker compose ps -q relay)

# Common causes:
# 1. Too many relay reservations — reduce --max-reservations
# 2. Large number of connected peers — expected, scale container limits
# 3. Memory leak (rare) — check if memory grows unbounded, report as bug
```

If memory exceeds the container limit, Docker kills the process (OOMKilled). Increase the `deploy.resources.limits.memory` in `docker-compose.yml`:

```yaml
deploy:
  resources:
    limits:
      memory: 1G  # Increase from default 512M
```

### Slow Discovery

| Symptom | Likely Cause | Fix |
|---|---|---|
| Discovery queries take > 1s | Large registry with many skills | Normal for registries with 1000+ entries; check `registry_discover_duration_seconds` |
| Stale results returned | TTL too long | Reduce `--registry-ttl` (e.g., `15s`) for faster convergence |
| Missing agents in results | Agent not heartbeating | Check agent logs for gRPC connectivity to registry |
| Federation results delayed | Sync interval too long | Reduce `--federation-sync-interval` (e.g., `5s`) |

### Connection Drops

```bash
# Check relay logs for connection events
docker compose logs relay --since 10m | grep -i "disconnect\|error\|failed"

# Look for Noise handshake failures
docker compose logs relay --since 10m | grep -i "noise\|handshake"

# Common causes:
# 1. Relay circuit duration limit (2 min) — expected for long-lived connections;
#    agents should establish direct connections via hole punching
# 2. Relay data limit (128 KiB) — expected for large payloads;
#    use streaming or direct connections for bulk data
# 3. Network instability — check host network metrics
# 4. Resource exhaustion — check max-reservations and per-peer/per-IP limits
```

Enable debug logging for detailed diagnostics:

```bash
# Temporarily increase log verbosity
docker compose down
# Edit docker-compose.yml: change --log-level=info to --log-level=debug
docker compose up -d

# Collect debug logs for analysis
docker compose logs relay --since 5m > relay-debug.log

# Remember to revert to --log-level=info after debugging
```
