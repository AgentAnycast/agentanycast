<p align="center">
  <img src="docs/assets/logo.png" alt="AgentAnycast" width="50%">
</p>

<h1 align="center">AgentAnycast</h1>

<p align="center">
  <strong>ngrok + DNS for AI Agents.<br>Zero-config connectivity. Capability-based routing. End-to-end encrypted.</strong>
</p>

<p align="center">
  <a href="https://github.com/AgentAnycast/agentanycast-python"><img src="https://img.shields.io/pypi/v/agentanycast?label=Python%20SDK&color=blue" alt="PyPI"></a>
  <a href="https://github.com/AgentAnycast/agentanycast-ts"><img src="https://img.shields.io/npm/v/agentanycast?label=TypeScript%20SDK&color=blue" alt="npm"></a>
  <a href="https://github.com/AgentAnycast/agentanycast-node/releases"><img src="https://img.shields.io/github/v/release/AgentAnycast/agentanycast-node?label=Daemon" alt="Release"></a>
  <a href="#license"><img src="https://img.shields.io/badge/license-Apache%202.0%20%2F%20FSL-green" alt="License"></a>
</p>

---

AgentAnycast is a **decentralized P2P runtime for the [A2A protocol](https://github.com/a2aproject/A2A)**. One line of code makes your agent reachable from anywhere — no public IP, no VPN, no reverse proxy, no SSL certificates.

```bash
pip install agentanycast    # or: npm install agentanycast
```

## Why

The [A2A protocol](https://github.com/a2aproject/A2A) defines how agents collaborate — Agent Card, Task, Message, Artifact. But its transport layer requires every agent to be an HTTP server with a public URL. This excludes the majority of real-world agents:

- **Local agents** — Claude Code, Cursor, coding assistants on your laptop (behind NAT)
- **Corporate agents** — behind firewalls, can't expose endpoints to the internet
- **Privacy-sensitive agents** — routing prompts through a centralized gateway is unacceptable
- **Edge agents** — IoT devices, embedded systems without static IPs

No mainstream agent framework (CrewAI, LangGraph, AutoGen, OpenAI Agents SDK) solves cross-network agent communication. They all assume agents run in the same process, cluster, or cloud.

## What AgentAnycast Does

**Three things, done well:**

**1. Agent's ngrok** — one command, your agent is reachable

```bash
agentanycast demo
# Your agent is now reachable by any peer on the network.
```

**2. Agent's DNS** — find agents by what they do, not where they are

```python
# Don't need an address. Just describe what you need.
task = await node.send_task(skill="translate", message=msg)
```

**3. Agent's zero-trust network** — E2E encrypted, cryptographic identity

```
Agent A ◄──── Noise_XX (E2E encrypted) ────► Agent B
                       │
                 ┌─────┴─────┐
                 │   Relay    │  ← sees only ciphertext
                 └───────────┘
```

## Quick Start

### 30-second demo

```bash
pip install agentanycast

# Terminal 1 — start an echo agent
agentanycast demo

# Terminal 2 — send it a task
agentanycast send <PEER_ID> "Hello!"
```

### Python (server)

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

### Python (client)

```python
async with Node(card=card) as node:
    task = await node.send_task(
        peer_id="12D3KooW...",
        message={"role": "user", "parts": [{"text": "Hello!"}]},
    )
    result = await task.wait()
    print(result.artifacts[0].parts[0].text)  # "Echo: Hello!"
```

### TypeScript

```typescript
import { Node } from "agentanycast";

const node = new Node({
  card: { name: "Echo", skills: [{ id: "echo", description: "Echo" }] },
});
await node.start();

node.onTask(async (task) => {
  const text = task.messages.at(-1)?.parts[0]?.text ?? "";
  await task.complete([{ parts: [{ text: `Echo: ${text}` }] }]);
});

await node.serveForever();
```

Python and TypeScript agents interoperate seamlessly — same daemon, same protocol.

## Three Ways to Send a Task

```python
# 1. Direct — you know the agent
await node.send_task(peer_id="12D3KooW...", message=msg)

# 2. Anycast — you know what you need (the network finds the agent)
await node.send_task(skill="translate", message=msg)

# 3. HTTP Bridge — reach standard HTTP A2A agents from P2P
await node.send_task(url="https://agent.example.com", message=msg)
```

| Mode | When to use |
|---|---|
| **Direct** | You have the Peer ID. Point-to-point. |
| **Anycast** | You need a capability. The skill registry resolves the best agent. |
| **HTTP Bridge** | The target is a standard HTTP A2A agent (Google ADK, etc.). |

## How It Works

```
┌──────────────┐
│  Your App    │  Python or TypeScript
└──────┬───────┘
       │ gRPC (local)
┌──────▼───────┐
│  Daemon      │  Go binary, auto-managed
│  (libp2p)    │  NAT traversal + Noise_XX encryption
└──────┬───────┘
       │ TCP / QUIC
┌──────▼───────┐
│  Network     │  mDNS (LAN) / Relay (WAN) / DHT (decentralized)
└──────────────┘
```

- **Local network** — agents discover each other via mDNS. Zero configuration.
- **Cross-network** — deploy your own relay (`docker-compose up -d`). Agents connect through it.
- **NAT traversal** — automatic: hole-punch first (DCUtR), relay fallback if needed.
- **Encryption** — Noise_XX by default. No plaintext path exists in the codebase.
- **Identity** — Ed25519 keypair → Peer ID. No CA, no DNS. Self-sovereign.

## Framework Adapters

Expose existing CrewAI or LangGraph workflows as P2P agents with one function call:

```python
from agentanycast.adapters.crewai import serve_crew
await serve_crew(my_crew, card=card, relay="...")

from agentanycast.adapters.langgraph import serve_graph
await serve_graph(my_graph, card=card, relay="...")
```

## Interoperability

| Standard | Support |
|---|---|
| **A2A** | Native — Agent Card, Task, Message, Artifact |
| **HTTP A2A** | HTTP Bridge — bidirectional P2P ↔ HTTP translation |
| **MCP** | Tool ↔ Skill mapping (`mcpToolToSkill` / `skillToMcpTool`) |
| **W3C DID** | `did:key` ↔ Peer ID conversion |
| **AGNTCY** | Agent directory integration for cross-ecosystem discovery |

## Deploy Your Own Relay

On a LAN, no relay is needed. For cross-network:

```bash
git clone https://github.com/AgentAnycast/agentanycast-relay.git
cd agentanycast-relay
docker-compose up -d
```

Then point agents to it:

```python
async with Node(card=card, relay="/ip4/<IP>/tcp/4001/p2p/12D3KooW...") as node:
    ...
```

The relay **cannot read your traffic** — all communication is end-to-end encrypted before reaching the relay. The relay also hosts a **skill registry** for capability-based routing.

## Repositories

| Repository | What it is | Language |
|---|---|---|
| **[agentanycast](https://github.com/AgentAnycast/agentanycast)** | This repo — docs, specs, discussions | — |
| **[agentanycast-python](https://github.com/AgentAnycast/agentanycast-python)** | Python SDK — `pip install agentanycast` | Python |
| **[agentanycast-ts](https://github.com/AgentAnycast/agentanycast-ts)** | TypeScript SDK — `npm install agentanycast` | TypeScript |
| **[agentanycast-node](https://github.com/AgentAnycast/agentanycast-node)** | Go daemon — P2P, encryption, A2A engine | Go |
| **[agentanycast-relay](https://github.com/AgentAnycast/agentanycast-relay)** | Relay server + skill registry | Go |
| **[agentanycast-proto](https://github.com/AgentAnycast/agentanycast-proto)** | Protocol Buffer definitions | Protobuf |

## Documentation

| Guide | Description |
|---|---|
| **[Getting Started](docs/getting-started.md)** | Installation, first agent, three addressing modes |
| **[Architecture](docs/architecture.md)** | Sidecar model, security, NAT traversal, discovery |
| **[Python SDK Reference](docs/python-sdk.md)** | Complete API documentation |
| **[Deployment](docs/deployment.md)** | Production relay, HTTP bridge, metrics, security |
| **[Protocol Reference](docs/protocol.md)** | A2A envelopes, task lifecycle, gRPC service |
| **[Examples](docs/examples.md)** | Patterns: anycast, adapters, streaming, LLM agents |

## What AgentAnycast Is Not

- **Not an agent framework** — use CrewAI, LangGraph, or whatever you like. We're the transport layer.
- **Not an orchestration engine** — we don't decide what agents do, we let them connect.
- **Not a centralized platform** — you own your relay, your keys, your data.

## Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

All repositories require a [CLA](CLA.md) signature — a bot will guide you on your first PR.

## License

| Component | License |
|---|---|
| SDKs (Python, TypeScript) + Proto | [Apache-2.0](https://www.apache.org/licenses/LICENSE-2.0) |
| Daemon + Relay | [FSL-1.1-Apache-2.0](https://fsl.software/) (auto-converts to Apache-2.0 after 2 years) |

## Community

- [GitHub Discussions](https://github.com/AgentAnycast/agentanycast/discussions) — Questions, ideas, show & tell
- [GitHub Issues](https://github.com/AgentAnycast/agentanycast/issues) — Bug reports, feature requests
