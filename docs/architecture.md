# Architecture

AgentAnycast uses a **sidecar architecture** to bring decentralized P2P communication to AI agents while keeping application code simple.

## Overview

```
┌──────────────────────────────────────────────────────────────────┐
│                        Your Machine                              │
│                                                                  │
│  ┌─────────────────────┐      ┌────────────────────────────────┐ │
│  │  Your Python App    │      │     agentanycastd (daemon)     │ │
│  │                     │      │                                │ │
│  │  ┌───────────────┐  │ gRPC │  ┌──────┐  ┌───────────────┐  │ │
│  │  │ agentanycast   │  │ over │  │Engine│  │  libp2p Host  │  │ │
│  │  │ SDK (Python)  │──┼──UDS─┼──│(A2A) │  │ TCP/QUIC/mDNS │──┼──► Network
│  │  └───────────────┘  │      │  └──────┘  └───────────────┘  │ │
│  │                     │      │  ┌──────┐  ┌───────────────┐  │ │
│  │  - AgentCard        │      │  │Router│  │  BoltDB Store │  │ │
│  │  - @on_task handler │      │  └──────┘  └───────────────┘  │ │
│  │  - send_task()      │      │  ┌──────┐  ┌───────────────┐  │ │
│  │  - discover()       │      │  │Bridge│  │   Metrics     │  │ │
│  └─────────────────────┘      │  └──────┘  └───────────────┘  │ │
│                               └────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────┘
```

**Why a sidecar?** The networking layer (libp2p, NAT traversal, Noise encryption) is complex and performance-sensitive. Writing it in Go and exposing it via gRPC lets the Python SDK stay thin and simple while the daemon handles the hard parts. This architecture already supports multiple SDKs — Python and TypeScript are available today, with more languages possible by adding a gRPC client.

## Components

### Python SDK (`agentanycast-python`)

The SDK is the developer-facing interface. It provides:

- **`Node`** — main entry point; manages daemon lifecycle, sends/receives tasks
- **`AgentCard`** / **`Skill`** — capability descriptors (A2A-compatible)
- **`TaskHandle`** / **`IncomingTask`** — task sending and handling
- **`discover()`** — skill-based agent discovery
- **Framework adapters** — CrewAI, LangGraph integration
- **Interop modules** — W3C DID, MCP tool mapping, AGNTCY directory
- **CLI** — `agentanycast demo/discover/send/status`
- **Daemon auto-management** — downloads, starts, and stops `agentanycastd` automatically

The SDK communicates with the daemon exclusively through gRPC over a Unix domain socket. It never touches the network directly.

### Go Daemon (`agentanycast-node`)

The daemon is the P2P engine. Internal packages:

| Package | Responsibility |
|---|---|
| `internal/a2a/` | A2A protocol engine — task state machine, envelope routing, offline queue, streaming |
| `internal/node/` | libp2p host — peer connections, mDNS discovery, DHT, stream multiplexing |
| `internal/crypto/` | Ed25519 key management, Noise_XX integration, DID conversion (did:key, did:web, did:dns), Verifiable Credentials |
| `internal/nat/` | AutoNAT detection, DCUtR hole punching, Circuit Relay v2 client |
| `internal/store/` | BoltDB persistence — tasks, agent cards, offline message queue |
| `internal/config/` | Configuration — TOML file, environment variables, CLI flags |
| `internal/bridge/` | HTTP Bridge — translates HTTP JSON-RPC ↔ P2P A2A envelopes |
| `internal/anycast/` | Anycast router — skill-based addressing, registry + multi-registry federation + DHT discovery |
| `internal/metrics/` | Prometheus metrics — connections, tasks, routing, bridge, streaming, MCP |
| `internal/mcp/` | MCP Server — exposes P2P capabilities as MCP tools (stdio + Streamable HTTP) |
| `internal/anp/` | ANP Bridge — translates ANP HTTP ↔ A2A P2P (JSON-RPC 2.0 + JSON-LD) |
| `pkg/grpcserver/` | gRPC server — 16 RPC methods exposed to the SDK |

The daemon is started and stopped by the SDK. It runs as a local process, listening only on a Unix domain socket (or localhost TCP).

### Relay Server (`agentanycast-relay`)

The relay provides three services:

