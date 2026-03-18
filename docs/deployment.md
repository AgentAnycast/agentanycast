# Deployment Guide

This guide covers deploying AgentAnycast in production environments: relay server setup, daemon configuration, HTTP bridge, metrics, and security considerations.

## Deployment Modes

### LAN Only (Zero Configuration)

If all agents are on the same local network, **no deployment is needed**. Agents discover each other via mDNS automatically.

```python
# Just start your agents — they find each other
async with Node(card=card) as node:
    ...
```

### Cross-Network (Self-Hosted Relay)

For agents across different networks, deploy a relay server on a machine with a public IP.

## Deploying a Relay Server

### Docker Compose (Recommended)

```bash
git clone https://github.com/AgentAnycast/agentanycast-relay.git
cd agentanycast-relay
docker-compose up -d
```

The `docker-compose.yml` mounts a volume for the identity key, ensuring the relay's Peer ID survives container restarts.

Check the relay address:

```bash
docker-compose logs relay
# RELAY_ADDR=/ip4/<YOUR_IP>/tcp/4001/p2p/12D3KooW...
```

### From Source

```bash
git clone https://github.com/AgentAnycast/agentanycast-relay.git
cd agentanycast-relay
go build -o relay ./cmd/relay
./relay --listen /ip4/0.0.0.0/tcp/4001 --key ./relay.key
```

> **Important:** Always use `--key` with a persistent path. Without it, the relay generates a new in-memory key on each restart, changing its Peer ID. All agents would then need to update their bootstrap configuration.

### Relay Configuration

| Flag | Description | Default |
|---|---|---|
| `--listen` | Multiaddr to listen on | `/ip4/0.0.0.0/tcp/4001` |
| `--key` | Path to persistent identity key | In-memory (not recommended) |
| `--max-reservations` | Max concurrent relay reservations | `128` |
| `--registry-listen` | gRPC address for skill registry | `:50052` |
| `--registry-ttl` | Skill registration TTL | `30s` |
| `--log-level` | Log level (`debug`, `info`, `warn`, `error`) | `info` |

### Relay Resource Limits

The relay enforces strict per-peer and global limits:

| Limit | Value | Purpose |
|---|---|---|
| Duration | 2 min | Max duration of a single relayed connection |
| Data | 128 KiB | Max data per relayed connection |
| Reservations | 128 | Global max concurrent reservations |
| Circuits | 16 | Max concurrent active relay circuits |
| Per Peer | 4 | Max reservations per Peer ID |
| Per IP | 8 | Max reservations per IP address |

### Skill Registry Limits

| Limit | Value |
|---|---|
| Max registrations | 4096 |
| Default discover limit | 100 |
| Hard discover limit | 1000 |
| Default TTL | 30 seconds |

### Hosting Recommendations

| Platform | Cost | Notes |
|---|---|---|
| **Oracle Cloud Free Tier** | $0/forever | 4 ARM cores, 24 GB RAM — more than enough |
| DigitalOcean | $4/mo | Basic droplet |
| Fly.io | $0 (free tier) | 3 shared VMs |
| Any VPS with public IP | Varies | Ensure ports 4001 TCP+UDP and 50052 TCP are open |

**Firewall requirements:**
- Port 4001 TCP + UDP — relay circuit traffic (P2P + QUIC)
- Port 50052 TCP — skill registry gRPC (only needed if agents use skill-based routing)

## Configuring the Daemon

The daemon (`agentanycastd`) is typically auto-managed by the Python SDK. For advanced use cases, you can configure it directly.

### Configuration Priority

CLI flags > environment variables > config file > defaults

### Environment Variables

| Variable | Description | Default |
|---|---|---|
| `AGENTANYCAST_KEY_PATH` | Identity key file path | `~/.agentanycast/key` |
| `AGENTANYCAST_GRPC_LISTEN` | gRPC listen address | `127.0.0.1:50051` |
| `AGENTANYCAST_LOG_LEVEL` | Log level | `info` |
| `AGENTANYCAST_STORE_PATH` | BoltDB store path | `~/.agentanycast/store` |
| `AGENTANYCAST_BOOTSTRAP_PEERS` | Comma-separated relay multiaddrs | (none) |
| `AGENTANYCAST_ENABLE_MDNS` | Enable mDNS discovery | `true` |

### Config File

Default: `~/.agentanycast/config.toml`

```toml
key_path = "~/.agentanycast/key"
grpc_listen = "127.0.0.1:50051"
log_level = "info"
log_format = "json"
store_path = "~/.agentanycast/store"
enable_mdns = true
bootstrap_peers = [
    "/ip4/203.0.113.50/tcp/4001/p2p/12D3KooW..."
]

# HTTP Bridge — expose P2P agents via HTTP A2A endpoint
[bridge]
enabled = false
listen = ":8080"
# tls_cert = "/path/to/cert.pem"
# tls_key = "/path/to/key.pem"
# cors_origins = ["https://app.example.com"]

# Anycast — skill-based routing
[anycast]
# registry_addr = "relay.example.com:50052"   # Relay's registry gRPC address
enable_dht = false                             # Enable Kademlia DHT discovery
dht_mode = "auto"                              # "auto", "server", or "client"
cache_ttl = "30s"                              # Route cache TTL
auto_register = true                           # Auto-register skills on startup

# Prometheus Metrics
[metrics]
enabled = false
listen = ":9090"
```

