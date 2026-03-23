# agentgateway Integration

[agentgateway](https://agentgateway.dev/) is a Linux Foundation project that provides an AI-native gateway for MCP and A2A protocol-aware routing. AgentAnycast integrates with agentgateway as a complementary backend, extending its reach to agents behind NATs and across different networks.

## Architecture

agentgateway handles centralized traffic management (authentication, rate limiting, RBAC), while AgentAnycast provides decentralized connectivity (NAT traversal, P2P routing, E2E encryption).

```
External Agent / MCP Client
    │
    ▼
agentgateway (centralized gateway)
    │  Auth, RBAC, rate limiting, observability
    ▼
AgentAnycast HTTP Bridge
    │  NAT traversal, P2P routing, E2E encryption
    ▼
Remote Agents (behind NAT, different networks)
```

## Use Case 1: A2A Backend

Route A2A agent requests through agentgateway to AgentAnycast for cross-network delivery.

### agentgateway configuration

```yaml
binds:
  - port: 3000
listeners:
  - routes:
      - policies:
          a2a: {}
        backends:
          - host: agentanycast-node:8080
```

### AgentAnycast setup

```bash
# Start the AgentAnycast daemon with HTTP Bridge enabled
agentanycastd --bridge-listen :8080 --log-level info
```

### Docker Compose

```yaml
version: "3.8"
services:
  agentgateway:
    image: ghcr.io/agentgateway/agentgateway:latest
    ports:
      - "3000:3000"
    volumes:
      - ./agentgateway-config.yaml:/app/config.yaml
    depends_on:
      - agentanycast-node

  agentanycast-relay:
    image: agentanycast/relay:latest
    command: ["--listen", "/ip4/0.0.0.0/tcp/4001", "--registry-listen", "0.0.0.0:50052"]

  agentanycast-node:
    image: agentanycast/node:latest
    command:
      - --bridge-listen
      - ":8080"
      - --bootstrap-peers
      - "/dns4/agentanycast-relay/tcp/4001"
    depends_on:
      - agentanycast-relay
```

## Use Case 2: MCP Tool Federation

agentgateway aggregates local MCP servers with remote AgentAnycast-connected MCP servers.

### agentgateway configuration

```yaml
binds:
  - port: 3000
listeners:
  - routes:
      - policies:
          cors:
            allowOrigins: ["*"]
            allowHeaders: ["mcp-protocol-version", "content-type"]
            exposeHeaders: ["Mcp-Session-Id"]
        backends:
          - mcp:
              targets:
                # Local MCP server (filesystem access)
                - name: filesystem
                  stdio:
                    cmd: npx
                    args: ["@modelcontextprotocol/server-filesystem", "/workspace"]
                # Remote MCP server via AgentAnycast
                - name: remote-agents
                  http:
                    url: http://agentanycast-node:8080/mcp
```

This configuration federates local and remote MCP tools into a single endpoint.

## Use Case 3: Enterprise Deployment

For enterprise environments with existing agentgateway infrastructure:

```yaml
binds:
  - port: 3000
listeners:
  - routes:
      - policies:
          a2a: {}
          auth:
            jwt:
              issuer: "https://auth.company.com"
              audience: "agents.company.com"
          rateLimit:
            local:
              requests: 100
              unit: second
        backends:
          - host: agentanycast-node:8080
```

agentgateway handles JWT authentication and rate limiting, while AgentAnycast provides:
- NAT traversal for agents on different networks
- E2E encryption (Noise_XX + NaCl box) beyond TLS termination
- Skill-based anycast routing across the P2P network
- DID-based agent identity

## When to Use Each

| Scenario | Use agentgateway | Use AgentAnycast | Use Both |
|----------|-----------------|------------------|----------|
| Datacenter agents | ✅ | | |
| Cross-network agents | | ✅ | |
| Enterprise with NAT | | | ✅ |
| MCP tool aggregation | ✅ | | ✅ (for remote tools) |
| Zero-config P2P | | ✅ | |
| Centralized auth/RBAC | ✅ | | ✅ |

## Further Reading

- [agentgateway Documentation](https://agentgateway.dev/docs/)
- [AgentAnycast HTTP Bridge](../deployment.md)
- [AgentAnycast Security Model](../security-model.md)
