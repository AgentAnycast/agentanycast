# Glossary

Key terms and concepts used throughout the AgentAnycast documentation.

## A

### A2A Protocol

The Agent-to-Agent protocol. An open standard for inter-agent communication that defines how agents exchange tasks, messages, and artifacts. AgentAnycast implements A2A over both P2P (libp2p) and HTTP transports, using a protobuf-based envelope format with 11 envelope types including streaming support.

### Agent Card

A JSON descriptor that advertises an agent's identity, capabilities, and connection information. Agent cards follow the A2A standard and include a P2P extension with `did_key` for decentralized identity. Cards are automatically exchanged between peers upon connection and stored persistently for offline reference.

### Anycast

A routing mode where a task is sent to a skill identifier rather than a specific peer. The anycast router discovers agents offering that skill (via DHT, relay registry, or both), selects one using a configurable strategy (e.g., random), and delivers the task. This decouples the sender from knowing which specific agent will handle the request.

### Audit Logging

A security feature that records all access control decisions (allow, deny, rate-limit) as JSON Lines to a file. Each event includes timestamp, source DID, target, skill, transport, and envelope ID. Enabled via `policy.audit_log_path` in the daemon configuration.

### AutoNAT

A libp2p protocol that allows a node to determine whether it is reachable from the public internet. Relay servers provide AutoNAT service to help peers detect their NAT type and decide whether hole punching or relay-based communication is needed.

## C

### Circuit Relay

A libp2p protocol (v2) that allows two peers behind NATs to communicate through an intermediary relay server. The relay enforces resource limits (connection duration, data transfer, reservations per peer/IP) to prevent abuse. AgentAnycast relay servers enable Circuit Relay v2 by default.

### Connection Core

The pluggable adapter architecture introduced in v0.7 of the node daemon. It provides a unified interface for protocol adapters (A2A, ANP) and transport adapters (libp2p, HTTP, NATS), along with enterprise capabilities such as ACL enforcement, rate limiting, and audit logging.

## D

### DCUtR

Direct Connection Upgrade through Relay. A libp2p protocol that enables two peers, both behind NATs, to establish a direct connection by coordinating through a relay server. It performs NAT hole punching after an initial relayed connection is established.

### DHT

Distributed Hash Table. A decentralized data structure used for peer discovery without relying on a central registry. AgentAnycast uses the Kademlia DHT implementation from libp2p to advertise and discover skills across the network. DHT mode can be set to `auto`, `server`, or `client`.

### DID

Decentralized Identifier. A W3C standard for self-sovereign identity. AgentAnycast supports three DID methods:

- **did:key** -- Derived directly from the agent's Ed25519 public key. Every agent automatically has a `did:key` identity. Supports bidirectional conversion with libp2p Peer IDs.
- **did:web** -- Resolved via HTTPS to a domain-hosted DID Document. Configured via `identity.did_web` in the daemon config.
- **did:dns** -- Resolved via DNS TXT records at `_did.<domain>`. Configured via `identity.did_dns_domain`.

## E

### Envelope

The wire-format wrapper for all A2A messages sent between peers. Defined in `a2a_models.proto`, the `A2AEnvelope` supports 11 message types including task send/status/cancel, card exchange, acknowledgments, and streaming operations.

## G

### gRPC

The communication channel between the SDK (Python or TypeScript) and the local daemon process. The daemon exposes 16 RPC methods over a Unix domain socket (default: `~/.agentanycast/daemon.sock`) or TCP. The SDK sends requests via gRPC and receives streamed responses for incoming tasks.

## L

### libp2p

A modular peer-to-peer networking framework that provides the transport layer for AgentAnycast. It handles TCP and QUIC connections, Noise encryption, stream multiplexing (yamux), peer discovery (mDNS, DHT), NAT traversal (AutoNAT, DCUtR), and Circuit Relay. The node daemon uses libp2p v0.47+.

## M

### MCP