## HTTP Bridge

The HTTP Bridge enables standard HTTP A2A clients to interact with P2P agents.

### Enabling the Bridge

```toml
[bridge]
enabled = true
listen = ":8080"
```

This exposes:
- `GET /.well-known/a2a-agent-card` — returns the local agent's card
- `POST /` — JSON-RPC endpoint for A2A task operations

### TLS

For production, enable TLS:

```toml
[bridge]
enabled = true
listen = ":8443"
tls_cert = "/etc/agentanycast/cert.pem"
tls_key = "/etc/agentanycast/key.pem"
```

### CORS

Allow browser-based clients:

```toml
[bridge]
cors_origins = ["https://app.example.com"]
```

## Anycast Routing

### Relay Registry

The simplest option — agents register skills with the relay's built-in registry:

```toml
[anycast]
registry_addr = "relay.example.com:50052"
auto_register = true
```

When `auto_register` is true, the daemon automatically registers all skills from the Agent Card with the relay on startup and sends heartbeats to keep registrations alive.

### DHT Discovery

For fully decentralized discovery (no relay dependency):

```toml
[anycast]
enable_dht = true
dht_mode = "auto"    # "auto" (discover role from peers), "server" (full DHT node), "client" (queries only)
```

### Composite Discovery

Both can run simultaneously — the anycast router deduplicates results:

```toml
[anycast]
registry_addr = "relay.example.com:50052"
enable_dht = true
cache_ttl = "30s"
```

## Prometheus Metrics

Enable observability with Prometheus:

```toml
[metrics]
enabled = true
listen = ":9090"
```

Scrape target: `http://localhost:9090/metrics`

Available metrics:

| Metric | Type | Description |
|---|---|---|
| `agentanycast_connected_peers` | Gauge | Current peer count |
| `agentanycast_connections_total` | Counter | Total connection events |
| `agentanycast_tasks_total` | Counter | Tasks by status |
| `agentanycast_task_duration_seconds` | Histogram | Task completion latency |
| `agentanycast_route_resolutions_total` | Counter | Anycast resolution count |
| `agentanycast_bridge_requests_total` | Counter | HTTP bridge requests |
| `agentanycast_stream_chunks_total` | Counter | Streaming chunks sent/received |
| `agentanycast_messages_total` | Counter | A2A messages by type |
| `agentanycast_offline_queue_size` | Gauge | Queued offline messages |

### Running Multiple Nodes on One Machine

Use separate `home` directories:

```python
# Agent 1
async with Node(card=card1, home="/opt/agent1") as node1:
    ...

# Agent 2
async with Node(card=card2, home="/opt/agent2") as node2:
    ...
```

Each home directory gets its own key, socket, and store — no conflicts.

## Security Considerations

### Identity Key Protection

The Ed25519 key at `~/.agentanycast/key` is the agent's identity. Anyone with this key can impersonate the agent.

- Set file permissions to `600` (owner read/write only)
- Back up keys for persistent agents
- Never share keys between agents
- Rotate keys by deleting the key file and restarting (generates a new Peer ID)

### Network Exposure

The daemon's gRPC server listens on `127.0.0.1:50051` by default — **localhost only**. Never expose the gRPC port to the network unless you understand the implications.

### HTTP Bridge Security

If the HTTP bridge is enabled:

- Use TLS in production (`tls_cert` + `tls_key`)
- Restrict CORS origins (`cors_origins`)
- Consider placing behind a reverse proxy for rate limiting
- The bridge port is public-facing — treat it like any web service

### Relay Trust Model

The relay is a **zero-knowledge forwarder**:

- All traffic is end-to-end encrypted with Noise_XX before reaching the relay
- The relay cannot decrypt, inspect, or modify message content
- The relay sees only: source Peer ID, destination Peer ID, and encrypted bytes
- You can run your own relay — no trust in third-party infrastructure required
- The skill registry stores only metadata (skill IDs, tags, Peer IDs) — no message content

### mDNS Considerations

mDNS broadcasts agent presence on the local network. In security-sensitive environments:

- Disable mDNS if LAN discovery is not needed: `AGENTANYCAST_ENABLE_MDNS=false`
- Use relay-only mode for controlled connectivity
- Note: even with mDNS discovery, all connections are still Noise_XX encrypted

## Production Checklist

- [ ] Deploy a relay server with `--key` pointing to a persistent file
- [ ] Open firewall ports: 4001 TCP+UDP (relay), 50052 TCP (registry)
- [ ] Set `AGENTANYCAST_BOOTSTRAP_PEERS` on all agent machines
- [ ] Ensure identity keys have `600` permissions
- [ ] Verify gRPC listens on localhost only (default)
- [ ] If using HTTP bridge: enable TLS and restrict CORS
- [ ] If using metrics: scrape endpoint with Prometheus
- [ ] Disable mDNS if not needed (`AGENTANYCAST_ENABLE_MDNS=false`)
- [ ] Set log level to `info` or `warn` for production
- [ ] Set log format to `json` for structured logging
- [ ] Configure offline queue TTL appropriately (`offline_queue_ttl`)
- [ ] Monitor relay logs for resource limit hits
- [ ] Back up identity keys for persistent agents