1. **Circuit Relay v2** — bridges agents across different networks with strict resource limits. The relay **cannot read traffic** — all communication is end-to-end encrypted before reaching the relay.

2. **Skill Registry** — in-memory registry where agents register their skills and discover each other by capability. TTL-based expiration with heartbeat renewal.

3. **Federation** — gossip-based synchronization across multiple relays for global agent discovery. Uses Last-Writer-Wins conflict resolution.

### Proto Definitions (`agentanycast-proto`)

The single source of truth for all interfaces. Contains:

- **`node_service.proto`** — 16 RPC methods between SDK and daemon
- **`registry_service.proto`** — 4 RPC methods for skill registry on relay
- **`federation.proto`** — 2 RPC methods for multi-relay registry synchronization
- **`a2a_models.proto`** — Task, Message, Part, Artifact, A2AEnvelope (11 envelope types)
- **`agent_card.proto`** — A2A-compatible capability descriptor with P2P extension (did:key, did:web, did:dns, VCs)
- **`streaming.proto`** — StreamStart, StreamChunk, StreamEnd for chunked delivery
- **`common.proto`** — Shared types (PeerInfo, NodeInfo, TaskStatus)

## Data Flow

### Sending a Task (Direct)

```
 Agent A (sender)                                    Agent B (receiver)
 ─────────────────                                   ──────────────────

 Python: send_task(peer_id=...)
        │
        ▼
 SDK: serialize to gRPC
        │
        ▼ (Unix domain socket)
 Daemon: create A2AEnvelope
        │
        ▼
 Router: lookup peer, open libp2p stream
        │
        ▼ (Noise_XX encrypted)
 ───────┼──────── Network ────────┼───────
        │                         │
        ▼                         ▼
                           Daemon: receive envelope
                                  │
                                  ▼
                           Engine: update task state
                                  │
                                  ▼ (Unix domain socket)
                           SDK: deliver to @on_task
                                  │
                                  ▼
                           Python: handler executes
```

### Sending a Task (Anycast)

```
 Agent A                    Relay                    Agent B
 ────────                   ─────                    ────────

 send_task(skill="translate")
        │
        ▼
 Anycast Router
        │
        ▼ (gRPC)
 ───────┼────────────►  Skill Registry
                        DiscoverBySkill("translate")
                              │
                              ▼
                        Returns: Agent B peer_id
        ◄─────────────────────┘
        │
        ▼
 Router: connect to Agent B
        │
        ▼ (Noise_XX encrypted)
 ───────┼──────── Network ────────┼───────
                                  │
                           Agent B processes task
```

### Sending a Task (HTTP Bridge)

```
 Agent A (P2P)                                    HTTP A2A Agent
 ─────────────                                    ──────────────

 send_task(url="https://agent.example.com")
        │
        ▼
 Daemon: HTTP Bridge
        │
        ▼ (HTTPS)
 ───────┼──────── Network ────────┼───────
                                  │
                           POST / (JSON-RPC)
                           A2A HTTP endpoint
```

### Task Lifecycle

A task follows the A2A state machine:

```
SUBMITTED ──► WORKING ──► COMPLETED
                │
                ├──► FAILED
                │
                └──► INPUT_REQUIRED ──► WORKING ──► ...

Any non-terminal state ──► CANCELED
Any state ──► REJECTED (by receiver)
```

- **SUBMITTED** — task sent, waiting for remote agent to pick it up
- **WORKING** — remote agent is processing
- **INPUT_REQUIRED** — remote agent needs more information from the sender
- **COMPLETED** — task finished successfully, artifacts available
- **FAILED** — task failed with an error message
- **CANCELED** — sender canceled the task
- **REJECTED** — receiver refused the task

## Security Model

### Identity

Every node has an **Ed25519 key pair**, generated on first start and persisted in `~/.agentanycast/key`. The public key derives the node's **Peer ID** (a multihash of the public key), which serves as its cryptographic identity.

- No certificate authorities, no DNS — identity is self-sovereign
- Peer IDs are stable across restarts (as long as the key file is preserved)
- Format: `12D3KooW...` (Base58-encoded multihash)

#### W3C DID Interop

Peer IDs can be converted to multiple DID methods for interoperability:

