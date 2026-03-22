# Configuration Reference

This document provides a complete reference for configuring the AgentAnycast node daemon (`agentanycastd`) and relay server (`agentanycast-relay`).

## Node Daemon (`agentanycastd`)

### Configuration Priority

Configuration values are resolved in this order (highest priority first):

1. **CLI flags** (e.g., `--log-level debug`)
2. **Environment variables** (e.g., `AGENTANYCAST_LOG_LEVEL=debug`)
3. **TOML config file** (default: `~/.agentanycast/config.toml`)
4. **Built-in defaults**

### Environment Variables

| Variable | Description | Default |
|---|---|---|
| `AGENTANYCAST_KEY_PATH` | Path to Ed25519 identity key file | `~/.agentanycast/key` |
| `AGENTANYCAST_GRPC_LISTEN` | gRPC listen address (Unix socket or TCP) | `unix://~/.agentanycast/daemon.sock` |
| `AGENTANYCAST_LOG_LEVEL` | Log level (`debug`, `info`, `warn`, `error`) | `info` |
| `AGENTANYCAST_STORE_PATH` | BoltDB persistence directory | `~/.agentanycast/data` |
| `AGENTANYCAST_BOOTSTRAP_PEERS` | Comma-separated relay multiaddrs | (none) |
| `AGENTANYCAST_ENABLE_MDNS` | Enable mDNS LAN discovery (`true`/`false`) | `true` |
| `AGENTANYCAST_REGISTRY_ADDRS` | Comma-separated registry gRPC addresses | (none) |
| `AGENTANYCAST_MCP_LISTEN` | MCP Streamable HTTP listen address (enables MCP) | (none) |
| `AGENTANYCAST_ANP_LISTEN` | ANP bridge listen address | `:8090` |
| `AGENTANYCAST_ANP_ENABLED` | Enable ANP bridge (`true`/`false`) | `false` |
| `AGENTANYCAST_DID_WEB` | did:web identifier for this agent | (none) |
| `AGENTANYCAST_DID_DNS_DOMAIN` | Domain for did:dns resolution | (none) |
| `AGENTANYCAST_OTLP_ENDPOINT` | OTLP gRPC endpoint for tracing | (none) |
| `AGENTANYCAST_TELEMETRY_ENABLED` | Enable OpenTelemetry tracing (`true`/`false`) | `false` |
| `AGENTANYCAST_SAMPLE_RATE` | Trace sampling rate (0.0 - 1.0) | `1.0` |
| `AGENTANYCAST_NATS_ENABLED` | Enable NATS transport (`true`/`false`) | `false` |
| `AGENTANYCAST_NATS_BROKER` | NATS broker URL (`nats://` or `tls://`) | (none) |
| `AGENTANYCAST_NATS_SUBJECT_PREFIX` | NATS subject prefix per agent | (none) |

### TOML Configuration File

Default location: `~/.agentanycast/config.toml`

If the file does not exist, the daemon starts with built-in defaults. Below is a fully annotated example showing all available options:

