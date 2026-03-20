# RFC: Browser Runtime for AgentAnycast

**Status:** Draft
**Authors:** AgentAnycast Team
**Created:** 2026-03-19
**Target Release:** v0.9

## Summary

Enable AgentAnycast agents to run directly in web browsers, allowing browser-based AI applications to participate in the P2P agent network without requiring a locally installed daemon.

## Motivation

Currently, AgentAnycast requires a native Go daemon (`agentanycastd`) for all P2P networking. This creates a barrier for:

- **Web-based AI tools** that want to discover and communicate with agents
- **Lightweight demos and sandboxes** where users cannot install native binaries
- **Mobile web applications** that need agent-to-agent communication

A browser runtime would extend AgentAnycast's reach to any platform with a modern web browser.

## Architecture

### Approach: WebTransport Gateway at Relay

Rather than reimplementing libp2p in the browser (which would require porting Noise_XX, the gRPC client, and the full protocol stack to JavaScript), we propose a **WebTransport Gateway** model:

```
Browser Agent                Relay                    Native Agent
┌──────────┐    WebTransport   ┌──────────┐   libp2p    ┌──────────┐
│  Browser  │ ←──────────────→ │  Relay   │ ←─────────→ │  Daemon  │
│  SDK      │  (QUIC/H3)      │  Gateway │  (Noise)    │          │
└──────────┘                   └──────────┘              └──────────┘
```

1. The browser SDK connects to a relay via **WebTransport** (QUIC-based, browser-native)
2. The relay acts as a protocol translator: WebTransport ↔ libp2p
3. End-to-end encryption is maintained using **TLS 1.3** (WebTransport) on the browser→relay leg, and **Noise_XX** on the relay→peer leg
4. The relay holds the browser agent's registration and proxies A2A messages

### Why Not Full libp2p in Browser?

We evaluated and rejected a full browser-native libp2p implementation:

| Component | Browser Support | Effort |
|-----------|----------------|--------|
| libp2p transport | WebTransport only (no TCP/QUIC direct) | Medium |
| Noise_XX in JS | No mature library; `@noble/ed25519` exists but no Noise framework | High |
| gRPC client | `@grpc/grpc-js` requires Node.js (`http2`, `net`) | Very High |
| protobuf | `protobuf-es` works in browser | Low |
| Identity/keys | `@noble/ed25519` works in browser | Low |

The gRPC dependency alone would require rewriting the daemon communication layer. The WebTransport gateway approach avoids this entirely.

### Browser SDK API Surface

The browser SDK would expose a subset of the full Node.js/Python SDK:

```typescript
// Browser SDK (subset of full SDK)
class BrowserNode {
  // Connect to relay via WebTransport
  async connect(relayUrl: string): Promise<void>;

  // Register agent card
  async register(card: AgentCard): Promise<void>;

  // Discovery
  async discover(skillId: string): Promise<AgentEndpoint[]>;

  // Send/receive tasks (proxied through relay)
  async sendTask(target: string, message: Message): Promise<TaskHandle>;
  onTask(handler: (task: IncomingTask) => Promise<void>): void;

  // Cleanup
  async disconnect(): Promise<void>;
}
```

**Not supported in browser:**
- Direct peer-to-peer connections (all traffic proxied through relay)
- Noise_XX encryption (TLS 1.3 via WebTransport instead)
- MCP integration (browser has no local MCP server)

### Relay Changes Required

The relay already supports WebTransport via `--enable-webtransport`. Additional work:

1. **WebTransport A2A Protocol Handler**: Accept A2A envelopes over WebTransport streams (not libp2p streams)
2. **Session Management**: Track browser sessions, handle reconnection
3. **Registration Proxy**: Register browser agents in the skill registry on their behalf
4. **Message Routing**: Forward A2A messages between WebTransport sessions and libp2p peers

### Security Considerations

- Browser→Relay: TLS 1.3 (built into WebTransport)
- Relay→Peer: Noise_XX (existing)
- The relay is a trusted intermediary for browser agents (similar to a traditional server)
- Browser agents cannot verify peer identity directly (no Noise handshake)
- Rate limiting and authentication required to prevent relay abuse

## Implementation Estimate

| Phase | Work | Estimate |
|-------|------|----------|
| WebTransport protocol handler in relay | New stream handler, session management | 2-3 weeks |
| Browser SDK core | Connect, register, send/receive | 2 weeks |
| Message routing bridge | WebTransport ↔ libp2p envelope translation | 1-2 weeks |
| Testing and documentation | Integration tests, API docs, examples | 1-2 weeks |
| **Total** | | **6-9 weeks** |

## Alternatives Considered

### 1. WebRTC Data Channels
- Pro: True P2P between browsers
- Con: Still needs signaling server; NAT traversal unreliable; no Noise_XX

### 2. WebSocket Proxy
- Pro: Wider browser support than WebTransport
- Con: No multiplexing; higher latency; TCP head-of-line blocking

### 3. HTTP Polling
- Pro: Works everywhere
- Con: High latency; not suitable for real-time agent communication

## Decision

Deferred to v0.9. The WebTransport gateway approach is the most viable path forward, but it requires significant relay-side work that should not block v0.7 (observability) or v0.8 (enterprise readiness) milestones.

## Open Questions

1. Should browser agents get `did:key` identities, or are they anonymous/session-scoped?
2. How to handle browser agent offline → online transitions?
3. Should the browser SDK be a separate npm package or part of `agentanycast`?
4. What authentication mechanism for browser → relay connections?
