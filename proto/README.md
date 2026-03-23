# AgentAnycast Proto

**Protocol definitions — the single source of truth for AgentAnycast.**

[![Buf](https://img.shields.io/badge/Buf-STANDARD-4353ff?logo=buf&logoColor=white)](https://buf.build)

All cross-component interfaces in the [AgentAnycast](https://github.com/AgentAnycast/agentanycast) ecosystem are defined here as Protocol Buffers. Every downstream repo depends on these definitions.

> This directory was previously a standalone repository (`agentanycast-proto`). It now lives inside the main repo for simpler dependency management.

## Proto Files

| File | Purpose | Key Types |
|---|---|---|
| `node_service.proto` | SDK ↔ daemon gRPC interface | `NodeService` (16 RPCs) |
| `a2a_models.proto` | A2A wire format | `Task`, `Message`, `Artifact`, `Part`, `A2AEnvelope` (11 types) |
| `agent_card.proto` | Agent capability descriptor | `AgentCard`, `Skill`, `P2PExtension` |
| `common.proto` | Shared primitives | `PeerInfo`, `NodeInfo`, `TaskStatus` |
| `streaming.proto` | Chunked artifact delivery | `StreamStart`, `StreamChunk`, `StreamEnd` |
| `registry_service.proto` | Skill registry on relay | `RegistryService` (4 RPCs) |
| `federation.proto` | Multi-relay registry sync | `FederationService` (2 RPCs) |

## Dependency Flow

```
                    proto/
                (this directory)
                       |
        +--------------+--------------+
        |              |              |
        v              v              v
 agentanycast-   agentanycast-   agentanycast-
    node            relay          python / ts
 (Go: local      (Go: local     (vendored stubs
  replace)        replace)       in _generated/)
```

## Quick Start

### Prerequisites

Install [Buf CLI](https://buf.build/docs/installation):

```bash
# macOS
brew install bufbuild/buf/buf

# Other platforms: https://buf.build/docs/installation
```

### Generate Code

```bash
cd proto
buf generate
```

Output:

```
gen/
├── go/agentanycast/v1/       # Go stubs (agentanycast-node, agentanycast-relay)
├── python/agentanycast/v1/   # Python stubs (agentanycast-python)
└── ts/agentanycast/v1/       # TypeScript stubs (agentanycast-ts)
```

> `gen/` is gitignored. Downstream repos either run `buf generate` in CI or vendor the stubs.

### Lint & Breaking Change Detection

```bash
buf lint                                    # Lint against STANDARD rules
buf breaking --against '.git#branch=main'   # Detect breaking changes vs main
```

## Service Overview

### NodeService -- 16 RPCs

The main gRPC service used by SDKs to control the daemon:

| Group | RPCs |
|---|---|
| **Node** | `GetNodeInfo`, `SetAgentCard` |
| **Peers** | `ConnectPeer`, `ListPeers`, `GetPeerCard` |
| **Task Client** | `SendTask`, `GetTask`, `CancelTask`, `SubscribeTaskUpdates` |
| **Task Server** | `SubscribeIncomingTasks`, `UpdateTaskStatus`, `CompleteTask`, `FailTask` |
| **Streaming** | `SubscribeTaskStream`, `SendStreamingArtifact` |
| **Discovery** | `Discover` |

`SendTask` supports three addressing modes via `oneof target`:

| Field | Mode | Description |
|---|---|---|
| `peer_id` | Direct | Send to a specific Peer ID |
| `skill_id` | Anycast | Route by skill via registry/DHT |
| `url` | HTTP Bridge | Call an external HTTP A2A agent |

### RegistryService -- 4 RPCs

Hosted on the relay server for skill-based agent discovery:

| RPC | Description |
|---|---|
| `RegisterSkills` | Register skills with metadata and tags |
| `UnregisterSkills` | Remove specific skill registrations |
| `DiscoverBySkill` | Find agents by skill ID with optional tag filtering and federation |
| `Heartbeat` | Renew TTL on existing registrations |

### FederationService -- 2 RPCs

Gossip-based registry synchronization across multiple relay servers:

| RPC | Description |
|---|---|
| `SyncRegistrations` | Pull registration updates since a given timestamp |
| `PushRegistrations` | Push local registration updates to a peer relay |

## A2A Envelope Types

The wire protocol defines 11 envelope types for the full task lifecycle:

| Type | Direction | Purpose |
|---|---|---|
| `SEND_TASK` | Client -> Server | Initiate a new task |
| `TASK_STATUS_UPDATE` | Server -> Client | Report progress |
| `TASK_COMPLETE` | Server -> Client | Deliver results |
| `TASK_FAIL` | Server -> Client | Report failure |
| `TASK_CANCEL` | Client -> Server | Request cancellation |
| `GET_TASK` | Client -> Server | Query task state |
| `GET_TASK_RESPONSE` | Server -> Client | Return task state |
| `ACK` | Bidirectional | Acknowledge receipt |
| `STREAM_START` | Server -> Client | Begin streaming artifact |
| `STREAM_CHUNK` | Server -> Client | Deliver artifact chunk |
| `STREAM_END` | Server -> Client | End streaming |

## P2P Extension Fields

The Agent Card includes a P2P extension for decentralized identity and transport metadata:

| Field | Description |
|---|---|
| `peer_id` | libp2p Peer ID |
| `supported_transports` | Active transports (tcp, quic, webtransport) |
| `relay_addresses` | Connected relay addresses |
| `did_key` | W3C `did:key` derived from Ed25519 public key |
| `did_web` | `did:web` identifier for web-based DID resolution |
| `did_dns` | `did:dns` domain for DNS-based DID resolution |
| `verifiable_credentials` | JSON-encoded Verifiable Credentials |

## Conventions

- **Package:** `agentanycast.v1`
- **Lint rules:** Buf STANDARD (enforced in CI)
- **Breaking change policy:** FILE-level detection -- never remove or rename fields, only additive changes
- **Go package:** `github.com/agentanycast/agentanycast-proto/gen/go/agentanycast/v1`

## License

[Apache License, Version 2.0](../LICENSE)
