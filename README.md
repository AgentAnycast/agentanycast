<p align="center">
  <img src="docs/assets/logo.png" alt="AgentAnycast" width="50%">
</p>

<h1 align="center">AgentAnycast</h1>

<p align="center">
  <strong>A2A Protocol over P2P — Agents talk without public IPs.</strong>
</p>

<p align="center">
  <a href="https://github.com/AgentAnycast/agentanycast-python"><img src="https://img.shields.io/pypi/v/agentanycast?label=SDK&color=blue" alt="PyPI"></a>
  <a href="https://github.com/AgentAnycast/agentanycast-node/releases"><img src="https://img.shields.io/github/v/release/AgentAnycast/agentanycast-node?label=Daemon" alt="Release"></a>
  <a href="#license"><img src="https://img.shields.io/badge/license-Apache%202.0%20%2F%20FSL-green" alt="License"></a>
</p>

---

> **Fully decentralized.** On a local network, agents discover each other automatically via mDNS -- zero configuration. For cross-network communication, deploy your own relay with a single command.

AgentAnycast is a **decentralized P2P runtime for the [A2A (Agent-to-Agent) protocol](https://github.com/a2aproject/A2A)**. It lets AI agents securely collaborate across any network -- no public IP, no centralized gateway, no VPN.

Same A2A semantics (Agent Card, Task, Message, Artifact). Powered by [libp2p](https://libp2p.io/) underneath -- automatic NAT traversal and end-to-end encryption.

## The Problem

A2A requires every agent to expose an HTTP endpoint. This excludes:

- Agents on a developer's laptop (behind NAT)
- Agents inside corporate firewalls
- Edge / IoT agents
- Any privacy-sensitive scenario where routing prompts through a centralized gateway is unacceptable

## The Solution

```
Developer Laptop (behind NAT)           Company Server (behind firewall)
┌─────────────────────────┐             ┌─────────────────────────┐
│  Coding Agent           │  P2P direct │  CI/CD Agent            │
│  (AgentAnycast Node)    │◄───────────►│  (AgentAnycast Node)    │
│                         │  E2E encrypted                        │
│  Skills:                │             │  Skills:                │
│  - write_code           │             │  - run_tests            │
│  - review_pr            │             │  - deploy               │
└─────────────────────────┘             └─────────────────────────┘
```

AgentAnycast automatically handles:

- **NAT Traversal** — AutoNAT detection → DCUtR hole-punching → Relay fallback
- **E2E Encryption** — Noise_XX handshake, relay servers only see ciphertext
- **Cryptographic Identity** — Ed25519 key-derived PeerID, no CA required

## Quick Start

### Local network -- zero configuration

```bash
pip install agentanycast
```

```python
from agentanycast import Node, AgentCard, Skill

# Define your agent
card = AgentCard(
    name="MyAgent",
    description="A helpful assistant",
    skills=[Skill(id="hello", description="Say hello")],
)

# On a LAN, agents discover each other via mDNS -- no relay needed
async with Node(card=card) as node:
    print(f"My Peer ID: {node.peer_id}")

    # Send a task to a remote agent
    task = await node.send_task(
        peer_id="12D3KooW...",
        message={"role": "user", "parts": [{"text": "Hello!"}]},
    )
    result = await task.wait()
    print(result.artifacts)
```

```python
# On the other side -- receive and handle tasks
@node.on_task
async def handle(task):
    await task.update_status("working")
    await task.complete(artifacts=[{"parts": [{"text": "Hello back!"}]}])

await node.serve_forever()
```

### Cross-network -- deploy your own relay

```bash
git clone https://github.com/AgentAnycast/agentanycast-relay.git
cd agentanycast-relay
docker-compose up -d
# Note the RELAY_ADDR from the logs
```

Then point your agents to it:

```python
async with Node(card=card, relay="/ip4/<YOUR_IP>/tcp/4001/p2p/12D3KooW...") as node:
    ...
```

## Architecture

AgentAnycast uses a **sidecar architecture** with four components:

```
┌──────────────────────────┐
│   Your Python App        │
│   (AI Agent logic)       │
└────────────┬─────────────┘
             │
┌────────────▼─────────────┐
│  agentanycast-python     │  ← pip install agentanycast
│  (SDK)                   │
└────────────┬─────────────┘
             │ gRPC over UDS
┌────────────▼─────────────┐
│  agentanycast-node       │  ← Go daemon, auto-managed
│  (P2P + Crypto + A2A)    │
└────────────┬─────────────┘
             │ libp2p (TCP/QUIC)
      ┌──────┼──────┐
      │      │      │
   Peer    Relay   Peer
       (self-hosted)
```

## Repositories

| Repository                                                                     | Description                                        | Language | License            |
| ------------------------------------------------------------------------------ | -------------------------------------------------- | -------- | ------------------ |
| **[agentanycast](https://github.com/AgentAnycast/agentanycast)**               | This repo — docs, specs, discussions               | —        | Apache-2.0         |
| **[agentanycast-proto](https://github.com/AgentAnycast/agentanycast-proto)**   | Protocol Buffer definitions (gRPC + A2A models)    | Protobuf | Apache-2.0         |
| **[agentanycast-node](https://github.com/AgentAnycast/agentanycast-node)**     | Go daemon — P2P networking, encryption, A2A engine | Go       | FSL-1.1-Apache-2.0 |
| **[agentanycast-relay](https://github.com/AgentAnycast/agentanycast-relay)**   | Relay server -- Circuit Relay v2, self-hosted      | Go       | FSL-1.1-Apache-2.0 |
| **[agentanycast-python](https://github.com/AgentAnycast/agentanycast-python)** | Python SDK — `pip install agentanycast`            | Python   | Apache-2.0         |

## Key Features

| Feature                                          | Status |
| ------------------------------------------------ | ------ |
| A2A-native (Agent Card, Task, Message, Artifact) | MVP    |
| NAT traversal (AutoNAT + DCUtR + Relay)          | MVP    |
| E2E encryption (Noise_XX)                        | MVP    |
| Cryptographic identity (Ed25519 PeerID)          | MVP    |
| Python SDK (`pip install agentanycast`)          | MVP    |
| mDNS auto-discovery (zero-config on LAN)         | MVP    |
| Docker-deployable self-hosted Relay               | MVP    |
| Offline message queue + auto-retry               | MVP    |
| A2A Streaming                                    | v0.2   |
| CrewAI / AutoGen integration                     | v0.2   |
| TypeScript SDK                                   | v0.3   |
| HTTP Bridge (P2P ↔ HTTP A2A interop)             | v0.3   |
| DHT-based agent discovery                        | v0.3   |

## Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

- **Proto & Python SDK** — Apache 2.0, [DCO sign-off](https://developercertificate.org/) required
- **Node & Relay** — FSL 1.1, [CLA](CLA.md) signature required

## License

| Component | License |
|---|---|
| **agentanycast-node** | [FSL-1.1-Apache-2.0](https://fsl.software/) |
| **agentanycast-relay** | [FSL-1.1-Apache-2.0](https://fsl.software/) |
| **agentanycast-python** | [Apache-2.0](https://www.apache.org/licenses/LICENSE-2.0) |
| **agentanycast-proto** | [Apache-2.0](https://www.apache.org/licenses/LICENSE-2.0) |
| **Documentation** (this repo) | [Apache-2.0](https://www.apache.org/licenses/LICENSE-2.0) |

FSL-licensed components auto-convert to Apache 2.0 two years after each release.

## Community

- [GitHub Discussions](https://github.com/AgentAnycast/agentanycast/discussions) — Questions, ideas, show & tell
- [GitHub Issues](https://github.com/AgentAnycast/agentanycast/issues) — Bug reports, feature requests