- **`did:key`** — derived directly from the Ed25519 public key (`did:key:z6Mk...`)
- **`did:web`** — web-based DID resolution (`did:web:example.com:agents:myagent`)
- **`did:dns`** — DNS-based DID resolution

The SDK provides bidirectional conversion functions (`peer_id_to_did_key`, `did_web_to_url`, etc.). Agent Cards can also carry Verifiable Credentials for trust attestation.

### Encryption

All peer-to-peer connections use the **Noise_XX** handshake:

1. Both peers exchange ephemeral Curve25519 keys
2. Both peers authenticate with their static Ed25519 keys
3. A shared secret is derived; all subsequent traffic is encrypted with **ChaCha20-Poly1305**

This provides:

- **Mutual authentication** — both sides prove their identity
- **Forward secrecy** — compromising a long-term key doesn't compromise past sessions
- **Confidentiality** — even relay servers only see ciphertext

### Transport Security

```
Agent A ◄────── Noise_XX (E2E encrypted) ──────► Agent B
                        │
                  ┌─────┴─────┐
                  │   Relay    │  ← sees only ciphertext
                  └───────────┘
```

The relay is a **zero-knowledge forwarder**. It cannot decrypt, inspect, or modify traffic.

## NAT Traversal

Agents behind NATs or firewalls use a three-tier strategy:

### Tier 1: Direct Connection

If both agents are on the same network (or have public IPs), they connect directly via TCP, QUIC, or WebTransport.

### Tier 2: Hole Punching (DCUtR)