Model Context Protocol. A standard for exposing tools to AI assistants. AgentAnycast provides MCP integration in two ways: (1) the daemon can run as an MCP server (stdio or Streamable HTTP), exposing P2P networking as tools; (2) the `agentanycast-mcp` package provides a standalone MCP server. MCP tools can also be mapped to A2A skills for cross-protocol bridging.

### mDNS

Multicast DNS. A zero-configuration discovery protocol that allows agents on the same local network to find each other without a relay server or DHT. Enabled by default in the daemon (`enable_mdns = true`). Useful for development and same-LAN deployments.

## N

### NAT Traversal

The set of techniques used to establish direct peer connections when one or both peers are behind a Network Address Translation device. AgentAnycast combines three complementary mechanisms: AutoNAT (reachability detection), DCUtR (coordinated hole punching), and Circuit Relay v2 (fallback relaying).

### NATS

A cloud-native messaging system used as an optional transport adapter in AgentAnycast. When enabled, agents can communicate through a NATS broker in addition to (or instead of) direct libp2p connections. Configured via `transport.nats` in the daemon config or the `--nats-broker` flag.

### Noise Protocol

The encryption protocol used for all peer-to-peer connections. AgentAnycast uses the Noise_XX handshake pattern, which provides mutual authentication and forward secrecy. Both peers exchange their static public keys during the handshake, and all subsequent communication is end-to-end encrypted.

## O

### Offline Queue

A persistent message queue (backed by BoltDB) that stores outbound A2A messages when the target peer is unreachable. Messages are automatically flushed and delivered when the peer reconnects. Messages expire after a configurable TTL (default: 24 hours).

## P

### Peer ID

A unique identifier for each node in the network, derived from the node's Ed25519 public key using multihash encoding. Peer IDs are the fundamental addressing unit in libp2p and can be bidirectionally converted to `did:key` identifiers.

### Protocol Adapter

A Connection Core component that handles serialization and deserialization for a specific agent protocol. Built-in adapters include A2A (protobuf envelopes) and ANP (JSON-RPC). Protocol adapters are registered with the Connection Core at startup.

## R

### Relay

A publicly reachable server (`agentanycast-relay`) that provides three services: Circuit Relay v2 for NAT traversal, a skill registry for anycast discovery, and a bootstrap node for initial peer discovery. Relay servers can be federated for multi-region deployments.

## S

### Sidecar Architecture

The deployment pattern used by AgentAnycast. A long-lived Go daemon (`agentanycastd`) handles all P2P networking, encryption, and protocol logic, while thin SDK layers (Python, TypeScript) communicate with it over gRPC. This separates networking concerns from application logic and allows the daemon to maintain persistent connections across SDK restarts.

### Skill

A named capability that an agent advertises in its Agent Card. Skills have an ID, description, and optional tags. They serve as the routing key for anycast -- a sender can target a skill ID and the network will route the task to an available agent offering that skill.

## T

### Task

The primary unit of work in the A2A protocol. A task contains messages (with text, file, and data parts), transitions through states (submitted, working, input-required, completed, failed, canceled), and produces artifacts upon completion. Tasks support streaming delivery of large artifacts via chunked transfers.

### Task Handle

An SDK-side object returned by `send_task()` that represents an in-flight task. It provides methods to wait for completion, check status, cancel the task, and receive streaming updates. The handle abstracts the underlying gRPC streaming communication with the daemon.

### Transport Adapter

A Connection Core component that handles the physical delivery of messages over a specific network transport. Built-in adapters include libp2p (direct P2P), HTTP (bridge for standard A2A agents), and NATS (broker-based messaging). Transport adapters are registered with the Connection Core at startup.

## W

### W3C Trace Context

A W3C standard for distributed trace propagation. AgentAnycast uses the OpenTelemetry implementation of W3C Trace Context to propagate trace IDs across A2A messages, enabling end-to-end distributed tracing through the `traceparent` and `tracestate` headers.

### WebTransport

A QUIC-based transport protocol that enables browser-compatible peer connections. Optionally enabled on the daemon (`--enable-webtransport`) and relay server. WebTransport runs alongside TCP and QUIC on the same port using UDP.
