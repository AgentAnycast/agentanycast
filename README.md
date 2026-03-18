<p align="center">
  <img src="docs/assets/logo.png" alt="AgentAnycast" width="50%">
</p>

<h1 align="center">AgentAnycast</h1>

<p align="center">
  <strong>Connect AI agents across any network.<br>No public IP. No VPN. No configuration.</strong>
</p>

<p align="center">
  <a href="https://github.com/AgentAnycast/agentanycast-python"><img src="https://img.shields.io/pypi/v/agentanycast?label=Python%20SDK&color=blue" alt="PyPI"></a>
  <a href="https://github.com/AgentAnycast/agentanycast-ts"><img src="https://img.shields.io/npm/v/agentanycast?label=TypeScript%20SDK&color=blue" alt="npm"></a>
  <a href="https://github.com/AgentAnycast/agentanycast-node/releases"><img src="https://img.shields.io/github/v/release/AgentAnycast/agentanycast-node?label=Daemon" alt="Release"></a>
  <a href="#license"><img src="https://img.shields.io/badge/license-Apache%202.0%20%2F%20FSL-green" alt="License"></a>
</p>

---

AgentAnycast is a decentralized P2P runtime for the [A2A (Agent-to-Agent)](https://github.com/a2aproject/A2A) protocol, powered by [libp2p](https://libp2p.io/). It lets AI agents securely communicate across any network — your laptop, a corporate server, or the other side of the internet — without public IPs, VPNs, or any infrastructure setup.

Same A2A semantics you already know (Agent Card, Task, Message, Artifact), with automatic NAT traversal and end-to-end encryption built in.

```bash
pip install agentanycast    # or: npm install agentanycast
```

## Why

A2A requires every agent to be an HTTP server with a public URL. This excludes most real-world agents:

- **Agents behind NAT** — laptops, dev machines, edge devices can't accept incoming connections
- **Agents behind firewalls** — corporate networks don't expose internal services to the internet
- **Privacy-sensitive agents** — routing prompts through a centralized gateway is a non-starter

No mainstream agent framework solves cross-network communication. They all assume agents share the same process or cloud. AgentAnycast is the transport layer that closes this gap.

## What It Does

**Zero-config connectivity** — One command makes your agent reachable. Like ngrok, but for A2A agents.

```bash
agentanycast demo
# Your agent is now live. Other agents can find and call it.
```

**Capability-based routing** — Send tasks by skill, not by address. The network finds the right agent.

```python
task = await node.send_task(skill="translate", message=msg)
```

**End-to-end encryption** — All traffic is encrypted with [Noise_XX](https://noiseprotocol.org/). Relay servers only see ciphertext. No plaintext path exists in the codebase.

```
Agent A ◄──── Noise_XX (E2E encrypted) ────► Agent B
                       │
                 ┌─────┴─────┐
                 │   Relay    │  ← forwards ciphertext only
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

### Python — build a server agent

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

### Python — send a task to another agent

```python
async with Node(card=card) as node:
    task = await node.send_task(
        peer_id="12D3KooW...",
        message={"role": "user", "parts": [{"text": "Hello!"}]},
    )
    result = await task.wait()
    print(result.artifacts[0].parts[0].text)  # "Echo: Hello!"
```

### TypeScript — works the same way

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

Python and TypeScript agents can talk to each other out of the box — they share the same protocol.

## Three Ways to Send a Task

```python
# 1. Direct — you know the agent's ID
await node.send_task(peer_id="12D3KooW...", message=msg)

# 2. By skill — you know what you need, the network finds the right agent
await node.send_task(skill="translate", message=msg)

# 3. HTTP Bridge — call a traditional HTTP-based A2A agent from the P2P network
await node.send_task(url="https://agent.example.com", message=msg)
```

| Mode | When to use |
|---|---|
| **Direct** | You have the agent's Peer ID. Point-to-point communication. |
| **By skill** | You need a capability (e.g., "translate"). The skill registry finds an agent for you. |
| **HTTP Bridge** | The target agent uses standard HTTP (Google ADK, etc.). The bridge translates between HTTP and P2P. |

## How It Works

Sidecar architecture — a local Go daemon handles P2P networking, and your SDK communicates with it over gRPC.

```
┌──────────────┐
│  Your App    │  Python or TypeScript — your agent logic
└──────┬───────┘
       │ gRPC (local)
┌──────▼───────┐
│  Daemon      │  Go binary, auto-managed by the SDK
│  (libp2p)    │  handles P2P connections, encryption, NAT traversal
└──────┬───────┘
       │ TCP / QUIC
┌──────▼───────┐
│  Network     │  mDNS (LAN) / Relay (WAN) / DHT (decentralized)
└──────────────┘
```

- **On a local network** — agents discover each other automatically via mDNS. Nothing to configure.
- **Across networks** — deploy a lightweight relay server. Agents connect through it, and the relay can't read any traffic.
- **Behind NAT** — the daemon automatically tries hole-punching first, then falls back to relay if needed.
- **Identity** — each agent gets an Ed25519 key pair. No certificates, no DNS setup. The key *is* the identity.

## Framework Adapters

Turn an existing CrewAI crew or LangGraph graph into a P2P agent with one call:

```python
from agentanycast.adapters.crewai import serve_crew
await serve_crew(my_crew, card=card, relay="...")

from agentanycast.adapters.langgraph import serve_graph
await serve_graph(my_graph, card=card, relay="...")
```

## Interoperability

| Ecosystem | Integration |
|---|---|
| [**A2A**](https://github.com/a2aproject/A2A) | Native implementation — Agent Card, Task, Message, Artifact |
| **HTTP A2A agents** | HTTP Bridge translates between P2P and HTTP bidirectionally |
| [**MCP**](https://modelcontextprotocol.io/) | Map MCP tools to A2A skills and back (`mcpToolToSkill` / `skillToMcpTool`) |
| **W3C DID** | Convert between Peer IDs and `did:key` identifiers |
| [**AGNTCY**](https://github.com/agntcy) | Query the AGNTCY agent directory for cross-ecosystem discovery |

## Deploy Your Own Relay

On a local network, no relay is needed — agents find each other automatically.

For agents on different networks, deploy a relay on any machine with a public IP:

```bash
git clone https://github.com/AgentAnycast/agentanycast-relay.git
cd agentanycast-relay
docker-compose up -d
```

Then point your agents to it:

```python
async with Node(card=card, relay="/ip4/<IP>/tcp/4001/p2p/12D3KooW...") as node:
    ...
```

The relay **cannot read your traffic** — it only forwards ciphertext. It also hosts a **skill registry** for capability-based agent discovery.

## What AgentAnycast Is *Not*

- **Not an agent framework** — use CrewAI, LangGraph, or whatever you prefer. AgentAnycast is the networking layer underneath.
- **Not an orchestration engine** — it doesn't decide what agents do. It just lets them connect.
- **Not a centralized platform** — you own your relay, your keys, your data. Nothing is hosted for you unless you choose it.

## Repositories

| Repository | What it is | Language |
|---|---|---|
| **[agentanycast](https://github.com/AgentAnycast/agentanycast)** | This repo — documentation and discussions | — |
| **[agentanycast-python](https://github.com/AgentAnycast/agentanycast-python)** | Python SDK — `pip install agentanycast` | Python |
| **[agentanycast-ts](https://github.com/AgentAnycast/agentanycast-ts)** | TypeScript SDK — `npm install agentanycast` | TypeScript |
| **[agentanycast-node](https://github.com/AgentAnycast/agentanycast-node)** | Go daemon — P2P networking, encryption, A2A engine | Go |
| **[agentanycast-relay](https://github.com/AgentAnycast/agentanycast-relay)** | Relay server + skill registry | Go |
| **[agentanycast-proto](https://github.com/AgentAnycast/agentanycast-proto)** | Protocol Buffer definitions (gRPC + A2A data models) | Protobuf |

## Documentation

| Guide | What you'll learn |
|---|---|
| **[Getting Started](docs/getting-started.md)** | Install, run your first agent, connect two agents |
| **[Architecture](docs/architecture.md)** | How the sidecar model works, security design, NAT traversal |
| **[Python SDK Reference](docs/python-sdk.md)** | Complete API docs for every class and method |
| **[Deployment](docs/deployment.md)** | Production relay setup, HTTP bridge, metrics, security hardening |
| **[Protocol Reference](docs/protocol.md)** | Wire format, task lifecycle, gRPC service definition |
| **[Examples](docs/examples.md)** | Recipes: skill routing, framework adapters, streaming, LLM agents |

## Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

All repositories require a [CLA](CLA.md) signature — a bot will guide you on your first PR.

## License

| Component | License |
|---|---|
| SDKs (Python, TypeScript) + Proto | [Apache-2.0](https://www.apache.org/licenses/LICENSE-2.0) |
| Daemon + Relay | [FSL-1.1-Apache-2.0](https://fsl.software/) (auto-converts to Apache-2.0 after 2 years) |

## Community

- [GitHub Discussions](https://github.com/AgentAnycast/agentanycast/discussions) — questions, ideas, show & tell
- [GitHub Issues](https://github.com/AgentAnycast/agentanycast/issues) — bug reports, feature requests