When agents are behind NATs, the daemon uses [DCUtR (Direct Connection Upgrade through Relay)](https://docs.libp2p.io/concepts/nat/hole-punching/) to punch through NATs:

1. Both agents connect to a relay server
2. The relay coordinates a simultaneous connection attempt
3. If successful, agents upgrade to a direct connection
4. The relay connection is dropped

### Tier 3: Relay Fallback

If hole punching fails (e.g., symmetric NATs), traffic flows through the relay. This is the most restrictive path but always works.

```
NAT detection (AutoNAT)
        │
        ├── Public IP? ──► Direct connection
        │
        └── Behind NAT? ──► Try hole punch (DCUtR)
                                │
                                ├── Success ──► Direct connection
                                │
                                └── Fail ──► Relay fallback
```

### mDNS (Local Network)

On a LAN, [mDNS](https://en.wikipedia.org/wiki/Multicast_DNS) provides zero-configuration discovery. Agents broadcast their presence and find each other without any relay or bootstrap configuration.

## Agent Discovery

AgentAnycast supports multiple discovery mechanisms:

### mDNS (LAN)

Zero-configuration discovery on the local network. Agents broadcast their presence automatically.

### Skill Registry (Relay)

The relay server hosts an in-memory skill registry. Agents register their skills on startup and send heartbeats to keep registrations alive. Other agents query the registry by skill ID, optionally filtering by tags.

- **TTL-based** — registrations expire automatically (default 30s)
- **Tag filtering** — match agents by metadata (e.g., language, region)
- **Capacity limited** — 4096 max registrations, 100 default result limit

### DHT (Kademlia)

For fully decentralized discovery without relying on the relay's registry. Agents publish their skills as provider records on a Kademlia DHT. Other agents query the DHT to find providers.

- **No central dependency** — works even if the relay is down
- **Configurable mode** — `auto`, `server`, or `client`

### Composite Discovery

The anycast router can combine multiple discovery providers (registry + DHT) with deduplication, providing resilient discovery across mechanisms.

## Streaming

For large artifacts, AgentAnycast supports **chunked streaming delivery**:

1. Server sends `StreamStart` with artifact metadata (name, media type, total chunks)
2. Server sends sequential `StreamChunk` messages with data bytes
3. Server sends `StreamEnd` to signal completion

Clients subscribe to streams via `SubscribeTaskStream` for real-time delivery. This avoids loading large artifacts entirely into memory.

## HTTP Bridge

The HTTP Bridge enables interoperability between the P2P network and standard HTTP A2A agents:

- **Inbound** — HTTP clients can send tasks to P2P agents via the bridge's JSON-RPC endpoint
- **Outbound** — P2P agents can call HTTP A2A agents via `send_task(url="...")`
- **Agent Card** — bridge exposes `/.well-known/a2a-agent-card` for HTTP-based discovery

This means P2P agents can participate in the broader A2A ecosystem without requiring all agents to use libp2p.

## Metrics

The daemon optionally exposes Prometheus metrics:

- **Connection metrics** — peer count, connection events
- **Task metrics** — task count by status, duration histogram
- **Routing metrics** — anycast resolution count and latency
- **Bridge metrics** — HTTP bridge request count
- **Streaming metrics** — chunk count and bytes transferred
- **Queue metrics** — offline message queue size

## Agent Card Exchange

When two peers connect, they **automatically exchange Agent Cards**. This lets each side discover the other's capabilities (name, description, skills) without a separate discovery step.

The card exchange happens over a dedicated libp2p protocol stream, separate from task traffic.

## Offline Message Queue

If a message can't be delivered (peer is offline or unreachable), the daemon:

1. Persists the message in BoltDB
2. Monitors peer connectivity
3. Automatically retransmits when the peer comes back online

This provides **at-least-once delivery** for A2A envelopes without requiring the application to implement retry logic. Messages expire after a configurable TTL (default 24 hours).

## MCP Server

The daemon can run as an [MCP (Model Context Protocol)](https://modelcontextprotocol.io/) server, exposing P2P capabilities as tools for AI assistants like Claude Desktop, Cursor, VS Code, ChatGPT, and Gemini CLI.

Two transport modes:
- **stdio** — local integration (`agentanycastd -mcp`)
- **Streamable HTTP** — remote clients (`agentanycastd -mcp-listen :3000`)

Available tools: `toolGetNodeInfo`, `toolListConnectedPeers`, `toolGetAgentCard`, `toolDiscoverAgents`, `toolSendTask`, `toolSendTaskBySkill`, `toolGetTaskStatus`.

The relay also exposes an MCP server with registry-specific tools (`discover_agents`, `list_skills`, `get_relay_info`).

## ANP Bridge

The [ANP (Agent Network Protocol)](https://www.w3.org/community/anp/) bridge enables interoperability with the W3C ANP ecosystem:

- `GET /agent/ad.json` — Agent Description (JSON-LD)
- `GET /agent/interface.json` — OpenRPC specification
- `POST /agent/rpc` — JSON-RPC 2.0 endpoint

## Multi-Relay Federation

Multiple relay servers can synchronize their skill registries using gossip-based federation:

1. Each relay periodically pulls updates from configured peer relays
2. New registrations are pushed to peers
3. Conflicts are resolved using Last-Writer-Wins with version counters
4. Local registrations always take priority over federated ones

This enables global agent discovery across relay clusters without a single point of failure.

## Interoperability

### MCP Tool Mapping

The SDK can map MCP tools to A2A skills and vice versa, enabling agents built on MCP to participate in the AgentAnycast network.

### A2A v1.0 Protocol Compatibility

The Python SDK includes a compatibility layer (`compat/a2a_v1.py`) for bidirectional conversion between internal models and the official A2A v1.0 JSON format.

### OASF (Open Agentic Schema Framework)

Agent Cards can be converted to/from OASF records for publishing to the AGNTCY Agent Directory Service.

### AGNTCY Directory

The SDK can query the AGNTCY agent directory for cross-ecosystem discovery, finding agents registered in external directories.

### Framework Adapters

Built-in adapters for CrewAI, LangGraph, Google ADK, and OpenAI Agents SDK wrap existing framework instances as P2P-capable agents, requiring minimal code changes.

## gRPC Interface

The daemon exposes 16 RPC methods organized into six groups:

| Group | Methods | Description |
|---|---|---|
| **Node** | `GetNodeInfo`, `SetAgentCard` | Node status and identity |
| **Peers** | `ConnectPeer`, `ListPeers`, `GetPeerCard` | Peer management and discovery |
| **Task Client** | `SendTask`, `GetTask`, `CancelTask`, `SubscribeTaskUpdates` | Sending tasks to remote agents |
| **Task Server** | `SubscribeIncomingTasks`, `UpdateTaskStatus`, `CompleteTask`, `FailTask` | Handling incoming tasks |
| **Streaming** | `SubscribeTaskStream`, `SendStreamingArtifact` | Chunked artifact delivery |
| **Discovery** | `Discover` | Skill-based agent discovery |

See the [Protocol Reference](protocol.md) for detailed message definitions.
