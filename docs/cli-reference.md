# CLI Reference

## Python SDK CLI (`agentanycast`)

The Python SDK provides a Click-based CLI for interacting with the AgentAnycast network. Install it with:

```bash
pip install agentanycast
```

### Global Options

| Flag | Description |
|------|-------------|
| `--verbose`, `-v` | Enable debug logging. Shows daemon startup logs, gRPC calls, and detailed error information. |
| `--version` | Print the SDK version and exit. |

### `agentanycast --version`

Print the SDK version and exit.

```bash
agentanycast --version
```

---

### `agentanycast demo`

Start a demo echo agent that responds to any incoming task by echoing back the input message. Useful for testing connectivity and task delivery.

```bash
agentanycast demo [OPTIONS]
```

**Options:**

| Flag | Default | Description |
|------|---------|-------------|
| `--relay TEXT` | None | Relay server multiaddr for cross-network connectivity |
| `--home TEXT` | `~/.agentanycast` | Data directory for daemon state and keys |

**Example:**

```bash
# Start echo agent with default settings
agentanycast demo

# Start with a specific relay
agentanycast demo --relay /ip4/203.0.113.10/tcp/4001/p2p/12D3KooW...
```

The agent registers a single skill (`echo`) and prints its Peer ID on startup. It runs until interrupted with Ctrl+C.

---

### `agentanycast discover`

Discover agents offering a specific skill on the network.

```bash
agentanycast discover SKILL [OPTIONS]
```

**Arguments:**

| Argument | Required | Description |
|----------|----------|-------------|
| `SKILL` | Yes | The skill ID to search for |

**Options:**

| Flag | Default | Description |
|------|---------|-------------|
| `-t, --tag TEXT` | None | Filter by tag (`key=value` format). Can be repeated |
| `--relay TEXT` | None | Relay server multiaddr |
| `--home TEXT` | `~/.agentanycast` | Data directory |

**Example:**

```bash
# Discover agents with the "translate" skill
agentanycast discover translate

# Filter by language tag
agentanycast discover translate -t lang=en -t quality=high

# Use a specific relay for discovery
agentanycast discover echo --relay /ip4/203.0.113.10/tcp/4001/p2p/12D3KooW...
```

**Output:**

```
Found 2 agent(s) with skill 'translate':
  PeerID: 12D3KooWA1b2C3d4...
    Name: Translation Agent
    Desc: Multi-language translation service

  PeerID: 12D3KooWE5f6G7h8...
    Name: DeepL Bridge
    Desc: Translation via DeepL API
```

---

### `agentanycast send`

Send a task to a remote agent and print the response.

```bash
agentanycast send TARGET MESSAGE [OPTIONS]
```

**Arguments:**

| Argument | Required | Description |
|----------|----------|-------------|
| `TARGET` | Yes | Peer ID, skill ID (with `--skill`), or URL (with `--url`) |
| `MESSAGE` | Yes | Text message to send |

**Options:**

| Flag | Default | Description |
|------|---------|-------------|
| `--skill` | False | Treat TARGET as a skill ID (anycast routing) |
| `--url` | False | Treat TARGET as an HTTP A2A agent URL |
| `--relay TEXT` | None | Relay server multiaddr |
| `--home TEXT` | `~/.agentanycast` | Data directory |
| `--timeout INTEGER` | 30 | Wait timeout in seconds |

**Examples:**

```bash
# Send directly to a peer by Peer ID
agentanycast send 12D3KooWA1b2C3d4... "Hello, agent!"

# Send via anycast (skill-based routing)
agentanycast send echo "Hello!" --skill

# Send via HTTP bridge to a standard A2A agent
agentanycast send http://agent.example.com "Hello!" --url

# Send with a longer timeout
agentanycast send echo "Process this large document..." --skill --timeout 120
```

**Output:**

```
Sending task via anycast (skill=echo)...
Task task-abc123 completed (status: completed)
  Artifact: echo
    Echo: Hello!
```

---

### `agentanycast status`

Show the local node status, including the Peer ID and connected peers.

```bash
agentanycast status [OPTIONS]
```

**Options:**

| Flag | Default | Description |
|------|---------|-------------|
| `--relay TEXT` | None | Relay server multiaddr |
| `--home TEXT` | `~/.agentanycast` | Data directory |

**Example:**

```bash
agentanycast status
```

**Output:**

```
PeerID: 12D3KooWA1b2C3d4...
Connected peers: 3
  12D3KooWE5f6G7h8...
  12D3KooWI9j0K1l2...
  12D3KooWM3n4O5p6...
```

---

### `agentanycast info`

Show version and configuration information.

```bash
agentanycast info
```

**Output:**

