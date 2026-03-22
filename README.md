<p align="center">
  <img src="docs/assets/logo.png" alt="AgentAnycast" width="50%">
</p>

<h1 align="center">AgentAnycast</h1>

<p align="center">
  <strong>The connection layer for AI agents.</strong><br>
  <em>Connect AI agents across any network — zero config, encrypted, skill-based routing.</em>
</p>

<p align="center">
  <a href="https://pypi.org/project/agentanycast/"><img src="https://img.shields.io/pypi/v/agentanycast?label=Python&color=3776AB" alt="PyPI"></a>
  <a href="https://www.npmjs.com/package/agentanycast"><img src="https://img.shields.io/npm/v/agentanycast?label=TypeScript&color=3178C6" alt="npm"></a>
  <a href="https://github.com/AgentAnycast/agentanycast-node/releases"><img src="https://img.shields.io/github/v/release/AgentAnycast/agentanycast-node?label=Daemon&color=00ADD8" alt="Daemon"></a>
  <a href="#license"><img src="https://img.shields.io/badge/license-Apache%202.0%20%2F%20FSL-green" alt="License"></a>
  <a href="https://github.com/AgentAnycast/agentanycast/discussions"><img src="https://img.shields.io/github/discussions/AgentAnycast/agentanycast?label=Discussions&color=blue" alt="Discussions"></a>
</p>

---

AgentAnycast is the **connection layer** for AI agents — it solves discovery, identity, transport, and protocol bridging so that agents can find and talk to each other across any network. Laptops behind NAT, corporate firewalls, or across the internet — with automatic encryption, NAT traversal, and skill-based routing.

```bash
pip install agentanycast    # SDK — build P2P agents in Python or TypeScript
uvx agentanycast-mcp        # MCP Server — use P2P agents from Claude, Cursor, VS Code, etc.
```

## Quick Start

```bash
pip install agentanycast

# Terminal 1 — start an echo agent
agentanycast demo

# Terminal 2 — send it a task
agentanycast send <PEER_ID> "Hello!"
```

Build an agent in Python:

```python
from agentanycast import Node, AgentCard, Skill

card = AgentCard(
    name="EchoAgent",
    description="Echoes back any message",
    skills=[Skill(id="echo", description="Echo the input")],
)

async with Node(card=card) as node:
    @node.on_task
    async def handle(task):
        text = task.messages[-1].parts[0].text
        await task.complete(artifacts=[{"parts": [{"text": f"Echo: {text}"}]}])

    await node.serve_forever()
```

Send a task to another agent:

```python
async with Node(card=card) as node:
    task = await node.send_task(
        peer_id="12D3KooW...",
        message={"role": "user", "parts": [{"text": "Hello!"}]},
    )
    result = await task.wait()
    print(result.artifacts[0].parts[0].text)  # "Echo: Hello!"
```