```toml
# ── Node ──────────────────────────────────────────────────
# Path to the Ed25519 identity key. Generated automatically if missing.
key_path = "~/.agentanycast/key"

# libp2p listen addresses. Port 0 means random available port.
listen_addrs = [
    "/ip4/0.0.0.0/tcp/0",
    "/ip4/0.0.0.0/udp/0/quic-v1",
]

# ── gRPC ──────────────────────────────────────────────────
# Address for the SDK-to-daemon gRPC connection.
# Unix socket (recommended) or TCP (e.g., "127.0.0.1:50051").
grpc_listen = "unix://~/.agentanycast/daemon.sock"

# ── Relay & NAT ──────────────────────────────────────────
# Bootstrap peers (relay servers) for cross-network connectivity.
bootstrap_peers = [
    "/ip4/203.0.113.50/tcp/4001/p2p/12D3KooWExamplePeerID..."
]

# Enable Circuit Relay v2 client for NAT traversal.
enable_relay_client = true

# Enable DCUtR hole punching for direct connections through NATs.
enable_hole_punching = true

# ── Transport ─────────────────────────────────────────────
# Enable QUIC transport (UDP-based, faster connection establishment).
enable_quic = true

# Enable WebTransport (QUIC-based, browser-compatible). Requires QUIC.
enable_webtransport = false

# ── Discovery ─────────────────────────────────────────────
# Enable mDNS for zero-configuration LAN discovery.
enable_mdns = true

# ── Storage ───────────────────────────────────────────────
# Path to BoltDB data directory (tasks, agent cards, offline queue).
store_path = "~/.agentanycast/data"

# TTL for offline message queue entries. Messages expire after this duration.
offline_queue_ttl = "24h"

# ── Logging ───────────────────────────────────────────────
# Log level: debug, info, warn, error.
log_level = "info"

# Log format: json (structured, recommended for production) or text.
log_format = "json"

# ── HTTP Bridge ───────────────────────────────────────────
# Enables interoperability with standard HTTP-based A2A agents.
[bridge]
enabled = false
listen = ":8080"
# tls_cert = "/etc/agentanycast/cert.pem"
# tls_key = "/etc/agentanycast/key.pem"
# cors_origins = ["https://app.example.com"]

# ── Anycast Routing ───────────────────────────────────────
# Skill-based routing configuration for agent discovery and addressing.
[anycast]
# Strategy for selecting among multiple matching agents: "random".
routing_strategy = "random"

# TTL for discovery result cache.
cache_ttl = "30s"

# Automatically register all skills from the Agent Card on startup.
auto_register = true

# Single relay registry address (backward compatible).
# registry_addr = "relay.example.com:50052"

# Multiple relay registry addresses for multi-relay federation.
# registry_addrs = ["relay1.example.com:50052", "relay2.example.com:50052"]

# Enable DHT-based decentralized discovery (can work alongside registry).
enable_dht = false

# DHT mode: "auto" (discover role from peers), "server" (full DHT node),
# "client" (queries only).
dht_mode = "auto"

# ── Prometheus Metrics ────────────────────────────────────
[metrics]
enabled = false
listen = ":9090"    # Scrape target: http://localhost:9090/metrics

# ── MCP Server ────────────────────────────────────────────
# Exposes P2P capabilities as MCP tools for AI assistants.
[mcp]
enabled = false
listen = ":3000"    # Streamable HTTP transport

# ── ANP Bridge ────────────────────────────────────────────
# W3C Agent Network Protocol interoperability.
[anp]
enabled = false
listen = ":8090"

# ── Identity ──────────────────────────────────────────────
# Decentralized identity configuration.
[identity]
# did:web identifier. When set, serves DID Document via HTTP Bridge.
# did_web = "did:web:example.com:agents:myagent"

# Domain for did:dns resolution. DNS TXT records at _did.<domain>
# should contain did:key URIs mapping to this agent.
# did_dns_domain = "example.com"

# ── OpenTelemetry Tracing ─────────────────────────────────
[telemetry]
enabled = false
otlp_endpoint = "localhost:4317"    # OTLP gRPC collector endpoint
sample_rate = 1.0                   # 0.0 to 1.0 (1.0 = trace everything)
insecure = true                     # Use plaintext gRPC (default for localhost)

# ── NATS Transport ────────────────────────────────────────
# Pluggable transport via NATS message broker.
[transport.nats]
enabled = false
broker = "nats://localhost:4222"    # Use "tls://" for TLS connections
subject_prefix = "agent."           # Subject per agent = prefix + peerID
# auth_user = "agentanycast"
# auth_pass = "secret"
# tls_enabled = false
# tls_cert_file = "/path/to/cert.pem"
# tls_key_file = "/path/to/key.pem"

# ── Policy (ACL, Rate Limiting, Audit) ────────────────────
[policy]
# Path to audit log file (JSON Lines format). Empty = disabled.
# audit_log_path = "/var/log/agentanycast/audit.jsonl"

# Access control rules. Evaluated in order; first match wins.
# If rules are configured but none match, access is denied (default-deny).
# [[policy.acl]]
# source = "did:web:trusted.example.com:*"
# skill = "*"
# allow = true

# [[policy.acl]]
# source = "*"
# skill = "internal-*"
# allow = false

# [[policy.acl]]
# source = "*"
# skill = "*"
# allow = true

# Per-source rate limiting (token bucket).
[policy.rate_limit]
default_rps = 100    # Default requests per second per source

# Per-source overrides.
# [[policy.rate_limit.overrides]]
# source = "did:key:z6MkHighVolume..."
# rps = 500
```