```
AgentAnycast SDK v0.8.0
Python: 3.12.0 (main, Oct  2 2024, 12:00:00)
Default home: /Users/alice/.agentanycast
  Key exists: True
  Socket exists: True
```

---

### `agentanycast mcp`

Start the MCP (Model Context Protocol) server for AI tool integration. Exposes AgentAnycast P2P networking as MCP tools so that AI assistants can discover agents, send encrypted tasks, and query the network.

```bash
agentanycast mcp [OPTIONS]
```

**Options:**

| Flag | Default | Description |
|------|---------|-------------|
| `--transport [stdio\|http]` | `stdio` | Transport mode. Use `stdio` for Claude Desktop, Cursor, etc. Use `http` for remote clients |
| `--port INTEGER` | 8080 | HTTP port (only used with `--transport http`) |
| `--relay TEXT` | None | Relay server multiaddr for cross-network communication |
| `--home TEXT` | `~/.agentanycast` | Data directory for daemon state |

**Examples:**

```bash
# Start MCP server in stdio mode (default, for Claude Desktop / Cursor)
agentanycast mcp

# Start MCP server in HTTP mode on a custom port
agentanycast mcp --transport http --port 3000

# Start with relay connectivity
agentanycast mcp --relay /ip4/203.0.113.10/tcp/4001/p2p/12D3KooW...
```

**AI assistant configuration (Claude Desktop):**

```json
{
  "mcpServers": {
    "agentanycast": {
      "command": "agentanycast",
      "args": ["mcp"]
    }
  }
}
```

**Quick setup with install.sh:**

The standalone `agentanycast-mcp` package also provides an auto-detect install script that configures supported AI tools automatically:

```bash
curl -fsSL https://raw.githubusercontent.com/AgentAnycast/agentanycast-mcp/main/install.sh | bash
```

---

## TypeScript SDK CLI (`agentanycast-ts`)

The TypeScript SDK includes a CLI mirroring the Python SDK's functionality. Install it with:

```bash
npm install -g agentanycast
```

Or use without installing globally:

```bash
npx agentanycast-ts <command>
```

### Global Options

| Flag | Description |
|------|-------------|
| `--verbose`, `-v` | Enable debug logging. Shows daemon startup logs, gRPC calls, and detailed error information. |
| `--version` | Print the SDK version and exit. |

---

### `agentanycast-ts demo`

Start a demo echo agent that responds to any incoming task by echoing back the input message.

```bash
agentanycast-ts demo [OPTIONS]
```

**Options:**

| Flag | Default | Description |
|------|---------|-------------|
| `--relay TEXT` | None | Relay server multiaddr for cross-network connectivity |
| `--home TEXT` | `~/.agentanycast` | Data directory for daemon state and keys |
| `--verbose`, `-v` | False | Enable debug logging |

**Example:**

```bash
agentanycast-ts demo
agentanycast-ts demo --relay /ip4/203.0.113.10/tcp/4001/p2p/12D3KooW...
```

---

### `agentanycast-ts discover`

Discover agents offering a specific skill on the network.

```bash
agentanycast-ts discover SKILL [OPTIONS]
```

**Arguments:**

| Argument | Required | Description |
|----------|----------|-------------|
| `SKILL` | Yes | The skill ID to search for |

**Options:**

| Flag | Default | Description |
|------|---------|-------------|
| `--relay TEXT` | None | Relay server multiaddr |
| `--home TEXT` | `~/.agentanycast` | Data directory |
| `--verbose`, `-v` | False | Enable debug logging |

**Example:**

```bash
agentanycast-ts discover translate
agentanycast-ts discover echo --relay /ip4/203.0.113.10/tcp/4001/p2p/12D3KooW...
```

---

### `agentanycast-ts send`

Send a task to a remote agent and print the response.

```bash
agentanycast-ts send TARGET MESSAGE [OPTIONS]
```

**Arguments:**

| Argument | Required | Description |
|----------|----------|-------------|
| `TARGET` | Yes | Peer ID of the target agent |
| `MESSAGE` | Yes | Text message to send |

**Options:**

| Flag | Default | Description |
|------|---------|-------------|
| `--relay TEXT` | None | Relay server multiaddr |
| `--home TEXT` | `~/.agentanycast` | Data directory |
| `--verbose`, `-v` | False | Enable debug logging |

**Example:**

```bash
agentanycast-ts send 12D3KooWA1b2C3d4... "Hello, agent!"
```

---

### `agentanycast-ts status`

Show the local node status, including the Peer ID and connected peers.

```bash
agentanycast-ts status [OPTIONS]
```

**Options:**