> Python and TypeScript agents interoperate out of the box — same protocol, same daemon. See the [TypeScript SDK](https://github.com/AgentAnycast/agentanycast-ts) for JS/TS usage.

## Why AgentAnycast

[A2A](https://github.com/a2aproject/A2A) is the emerging standard for agent-to-agent communication, but it requires every agent to be an HTTP server with a public URL. This excludes agents on laptops (behind NAT), inside corporate firewalls, or in any environment where routing prompts through a centralized gateway is unacceptable. No mainstream agent framework solves cross-network agent communication — they all assume agents share the same process or the same cloud.

AgentAnycast solves this at the transport layer:

- **Zero-config connectivity** — `pip install` and your agent is reachable. The Go daemon is auto-managed.
- **Skill-based routing** — send tasks by capability, not by address. The network finds the right agent.
- **End-to-end encrypted** — Noise_XX protocol. Even relay servers see only ciphertext. No plaintext path exists in the codebase.
- **Automatic NAT traversal** — hole-punching (DCUtR) first, relay fallback if needed. Works from behind any firewall.
- **Decentralized identity** — Ed25519 keys, W3C DID (`did:key`, `did:web`), Verifiable Credentials. No CA, no accounts.
- **MCP server built in** — the daemon runs as an MCP server for Claude Desktop, Cursor, ChatGPT, and other AI tools.

## Three Ways to Send a Task

AgentAnycast supports three addressing modes, so you can reach any agent regardless of how it's connected:

```python
# 1. Direct — you know the agent's Peer ID
await node.send_task(peer_id="12D3KooW...", message=msg)

# 2. By skill — you know what you need, the network finds the right agent
await node.send_task(skill="translate", message=msg)

# 3. HTTP Bridge — reach a standard HTTP A2A agent from the P2P network
await node.send_task(url="https://agent.example.com", message=msg)
```

| Mode | When to use |
|---|---|
| **Direct** | You have the agent's Peer ID. Point-to-point communication. |
| **By skill** | You need a capability (e.g., "translate"). The skill registry finds an agent for you. |
| **HTTP Bridge** | The target is a standard HTTP A2A agent (Google ADK, etc.). The bridge translates between HTTP and P2P. |

## How It Works

AgentAnycast uses a sidecar architecture: a thin SDK communicates over gRPC with a local Go daemon that handles all the P2P networking, encryption, and A2A protocol logic.

<p align="center">
  <img src="docs/assets/architecture.svg" alt="Architecture" width="100%">
</p>

- **On a local network** — agents discover each other automatically via mDNS. Nothing to configure.
- **Across networks** — deploy a self-hosted relay. Agents connect through it, and the relay **cannot read traffic** — all communication is end-to-end encrypted.
- **Behind NAT** — the daemon automatically tries hole-punching (DCUtR) first, then falls back to relay if needed.
- **Identity** — each agent gets an Ed25519 key pair. No certificates, no DNS setup. The key *is* the identity. It maps to W3C DIDs (`did:key`, `did:web`) for cross-ecosystem interoperability.

## Framework Adapters

Turn existing agent frameworks into P2P agents with one function call:

```python
from agentanycast.adapters.crewai import serve_crew
from agentanycast.adapters.langgraph import serve_graph
from agentanycast.adapters.adk import serve_adk_agent
from agentanycast.adapters.openai_agents import serve_openai_agent
from agentanycast.adapters.claude_agent import serve_claude_agent
from agentanycast.adapters.strands import serve_strands_agent

await serve_crew(my_crew, card=card, relay="...")          # CrewAI
await serve_graph(my_graph, card=card, relay="...")         # LangGraph
await serve_adk_agent(my_agent, card=card, relay="...")     # Google ADK
await serve_openai_agent(my_agent, card=card, relay="...")  # OpenAI Agents SDK
await serve_claude_agent(prompt_template="...", card=card, relay="...")  # Claude Agent SDK
await serve_strands_agent(my_agent, card=card, relay="...")              # AWS Strands
```

## Interoperability

AgentAnycast is designed to work with the broader agent ecosystem, not as an isolated silo:

| Ecosystem | Integration |
|---|---|
| [**A2A**](https://github.com/a2aproject/A2A) | Native implementation — Agent Card, Task, Message, Artifact |
| **HTTP A2A** | HTTP Bridge translates between P2P and HTTP bidirectionally |
| [**MCP**](https://modelcontextprotocol.io/) | Daemon runs as MCP server (stdio + HTTP); SDK maps MCP tools ↔ A2A skills |
| [**ANP**](https://www.w3.org/community/anp/) | ANP Bridge for Agent Network Protocol interop |
| **W3C DID** | `did:key`, `did:web`, `did:dns` identity + Verifiable Credentials |
| [**AGNTCY**](https://github.com/agntcy) | Agent directory integration + OASF record conversion |

## MCP Server — Use from Any AI Tool

Don't want to write code? Install the MCP server and use P2P agents directly from Claude Desktop, Cursor, VS Code, or any MCP-compatible AI tool:

```bash
uvx agentanycast-mcp
```

Add to your AI tool's config (e.g., Claude Desktop `claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "agentanycast": {
      "command": "uvx",
      "args": ["agentanycast-mcp"]
    }
  }
}
```

Then ask your AI assistant: *"Find agents that can translate Japanese"* or *"Send 'summarize this' to the translate agent"*.

Works with: Claude Desktop/Code, Cursor, VS Code + Copilot, Windsurf, JetBrains AI, Gemini CLI, Amazon Q, Cline, Continue, ChatGPT (HTTP mode), and more. See the [MCP Server docs](https://github.com/AgentAnycast/agentanycast-mcp) for all platform configs.

## Comparison

| Feature | AgentAnycast | Standard A2A | agentgateway | Tailscale Aperture |
|---------|-------------|-------------|-------------|-----------|
| NAT Traversal | ✅ Automatic | ❌ Requires public IP | ❌ Requires public IP | ✅ Via DERP relays |
| Encryption | ✅ E2E through relays (Noise_XX) | TLS (terminates at server) | TLS (proxy decrypts) | ✅ E2E (WireGuard) |
| Skill-based Routing | ✅ Anycast by capability | ❌ URL-based only | ❌ Static config | ❌ |
| MCP Server | ✅ Built-in (6 tools) | ❌ | ✅ | ❌ |
| Decentralized | ✅ P2P + DHT | ❌ Central server | ❌ Central gateway | ❌ Coord server |
| Setup | `pip install` + 3 lines | HTTP server + public URL | Gateway deployment | Account + client install |

## Self-Hosted Relay

On a LAN, no relay is needed — agents find each other automatically via mDNS.

For agents on different networks, deploy a relay on any machine with a public IP:

```bash
git clone https://github.com/AgentAnycast/agentanycast-relay.git && cd agentanycast-relay
docker-compose up -d
```

Then point your agents to it:

```python
async with Node(card=card, relay="/ip4/<IP>/tcp/4001/p2p/12D3KooW...") as node:
    ...
```

The relay is a **zero-knowledge forwarder** — it only passes encrypted bytes. It also hosts a **skill registry** for capability-based agent discovery, with optional **multi-relay federation** for global discovery across relay clusters.

## Repositories

| Repository | Description |
|---|---|
| **[agentanycast](https://github.com/AgentAnycast/agentanycast)** | Documentation, examples, discussions — **start here** |
| **[agentanycast-mcp](https://github.com/AgentAnycast/agentanycast-mcp)** | MCP server — `uvx agentanycast-mcp` — use from Claude, Cursor, VS Code, etc. |
| **[agentanycast-python](https://github.com/AgentAnycast/agentanycast-python)** | Python SDK — `pip install agentanycast` |
| **[agentanycast-ts](https://github.com/AgentAnycast/agentanycast-ts)** | TypeScript SDK — `npm install agentanycast` |
| **[agentanycast-node](https://github.com/AgentAnycast/agentanycast-node)** | Go daemon — P2P networking, encryption, A2A engine |
| **[agentanycast-relay](https://github.com/AgentAnycast/agentanycast-relay)** | Relay server + skill registry + multi-relay federation |
| **[agentanycast-proto](https://github.com/AgentAnycast/agentanycast-proto)** | Protocol Buffer definitions — single source of truth |

## Documentation

| Guide | What you'll learn |
|---|---|
| **[Getting Started](docs/getting-started.md)** | Install, run your first agent, connect two agents |
| **[Architecture](docs/architecture.md)** | Sidecar model, security, NAT traversal, MCP, federation |
| **[Python SDK Reference](docs/python-sdk.md)** | Complete API docs — Node, AgentCard, TaskHandle, DID, adapters |
| **[Deployment Guide](docs/deployment.md)** | Production relay, HTTP bridge, MCP server, metrics, security |
| **[Protocol Reference](docs/protocol.md)** | Wire format, task lifecycle, 22 RPCs across 3 gRPC services |
| **[Examples](docs/examples.md)** | Patterns: anycast, adapters, streaming, LLM-powered agents |
| **[TypeScript SDK Reference](docs/typescript-sdk.md)** | Complete TypeScript API reference |
| **[FAQ & Troubleshooting](docs/faq.md)** | Common questions and solutions |
| **[Version Coordination](docs/versioning.md)** | Cross-repo release process and compatibility |

## Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines. All repositories require a [CLA](CLA.md) signature — a bot will guide you on your first PR.

## License

SDKs and Proto definitions are [Apache-2.0](https://www.apache.org/licenses/LICENSE-2.0). Daemon and Relay are [FSL-1.1-Apache-2.0](https://fsl.software/) — each release auto-converts to Apache-2.0 after two years.

## Community

- [GitHub Discussions](https://github.com/AgentAnycast/agentanycast/discussions) — questions, ideas, show & tell
- [GitHub Issues](https://github.com/AgentAnycast/agentanycast/issues) — bug reports, feature requests