### Configuration Validation

The daemon validates the configuration on startup and rejects invalid combinations:

- `store_path` and `grpc_listen` must not be empty
- `anycast.dht_mode` must be one of: `auto`, `server`, `client`
- When `anycast.auto_register` is `true`, at least one discovery mechanism must be configured (`registry_addr`/`registry_addrs` or `enable_dht`)
- `anp.listen` and `bridge.listen` must not use the same address
- When `transport.nats.enabled` is `true`, `broker` must start with `nats://` or `tls://`

## Relay Server (`agentanycast-relay`)

The relay server is configured entirely through CLI flags.

### CLI Flags

| Flag | Default | Description |
|---|---|---|
| `--listen` | `/ip4/0.0.0.0/tcp/4001` | libp2p listen multiaddr (TCP) |
| `--key` | (in-memory) | Path to persistent Ed25519 identity key |
| `--max-reservations` | `128` | Max concurrent relay reservations |
| `--log-level` | `info` | Log level (`debug`, `info`, `warn`, `error`) |
| `--registry-listen` | `:50052` | gRPC listen address for skill registry |
| `--registry-ttl` | `30s` | Skill registration TTL (heartbeat renewal) |
| `--enable-webtransport` | `false` | Enable WebTransport (QUIC-based) listener |
| `--mcp-listen` | `:8080` | MCP Streamable HTTP listen address |
| `--metrics-listen` | `:9090` | Health/metrics HTTP listen address |
| `--api-listen` | `:8081` | REST API listen address for agent directory |
| `--api-cors-origins` | (same-origin) | Comma-separated allowed CORS origins (`*` = all) |
| `--otlp-endpoint` | (none) | OTLP gRPC endpoint for distributed tracing |
| `--federation-peers` | (none) | Comma-separated peer relay gRPC addresses |
| `--federation-sync-interval` | `10s` | Federation gossip sync interval |
| `--version` | | Print version and exit |

### Usage Examples

**Minimal relay (development):**

```bash
./agentanycast-relay
```

Generates an ephemeral key (Peer ID changes on restart). Listens on TCP 4001 + QUIC 4001.

**Production relay with persistent identity:**

```bash
./agentanycast-relay \
    --key /var/lib/agentanycast/relay.key \
    --listen /ip4/0.0.0.0/tcp/4001 \
    --log-level info
```

**Full-featured relay:**

```bash
./agentanycast-relay \
    --key /var/lib/agentanycast/relay.key \
    --listen /ip4/0.0.0.0/tcp/4001 \
    --max-reservations 256 \
    --registry-listen :50052 \
    --registry-ttl 30s \
    --mcp-listen :8080 \
    --metrics-listen :9090 \
    --api-listen :8081 \
    --api-cors-origins "https://dashboard.example.com" \
    --enable-webtransport \
    --otlp-endpoint localhost:4317 \
    --log-level info
```

**Federated relay cluster:**