| Flag | Default | Description |
|------|---------|-------------|
| `--relay TEXT` | None | Relay server multiaddr |
| `--home TEXT` | `~/.agentanycast` | Data directory |
| `--verbose`, `-v` | False | Enable debug logging |

---

### `agentanycast-ts info`

Show version and configuration information.

```bash
agentanycast-ts info [OPTIONS]
```

**Options:**

| Flag | Default | Description |
|------|---------|-------------|
| `--home TEXT` | `~/.agentanycast` | Data directory |
| `--verbose`, `-v` | False | Enable debug logging |

---

## Node Daemon (`agentanycastd`)

The Go daemon that handles P2P networking, encryption, NAT traversal, and the A2A protocol engine. The SDK communicates with it over gRPC.

### Flags

| Flag | Default | Description |
|------|---------|-------------|
| `--config PATH` | `~/.agentanycast/config.toml` | Path to TOML configuration file |
| `--key PATH` | From config | Path to Ed25519 private key file |
| `--grpc-listen ADDR` | `unix://~/.agentanycast/daemon.sock` | gRPC listen address (`unix://` or `tcp://`) |
| `--log-level LEVEL` | `info` | Log level: `debug`, `info`, `warn`, `error` |
| `--bootstrap-peers ADDRS` | None | Comma-separated bootstrap peer multiaddrs |
| `--bridge-listen ADDR` | None | HTTP Bridge listen address (e.g., `:8080`). Enables the bridge |
| `--enable-webtransport` | `false` | Enable WebTransport (QUIC-based, browser-compatible) |
| `--anp-listen ADDR` | None | ANP bridge listen address (e.g., `:8090`). Enables ANP |
| `--mcp` | `false` | Run as MCP server over stdio (for Claude Desktop, Cursor) |
| `--mcp-listen ADDR` | None | MCP Streamable HTTP listen address (e.g., `:3000`) |
| `--mcp-proxy CMD` | None | Wrap an MCP server command as a P2P agent |
| `--otlp-endpoint ADDR` | None | OTLP gRPC endpoint for tracing (e.g., `localhost:4317`) |
| `--nats-broker ADDR` | None | NATS broker address (e.g., `nats://localhost:4222`) |
| `--version` | -- | Print version and exit |

### Configuration Priority

Configuration is resolved in this order (highest to lowest priority):

1. CLI flags
2. Environment variables
3. Config file (`config.toml`)
4. Built-in defaults

### Environment Variables

| Variable | Maps to |
|----------|---------|
| `AGENTANYCAST_KEY_PATH` | `key_path` |
| `AGENTANYCAST_GRPC_LISTEN` | `grpc_listen` |
| `AGENTANYCAST_LOG_LEVEL` | `log_level` |
| `AGENTANYCAST_STORE_PATH` | `store_path` |
| `AGENTANYCAST_BOOTSTRAP_PEERS` | `bootstrap_peers` (comma-separated) |
| `AGENTANYCAST_ENABLE_MDNS` | `enable_mdns` (`false`/`0` to disable) |
| `AGENTANYCAST_REGISTRY_ADDRS` | `anycast.registry_addrs` (comma-separated) |
| `AGENTANYCAST_MCP_LISTEN` | `mcp.listen` (also enables MCP) |
| `AGENTANYCAST_ANP_LISTEN` | `anp.listen` |
| `AGENTANYCAST_ANP_ENABLED` | `anp.enabled` |
| `AGENTANYCAST_DID_WEB` | `identity.did_web` |
| `AGENTANYCAST_DID_DNS_DOMAIN` | `identity.did_dns_domain` |
| `AGENTANYCAST_OTLP_ENDPOINT` | `telemetry.otlp_endpoint` |
| `AGENTANYCAST_TELEMETRY_ENABLED` | `telemetry.enabled` |
| `AGENTANYCAST_SAMPLE_RATE` | `telemetry.sample_rate` |
| `AGENTANYCAST_NATS_ENABLED` | `transport.nats.enabled` |
| `AGENTANYCAST_NATS_BROKER` | `transport.nats.broker` |
| `AGENTANYCAST_NATS_SUBJECT_PREFIX` | `transport.nats.subject_prefix` |

### Config File

The default config file location is `~/.agentanycast/config.toml`. See the [deployment guide](deployment.md) for a complete annotated example.

### Examples

```bash
# Start with defaults
agentanycastd

# Start with debug logging and a relay bootstrap peer
agentanycastd --log-level debug --bootstrap-peers /ip4/203.0.113.10/tcp/4001/p2p/12D3KooW...

# Start with HTTP bridge enabled
agentanycastd --bridge-listen :8080

# Start as MCP server (stdio mode for Claude Desktop)
agentanycastd --mcp

# Start with MCP Streamable HTTP and tracing
agentanycastd --mcp-listen :3000 --otlp-endpoint localhost:4317

# Wrap an existing MCP server as a P2P agent
agentanycastd --mcp-proxy "uvx mcp-server-filesystem /tmp"

# Start with NATS transport
agentanycastd --nats-broker nats://localhost:4222

# Print version
agentanycastd --version
```

