# Migration Guide

This guide covers upgrading between AgentAnycast versions. For general version coordination across repositories, see [Cross-Repo Version Coordination](versioning.md).

## General Upgrade Procedure

Follow these steps for any version upgrade:

1. **Back up the identity key** -- the key at `~/.agentanycast/key` is your agent's permanent identity:
   ```bash
   cp ~/.agentanycast/key ~/.agentanycast/key.backup
   ```

2. **Stop the daemon** -- if the SDK manages the daemon, stop the SDK application first. For standalone daemons:
   ```bash
   systemctl stop agentanycastd
   # or: docker compose down
   ```

3. **Upgrade the binary** -- replace the daemon and/or relay binary:
   ```bash
   # SDK-managed: upgrade the SDK package
   pip install --upgrade agentanycast     # Python
   npm install agentanycast@latest        # TypeScript

   # Standalone daemon: download the new binary
   curl -LO https://github.com/AgentAnycast/agentanycast-node/releases/latest/download/agentanycastd-$(uname -s)-$(uname -m)
   chmod +x agentanycastd-* && mv agentanycastd-* /usr/local/bin/agentanycastd

   # Relay: pull the new image or rebuild
   docker pull agentanycast/relay:latest
   ```

4. **Start and verify health** -- confirm the upgraded component is operational:
   ```bash
   systemctl start agentanycastd
   agentanycastd --version
   curl -sf http://localhost:9090/health | jq .status
   ```

5. **Verify peer connectivity** -- check that the node connects to peers and the relay:
   ```bash
   curl -s http://localhost:9090/health | jq .
   # Confirm connected_peers > 0 (if bootstrap peers are configured)
   ```

## Breaking Changes

AgentAnycast follows a strict additive-only policy for its protobuf API. Proto fields are never removed or renamed, and new RPC methods are backward compatible. As of v0.8, **there are no breaking changes** between any released versions.

The compatibility guarantee:

- Older SDKs work with newer daemons (new fields are ignored by old clients).
- Newer SDKs work with older daemons (new fields have default zero values).
- `buf breaking` enforces this in CI for every proto change.

## v0.5 to v0.6

**Release highlights:** MCP bridging, DID extensions (`did:web`, `did:dns`), streaming artifacts.

### What Changed

- **MCP Server** -- the daemon can now serve as an MCP (Model Context Protocol) server, exposing P2P capabilities as tools for AI assistants. Supports both stdio and Streamable HTTP transports.
- **DID Extensions** -- in addition to `did:key`, agents can now use `did:web` and `did:dns` identifiers for web-based and DNS-based identity resolution.
- **Streaming Artifacts** -- large artifacts can be delivered in chunks via `StreamStart`, `StreamChunk`, and `StreamEnd` envelope types, avoiding memory pressure on both sender and receiver.
- **MCP Tool-Skill Mapping** -- the `mcp.py` / `mcp.ts` modules provide bidirectional conversion between MCP Tools and A2A Skills.

### Upgrade Steps

No breaking changes. Add the new configuration sections if you want to enable the new features:

```toml
# Enable MCP server (Streamable HTTP mode)
[mcp]
enabled = true
listen = ":3000"

# Enable DID extensions
[identity]
did_web = "did:web:example.com:agents:myagent"
# did_dns_domain = "example.com"
```

For SDK users, MCP bridging is available through new module imports:

```python
# Python
from agentanycast.mcp import skill_to_tool, tool_to_skill
```

```typescript
// TypeScript
import { skillToTool, toolToSkill } from "agentanycast/mcp";
```

## v0.6 to v0.7

**Release highlights:** namespace support, transport abstraction layer, framework adapters.

### What Changed

- **Transport Abstraction** -- the internal architecture now uses a pluggable transport interface. libp2p remains the default, but NATS can be configured as an alternative transport for environments with existing message broker infrastructure.
- **Framework Adapters** -- the Python SDK gained optional adapters for CrewAI and LangGraph, enabling AgentAnycast as a transport layer for multi-agent frameworks.
- **ANP Bridge** -- W3C Agent Network Protocol interoperability via a dedicated HTTP endpoint (`/agent/ad.json`, `/agent/interface.json`, `/agent/rpc`).
- **Verifiable Credentials** -- Agent Cards can carry W3C Verifiable Credentials (VC Data Model v2.0) for skill attestation, using `Ed25519Signature2020` proof suite.

### Upgrade Steps

No breaking changes. To enable the new transport or adapters:

```toml
# Enable NATS transport (optional, alongside libp2p)
[transport.nats]
enabled = true
broker = "nats://localhost:4222"
subject_prefix = "agent."

# Enable ANP bridge
[anp]
enabled = true
listen = ":8090"
```

For Python framework adapters, install the optional dependency group:

```bash
pip install agentanycast[crewai]    # CrewAI adapter
pip install agentanycast[langgraph] # LangGraph adapter
pip install agentanycast[adapters]  # All adapters
```

## v0.7 to v0.8

**Release highlights:** multi-tenant isolation (ACL + rate limiting), NATS transport maturity, audit logging.

### What Changed

- **Access Control (ACL)** -- skill-level access control based on source identity (`did:key`, `did:web`). Rules support glob patterns and follow first-match-wins semantics with default-deny when rules are configured.
- **Per-Source Rate Limiting** -- token bucket rate limiting per source identity, with configurable defaults and per-source overrides.
- **Audit Logging** -- JSON Lines audit trail of all access control decisions (allow, deny, rate_limit) for compliance and security analysis.
- **NATS Transport Maturity** -- TLS support, authentication (`auth_user`/`auth_pass`), and per-agent subject prefixes for multi-tenant NATS deployments.
- **OpenTelemetry Tracing** -- distributed tracing with OTLP export and W3C Trace Context propagation across A2A messages.
- **Relay Federation** -- multiple relays can synchronize their skill registries for global agent discovery via gossip protocol.

### Upgrade Steps

No breaking changes. To enable the new security features:

```toml
[policy]
audit_log_path = "/var/log/agentanycast/audit.jsonl"

# Access control rules (first match wins; default-deny when rules exist)
[[policy.acl]]
source = "did:web:trusted.example.com:*"
skill = "*"
allow = true

[[policy.acl]]
source = "*"
skill = "internal-*"
allow = false

[[policy.acl]]
source = "*"
skill = "*"
allow = true

# Rate limiting
[policy.rate_limit]
default_rps = 100

# OpenTelemetry tracing
[telemetry]
enabled = true
otlp_endpoint = "localhost:4317"
sample_rate = 0.1
```

For relay federation, add `--federation-peers` when starting each relay:

```bash
./agentanycast-relay \
    --key /data/relay.key \
    --federation-peers "relay2.example.com:50052,relay3.example.com:50052" \
    --federation-sync-interval 10s
```

## Version Compatibility Matrix

| Proto | Node | Relay | Python SDK | TypeScript SDK |
|---|---|---|---|---|
| v0.5.x | v0.5.x | v0.5.x | v0.5.x | v0.5.x |
| v0.6.x | v0.6.x | v0.6.x | v0.6.x | v0.6.x |
| v0.7.x | v0.7.x | v0.7.x | v0.7.x | v0.7.x |
| v0.8.x | v0.8.x | v0.8.x | v0.8.x | v0.8.x |

Within a minor version series, all patch releases are backward compatible. See [Cross-Repo Version Coordination](versioning.md) for the full compatibility policy.