```bash
# Relay 1
./agentanycast-relay \
    --key /var/lib/agentanycast/relay1.key \
    --federation-peers "relay2.example.com:50052,relay3.example.com:50052" \
    --federation-sync-interval 10s

# Relay 2
./agentanycast-relay \
    --key /var/lib/agentanycast/relay2.key \
    --federation-peers "relay1.example.com:50052,relay3.example.com:50052"
```

### Firewall Requirements

| Port | Protocol | Service | Required? |
|---|---|---|---|
| 4001 | TCP | libp2p relay (Circuit Relay v2) | Yes |
| 4001 | UDP | QUIC transport | Yes |
| 50052 | TCP | Skill registry gRPC | Only if agents use skill-based routing |
| 8080 | TCP | MCP Streamable HTTP server | Optional |
| 8081 | TCP | REST API (agent directory) | Optional |
| 9090 | TCP | Health/metrics HTTP | Optional |

### Docker Compose

```yaml
version: "3.8"
services:
  relay:
    image: agentanycast/relay:latest
    command: >
      --key /data/relay.key
      --listen /ip4/0.0.0.0/tcp/4001
      --max-reservations 128
      --registry-listen :50052
      --registry-ttl 30s
      --mcp-listen :8080
      --metrics-listen :9090
      --log-level info
    ports:
      - "4001:4001/tcp"   # libp2p relay
      - "4001:4001/udp"   # QUIC
      - "50052:50052"     # Skill registry gRPC
      - "8080:8080"       # MCP server
      - "9090:9090"       # Health/metrics
    volumes:
      - relay-data:/data
    restart: unless-stopped

volumes:
  relay-data:
```

### Relay Resource Limits

These are compiled into the relay binary and enforce strict per-peer and global caps:

| Limit | Value | Purpose |
|---|---|---|
| Duration | 2 min | Max duration of a single relayed connection |
| Data | 128 KiB | Max data per relayed connection |
| Reservations | 128 (configurable) | Global max concurrent reservations |
| Circuits | 16 | Max concurrent active relay circuits |
| Per Peer | 4 | Max reservations per Peer ID |
| Per IP | 8 | Max reservations per IP address |
| Buffer Size | 4096 bytes | Internal relay buffer |

### Skill Registry Limits

| Limit | Value |
|---|---|
| Max registrations | 4096 |
| Default discover limit | 100 |
| Hard discover limit | 1000 |
| Default TTL | 30 seconds (configurable via `--registry-ttl`) |

## Running Multiple Nodes on One Machine

Use separate `home` directories to avoid socket, key, and store conflicts:

```python
# Python SDK
async with Node(card=card1, home="/opt/agent1") as node1:
    ...

async with Node(card=card2, home="/opt/agent2") as node2:
    ...
```

```typescript
// TypeScript SDK
const node1 = new Node({ card: card1, home: "/opt/agent1" });
const node2 = new Node({ card: card2, home: "/opt/agent2" });
```

Each `home` directory gets its own `key`, `daemon.sock`, and `data/` -- no conflicts.

## Python SDK Configuration

The Python SDK passes configuration to the daemon. Key parameters on `Node()`:

| Parameter | Description | Default |
|---|---|---|
| `home` | Data directory for key, socket, store | `~/.agentanycast` |
| `bootstrap_peers` | List of relay multiaddrs | `[]` |
| `registry_addr` | Skill registry gRPC address | `None` |
| `enable_mdns` | Enable mDNS LAN discovery | `True` |
| `log_level` | Daemon log level | `info` |

## TypeScript SDK Configuration

| Parameter | Description | Default |
|---|---|---|
| `home` | Data directory | `~/.agentanycast` |
| `bootstrapPeers` | List of relay multiaddrs | `[]` |
| `registryAddr` | Skill registry gRPC address | `undefined` |
| `enableMdns` | Enable mDNS LAN discovery | `true` |
| `logLevel` | Daemon log level | `info` |

The environment variable `AGENTANYCAST_SKIP_DOWNLOAD=1` skips the automatic daemon binary download during `npm install`.