### Startup Output

On successful startup, the daemon prints to stdout (suppressed in `--mcp` mode):

```
PEER_ID=12D3KooWA1b2C3d4...
LISTEN_ADDR=/ip4/0.0.0.0/tcp/12345/p2p/12D3KooWA1b2C3d4...
LISTEN_ADDR=/ip4/0.0.0.0/udp/12345/quic-v1/p2p/12D3KooWA1b2C3d4...
```

### Shutdown

The daemon handles `SIGINT` and `SIGTERM` for graceful shutdown. On shutdown it:

1. Unregisters skills from the relay registry (if anycast was enabled).
2. Closes the gRPC server.
3. Shuts down the HTTP bridge, MCP server, and metrics server.
4. Flushes OpenTelemetry traces.
5. Closes the libp2p host and BoltDB store.

---

## Relay Server (`agentanycast-relay`)

A standalone relay server that provides Circuit Relay v2, skill registry, and bootstrap services for the AgentAnycast network.

### Flags

| Flag | Default | Description |
|------|---------|-------------|
| `--listen MULTIADDR` | `/ip4/0.0.0.0/tcp/4001` | libp2p listen multiaddr |
| `--key PATH` | None (ephemeral key) | Path to persistent identity key file |
| `--max-reservations INT` | 128 | Maximum concurrent relay reservations |
| `--log-level LEVEL` | `info` | Log level: `debug`, `info`, `warn`, `error` |
| `--registry-listen ADDR` | `:50052` | gRPC listen address for the Skill Registry |
| `--registry-ttl DURATION` | `30s` | Skill registration TTL before expiry |
| `--enable-webtransport` | `false` | Enable WebTransport (QUIC-based) |
| `--mcp-listen ADDR` | `:8080` | MCP Streamable HTTP listen address (empty to disable) |
| `--metrics-listen ADDR` | `:9090` | Health/metrics HTTP listen address (empty to disable) |
| `--api-listen ADDR` | `:8081` | REST API listen address for agent directory (empty to disable) |
| `--api-cors-origins TEXT` | None | Comma-separated allowed CORS origins (empty = same-origin, `*` = all) |
| `--otlp-endpoint ADDR` | None | OTLP gRPC endpoint for tracing |
| `--federation-peers ADDRS` | None | Comma-separated peer relay gRPC addresses for federation |
| `--federation-sync-interval DURATION` | `10s` | Federation sync interval |
| `--version` | -- | Print version and exit |

### Examples

```bash
# Start with defaults (ephemeral identity)
agentanycast-relay

# Start with persistent identity and higher reservation limit
agentanycast-relay --key /var/lib/agentanycast-relay/key --max-reservations 512

# Start with federation to another relay
agentanycast-relay --federation-peers relay2.example.com:50052

# Start with all optional services
agentanycast-relay \
  --key /var/lib/relay/key \
  --max-reservations 256 \
  --registry-ttl 60s \
  --mcp-listen :8080 \
  --metrics-listen :9090 \
  --api-listen :8081 \
  --api-cors-origins "*" \
  --otlp-endpoint localhost:4317

# Start with WebTransport enabled
agentanycast-relay --enable-webtransport

# Print version
agentanycast-relay --version
```

### Startup Output

```
RELAY_ADDR=/ip4/0.0.0.0/tcp/4001/p2p/12D3KooWR1s2T3u4...
RELAY_ADDR=/ip4/0.0.0.0/udp/4001/quic-v1/p2p/12D3KooWR1s2T3u4...
REGISTRY_ADDR=:50052
MCP_ADDR=:8080
METRICS_ADDR=:9090
API_ADDR=:8081
```

### Docker

```bash
# Build the image
docker build -t agentanycast/relay .

# Run with persistent key storage
docker run -d \
  -p 4001:4001 \
  -p 50052:50052 \
  -p 8080:8080 \
  -p 9090:9090 \
  -v relay-data:/data \
  agentanycast/relay \
  --key /data/key --max-reservations 256
```

Or use Docker Compose:

```bash
docker compose up -d
```

### Shutdown

The relay handles `SIGINT` and `SIGTERM`. On shutdown it:

1. Closes the REST API server.
2. Closes the health/metrics server.
3. Stops federation sync.
4. Closes the MCP server.
5. Gracefully stops the gRPC registry server.
6. Closes the libp2p host.
