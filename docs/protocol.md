# Protocol Reference

This document describes the AgentAnycast wire protocol — how agents communicate over the P2P network.

## A2A Compatibility

AgentAnycast implements the [A2A (Agent-to-Agent) protocol](https://github.com/a2aproject/A2A) data model over a P2P transport. The same concepts — Agent Card, Task, Message, Artifact — map directly to A2A's specification.

| A2A Concept | AgentAnycast Implementation |
|---|---|
| Agent Card | Protobuf `AgentCard` with `P2PExtension` (peer_id, DID, transports) |
| Task | Protobuf `Task` with A2A-compatible state machine |
| Message / Part | Protobuf `Message` / `Part` (text, data, URL, raw) |
| Artifact | Protobuf `Artifact` with typed parts |
| Streaming | `StreamStart` / `StreamChunk` / `StreamEnd` envelopes |
| HTTP transport | HTTP Bridge translates JSON-RPC ↔ P2P envelopes |

## Proto Definitions

All types are defined in the `agentanycast.v1` proto package. Source files live in [`proto/`](../proto/).

| File | Contents |
|---|---|
| `common.proto` | `PeerInfo`, `NodeInfo`, `NATType`, `ConnectionType`, `ErrorDetail` |
| `a2a_models.proto` | `Task`, `Message`, `Part`, `Artifact`, `A2AEnvelope` (11 types) |
| `agent_card.proto` | `AgentCard`, `Skill`, `P2PExtension` |
| `streaming.proto` | `StreamStart`, `StreamChunk`, `StreamEnd`, `StreamEndReason` |
| `node_service.proto` | gRPC `NodeService` (16 RPCs) |
| `registry_service.proto` | gRPC `RegistryService` (4 RPCs) |
| `federation.proto` | gRPC `FederationService` (2 RPCs) — multi-relay registry sync |

## Agent Card

An Agent Card describes an agent's identity and capabilities:

```protobuf
message AgentCard {
  string name = 1;
  string description = 2;
  string version = 3;
  string protocol_version = 4;
  repeated Skill skills = 5;
  P2PExtension p2p_extension = 10;
}

message Skill {
  string id = 1;
  string description = 2;
  string input_schema = 3;   // JSON Schema
  string output_schema = 4;  // JSON Schema
}

message P2PExtension {
  string peer_id = 1;
  repeated string supported_transports = 2;
  repeated string relay_addresses = 3;
  string did_key = 4;         // W3C DID (did:key:z6Mk...)
  string did_web = 5;         // did:web identifier
  string did_dns = 6;         // did:dns domain
  repeated string verifiable_credentials = 7;  // JSON-encoded VCs
}
```

The `P2PExtension` is AgentAnycast's addition to the A2A Agent Card, carrying P2P-specific metadata. Cards are automatically exchanged when peers connect.

## A2A Envelope

All peer-to-peer messages are wrapped in an `A2AEnvelope`:

```protobuf
message A2AEnvelope {
  string envelope_id = 1;
  EnvelopeType type = 2;
  google.protobuf.Timestamp timestamp = 3;

  oneof payload {
    SendTaskPayload send_task = 10;
    TaskStatusUpdatePayload task_status_update = 11;
    TaskCompletePayload task_complete = 12;
    TaskFailPayload task_fail = 13;
    TaskCancelPayload task_cancel = 14;
    GetTaskPayload get_task = 15;
    GetTaskResponsePayload get_task_response = 16;
    AckPayload ack = 17;
    StreamStart stream_start = 18;
    StreamChunk stream_chunk = 19;
    StreamEnd stream_end = 20;
  }
}
```

### Envelope Types

| Type | Direction | Purpose |
|---|---|---|
| `SEND_TASK` | Client → Server | Initiate a new task |
| `TASK_STATUS_UPDATE` | Server → Client | Report progress (e.g., "working") |
| `TASK_COMPLETE` | Server → Client | Task finished with artifacts |
| `TASK_FAIL` | Server → Client | Task failed with error |
| `TASK_CANCEL` | Client → Server | Request task cancellation |
| `GET_TASK` | Client → Server | Query current task state |
| `GET_TASK_RESPONSE` | Server → Client | Response to `GET_TASK` |
| `ACK` | Bidirectional | Acknowledge receipt of an envelope |
| `STREAM_START` | Server → Client | Begin streaming an artifact |
| `STREAM_CHUNK` | Server → Client | Deliver a chunk of streaming data |
| `STREAM_END` | Server → Client | End streaming (complete, canceled, or error) |

### Core Payloads

```protobuf
message SendTaskPayload {
  string task_id = 1;
  string context_id = 2;
  Message message = 3;
  string target_skill_id = 4;
}

message TaskStatusUpdatePayload {
  string task_id = 1;
  TaskStatus status = 2;
  Message message = 3;  // optional status message
}

message TaskCompletePayload {
  string task_id = 1;
  repeated Artifact artifacts = 2;
  Message message = 3;  // optional completion message
}

message TaskFailPayload {
  string task_id = 1;
  string error_message = 2;
  Message message = 3;
}

message TaskCancelPayload {
  string task_id = 1;
}

message AckPayload {
  string acknowledged_envelope_id = 1;
}
```

### Streaming Payloads

```protobuf
message StreamStart {
  string task_id = 1;
  string artifact_id = 2;
  string artifact_name = 3;
  string media_type = 4;
  int32 total_chunks = 5;
  map<string, string> metadata = 6;
}

message StreamChunk {
  string task_id = 1;
  string artifact_id = 2;
  int32 sequence = 3;
  bytes data = 4;
  bool is_last = 5;
}

message StreamEnd {
  string task_id = 1;
  string artifact_id = 2;
  StreamEndReason reason = 3;  // COMPLETE, CANCELED, ERROR
}
```

## Task Lifecycle

### State Machine

```
                    ┌──────────────┐
                    │  SUBMITTED   │
                    └──────┬───────┘
                           │ agent picks up
                    ┌──────▼───────┐
              ┌─────│   WORKING    │─────┐
              │     └──────┬───────┘     │
              │            │             │
     ┌────────▼────────┐   │    ┌────────▼────────┐
     │ INPUT_REQUIRED   │   │    │     FAILED      │
     └────────┬────────┘   │    └─────────────────┘
              │            │
              └────► WORKING ◄──┘
                       │
              ┌────────▼────────┐
              │   COMPLETED     │
              └─────────────────┘

  Any non-terminal state ──► CANCELED
  Any state ──► REJECTED
```

### States

| Status | Terminal | Description |
|---|---|---|
| `SUBMITTED` | No | Task created, awaiting pickup by remote agent |
| `WORKING` | No | Remote agent is actively processing |
| `INPUT_REQUIRED` | No | Remote agent needs more information |
| `COMPLETED` | Yes | Task finished, artifacts available |
| `FAILED` | Yes | Task failed with error |
| `CANCELED` | Yes | Task canceled by sender |
| `REJECTED` | Yes | Task rejected by receiver |

### Typical Flow

1. Client sends `SEND_TASK` envelope
2. Server receives via `SubscribeIncomingTasks` stream
3. Server sends `TASK_STATUS_UPDATE` (status: `WORKING`)
4. Server processes the task
5. Server sends `TASK_COMPLETE` with artifacts
6. Client's `TaskHandle.wait()` resolves with the completed `Task`

### Streaming Flow

For large artifacts:

1. Client sends `SEND_TASK` envelope
2. Server sends `TASK_STATUS_UPDATE` (status: `WORKING`)
3. Server sends `STREAM_START` with artifact metadata
4. Server sends sequential `STREAM_CHUNK` messages
5. Server sends `STREAM_END` (reason: `COMPLETE`)
6. Server sends `TASK_COMPLETE`

### Multi-Turn Conversation

For tasks requiring back-and-forth:

1. Client sends `SEND_TASK` with initial message
2. Server sends `TASK_STATUS_UPDATE` (status: `INPUT_REQUIRED`) with a clarifying question
3. Client sends another `SEND_TASK` with the same `context_id` and additional information
4. Server processes and sends `TASK_COMPLETE`

The `context_id` links related tasks into a conversation thread.

## Message and Part Types

### Message

```protobuf
message Message {
  string message_id = 1;
  MessageRole role = 2;       // USER or AGENT
  repeated Part parts = 3;
  google.protobuf.Timestamp created_at = 4;
}
```

### Part

```protobuf
message Part {
  oneof content {
    string text_part = 1;     // Plain text
    bytes data_part = 2;      // Structured data (JSON bytes)
    string url_part = 3;      // URL reference
    bytes raw_part = 4;       // Binary data
  }
  string media_type = 10;     // MIME type
  map<string, string> metadata = 11;
}
```

Parts are flexible content containers. Common patterns:

| Use Case | Part Type | `media_type` |
|---|---|---|
| Text message | `text_part` | (omitted or `text/plain`) |
| JSON payload | `data_part` | `application/json` |
| Image reference | `url_part` | `image/png` |
| Binary file | `raw_part` | `application/octet-stream` |

## gRPC Services

### NodeService (16 RPCs)

The main gRPC service used by SDKs to control the daemon.

#### Node Management

```protobuf
rpc GetNodeInfo(GetNodeInfoRequest) returns (GetNodeInfoResponse);
rpc SetAgentCard(SetAgentCardRequest) returns (SetAgentCardResponse);
```

#### Peer Management

```protobuf
rpc ConnectPeer(ConnectPeerRequest) returns (ConnectPeerResponse);
rpc ListPeers(ListPeersRequest) returns (ListPeersResponse);
rpc GetPeerCard(GetPeerCardRequest) returns (GetPeerCardResponse);
```

#### Task Client RPCs

```protobuf
rpc SendTask(SendTaskRequest) returns (SendTaskResponse);
rpc GetTask(GetTaskRequest) returns (GetTaskResponse);
rpc CancelTask(CancelTaskRequest) returns (CancelTaskResponse);
rpc SubscribeTaskUpdates(SubscribeTaskUpdatesRequest) returns (stream SubscribeTaskUpdatesResponse);
```

`SendTask` supports three addressing modes via `oneof target`:

```protobuf
message SendTaskRequest {
  oneof target {
    string peer_id = 1;    // Direct: specific Peer ID
    string skill_id = 2;   // Anycast: route by capability
    string url = 3;        // HTTP Bridge: external HTTP A2A agent
  }
  Message message = 10;
  map<string, string> metadata = 11;
}
```

#### Task Server RPCs

```protobuf
rpc SubscribeIncomingTasks(SubscribeIncomingTasksRequest) returns (stream SubscribeIncomingTasksResponse);
rpc UpdateTaskStatus(UpdateTaskStatusRequest) returns (UpdateTaskStatusResponse);
rpc CompleteTask(CompleteTaskRequest) returns (CompleteTaskResponse);
rpc FailTask(FailTaskRequest) returns (FailTaskResponse);
```

#### Streaming RPCs

```protobuf
rpc SubscribeTaskStream(SubscribeTaskStreamRequest) returns (stream SubscribeTaskStreamResponse);
rpc SendStreamingArtifact(stream SendStreamingArtifactRequest) returns (SendStreamingArtifactResponse);
```

- `SubscribeTaskStream` — server-streaming RPC; client subscribes to stream events (start, chunk, end) for a task
- `SendStreamingArtifact` — client-streaming RPC; server sends artifact data in chunks

#### Discovery RPC

```protobuf
rpc Discover(DiscoverRequest) returns (DiscoverResponse);

message DiscoverRequest {
  string skill_id = 1;
  map<string, string> tags = 2;    // optional tag filters
  int32 limit = 3;                 // max results
}

message DiscoverResponse {
  repeated DiscoveredAgent agents = 1;
}

message DiscoveredAgent {
  string peer_id = 1;
  string agent_name = 2;
  string agent_description = 3;
  repeated Skill skills = 4;
}
```

### RegistryService (4 RPCs)

Hosted on the Relay server. Used by daemons to register and discover skills.

```protobuf
service RegistryService {
  rpc RegisterSkills(RegisterSkillsRequest) returns (RegisterSkillsResponse);
  rpc UnregisterSkills(UnregisterSkillsRequest) returns (UnregisterSkillsResponse);
  rpc DiscoverBySkill(DiscoverBySkillRequest) returns (DiscoverBySkillResponse);
  rpc Heartbeat(HeartbeatRequest) returns (HeartbeatResponse);
}
```

#### Key Messages

```protobuf
message SkillInfo {
  string id = 1;
  string description = 2;
  map<string, string> tags = 3;
}

message SkillRegistration {
  string peer_id = 1;
  string agent_name = 2;
  string agent_description = 3;
  SkillInfo skill = 4;
  google.protobuf.Timestamp registered_at = 5;
  google.protobuf.Timestamp expires_at = 6;
}
```

- `RegisterSkills` — registers skills with tags; returns expiration timestamp
- `UnregisterSkills` — removes specific skill registrations for this peer
- `DiscoverBySkill` — finds agents by skill ID with optional tag filtering
- `Heartbeat` — renews TTL on existing registrations

### FederationService (2 RPCs)

Enables gossip-based registry synchronization across multiple relay servers.

```protobuf
service FederationService {
  rpc SyncRegistrations(SyncRegistrationsRequest) returns (SyncRegistrationsResponse);
  rpc PushRegistrations(PushRegistrationsRequest) returns (PushRegistrationsResponse);
}
```

- `SyncRegistrations` — pull registration updates since a given timestamp from a peer relay
- `PushRegistrations` — push local registration updates to a peer relay; uses LWW (Last-Writer-Wins) conflict resolution with version counters

## libp2p Protocols

AgentAnycast uses dedicated libp2p protocol streams:

| Protocol ID | Purpose |
|---|---|
| `/agentanycast/a2a/1.0` | A2A envelope exchange (tasks, status, artifacts) |
| `/agentanycast/card/1.0` | Agent Card exchange on peer connection |

- **Transport:** TCP, QUIC, and WebTransport (all supported simultaneously)
- **Security:** Noise_XX (mandatory, no plaintext path)
- **Multiplexing:** yamux (over TCP), native (over QUIC)

### Connection Flow

```
1. Peer A opens stream to Peer B on /agentanycast/a2a/1.0
2. Noise_XX handshake (mutual authentication)
3. A2AEnvelope exchange (protobuf-serialized, length-prefixed)
4. ACK for each envelope
```

### ACK and Retry

The router tracks ACKs for each envelope:

- **Retry strategy:** Exponential backoff — 2s, 4s, 8s (max 3 retries)
- **Deduplication:** LRU cache (1024 envelopes) prevents duplicate processing
- **Callback:** `MaxRetriesFunc` fires when retries are exhausted

## Offline Message Queue

When a target peer is unreachable, the daemon queues the message:

1. Serialize the `A2AEnvelope` to BoltDB
2. Monitor peer connectivity events
3. When the peer reconnects, flush queued messages in order
4. Remove from queue after receiving ACK

This provides **at-least-once delivery** semantics. Messages expire after a configurable TTL (default 24 hours). Applications should handle potential duplicate deliveries idempotently.

## HTTP Bridge Protocol

The HTTP Bridge translates between HTTP JSON-RPC (standard A2A) and P2P A2A envelopes:

### Inbound (HTTP → P2P)

```
HTTP Client                    Bridge                     P2P Agent
    │                            │                            │
    │── POST / (JSON-RPC) ──────►│                            │
    │                            │── A2AEnvelope ────────────►│
    │                            │◄── A2AEnvelope (response) ─│
    │◄── JSON-RPC response ──────│                            │
```

### Outbound (P2P → HTTP)

```
P2P Agent                     Bridge                    HTTP Agent
    │                            │                            │
    │── send_task(url=...) ─────►│                            │
    │                            │── POST / (JSON-RPC) ──────►│
    │                            │◄── JSON-RPC response ──────│
    │◄── A2AEnvelope (response) ─│                            │
```

### Agent Card Discovery

The bridge exposes `GET /.well-known/a2a-agent-card` which returns the local P2P agent's card translated to standard A2A JSON format.
