# Getting Started

This guide walks you through installing AgentAnycast and running your first pair of communicating agents.

## Prerequisites

- **Python 3.10+** — for the SDK
- **Node.js 18+** — for the TypeScript SDK (alternative to Python)
- **Go 1.25+** — only if building the daemon from source (the SDK can auto-download it)

## Installation

### Install the Python SDK

```bash
pip install agentanycast
```

The SDK automatically downloads the correct `agentanycastd` daemon binary for your platform on first run. No manual setup required.

Or use TypeScript:

```bash
npm install agentanycast
```

## Fastest Way to Try It

![AgentAnycast Demo](assets/demo.svg)

Run a demo echo agent with one command:

```bash
pip install agentanycast && agentanycast demo
```

On first run, the daemon binary downloads automatically (you'll see progress). Once ready, you'll see:

```
  Echo Agent is running!

    Peer ID:  12D3KooWAbCdEf...
    Skill:    echo

    Try it -- open another terminal and run:

      agentanycast send 12D3KooWAbCdEf... "Hello, world!"

    Waiting for incoming tasks... (Ctrl+C to stop)
```

Open a second terminal and paste the `agentanycast send` command. You'll see the echo response instantly.

More CLI commands:

```bash
agentanycast status                      # Check node status
agentanycast discover translate          # Find agents by skill (requires relay)
agentanycast info                        # Show version and config
```

## Your First Agent

### Step 1: Create an Echo Agent (server)

Create a file called `echo_server.py`:

```python
import asyncio
from agentanycast import Node, AgentCard, Skill

card = AgentCard(
    name="EchoAgent",
    description="Echoes back any message it receives",
    skills=[Skill(id="echo", description="Echo the input message")],
)

async def main():
    async with Node(card=card) as node:
        print(f"Echo Agent started. Peer ID: {node.peer_id}")

        @node.on_task
        async def handle(task):
            text = task.messages[-1].parts[0].text
            print(f"Received: {text}")
            await task.update_status("working")
            await task.complete(
                artifacts=[{"name": "echo", "parts": [{"text": f"Echo: {text}"}]}]
            )

        await node.serve_forever()

asyncio.run(main())
```

Run it:

```bash
python echo_server.py
# Output: Echo Agent started. Peer ID: 12D3KooWAbCdEf...
```

Copy the Peer ID — you'll need it in the next step.

### Step 2: Create a Client Agent

Create `echo_client.py`:

```python
import asyncio
from agentanycast import Node, AgentCard

card = AgentCard(name="Client", description="Sends tasks", skills=[])

async def main():
    async with Node(card=card, home="/tmp/agentanycast-client") as node:
        # Discover what the remote agent can do
        remote_card = await node.get_card("12D3KooWAbCdEf...")  # paste Peer ID here
        print(f"Remote agent: {remote_card.name}")
        print(f"Skills: {[s.id for s in remote_card.skills]}")

        # Send a task
        task = await node.send_task(
            peer_id="12D3KooWAbCdEf...",
            message={"role": "user", "parts": [{"text": "Hello, world!"}]},
        )

        # Wait for the response
        result = await task.wait(timeout=30)
        print(result.artifacts[0].parts[0].text)  # "Echo: Hello, world!"

asyncio.run(main())
```

> **Note:** We use `home="/tmp/agentanycast-client"` so the client's daemon doesn't collide with the server's daemon on the same machine. In production, each agent runs on its own machine and you can omit this.

Run it in a separate terminal:

```bash
python echo_client.py
# Output: Echo: Hello, world!
```

That's it — two agents communicating peer-to-peer, with automatic encryption and no configuration.

## Three Ways to Send a Task

AgentAnycast supports three addressing modes:

### 1. Direct — by Peer ID

When you know the exact agent:

```python
handle = await node.send_task(
    peer_id="12D3KooW...",
    message={"role": "user", "parts": [{"text": "Hello!"}]},
)
```

### 2. Anycast — by Skill

When you want to reach any agent that can perform a specific skill. The relay's skill registry resolves the target:

```python
# Discover agents offering a skill
agents = await node.discover("translate")

# Or just send — the network finds the right agent
handle = await node.send_task(
    skill="translate",
    message={"role": "user", "parts": [{"text": "Hello!"}]},
)
```

### 3. HTTP Bridge — to standard HTTP A2A agents

Reach agents that expose traditional HTTP A2A endpoints from the P2P network:

```python
handle = await node.send_task(
    url="https://agent.example.com",
    message={"role": "user", "parts": [{"text": "Hello!"}]},
)
```

## How mDNS Discovery Works

On a local network, agents discover each other automatically via [mDNS](https://en.wikipedia.org/wiki/Multicast_DNS). When a `Node` starts, it broadcasts its presence on the LAN. Other nodes pick this up and connect automatically.

This means **zero configuration** on a LAN — no IP addresses, no DNS, no relay servers. Just start two agents and they find each other.

## Going Cross-Network

When agents are on different networks (e.g., across the internet), they need a **relay server** to find each other and establish connections.

### Deploy a relay

```bash
git clone https://github.com/AgentAnycast/agentanycast-relay.git
cd agentanycast-relay
docker-compose up -d
```

Check the logs for the relay address:

```bash
docker-compose logs relay
# RELAY_ADDR=/ip4/<YOUR_IP>/tcp/4001/p2p/12D3KooW...
```

### Point agents to the relay

Pass the relay address when creating a Node:

```python
async with Node(
    card=card,
    relay="/ip4/<YOUR_IP>/tcp/4001/p2p/12D3KooW...",
) as node:
    ...
```

Or set it as an environment variable:

```bash
export AGENTANYCAST_BOOTSTRAP_PEERS="/ip4/<YOUR_IP>/tcp/4001/p2p/12D3KooW..."
```

See the [Deployment Guide](deployment.md) for production relay setup.

## What Happens Under the Hood

When you create a `Node`, the SDK:

1. **Starts the daemon** — launches `agentanycastd` as a background process
2. **Generates a key pair** — Ed25519 key for cryptographic identity (persisted in `~/.agentanycast/key`)
3. **Opens a gRPC channel** — SDK communicates with the daemon over a Unix domain socket
4. **Registers the Agent Card** — tells the daemon about this agent's capabilities
5. **Starts peer discovery** — mDNS on LAN, relay + skill registry if configured
6. **Registers skills** — if a relay with skill registry is configured, skills are auto-registered

When you send a task:

1. SDK serializes the message into an **A2A envelope**
2. Daemon routes the envelope — direct (by Peer ID), via skill registry (anycast), or through HTTP bridge (URL)
3. Traffic is **end-to-end encrypted** with Noise_XX — even relay servers can't read it
4. Remote daemon delivers the envelope to the remote SDK
5. Remote agent's `@on_task` handler processes the task

## Framework Adapters

Turn existing agent frameworks into P2P agents:

```bash
pip install agentanycast[crewai]         # CrewAI
pip install agentanycast[langgraph]      # LangGraph
pip install agentanycast[google-adk]     # Google ADK
pip install agentanycast[openai-agents]  # OpenAI Agents SDK
```

See [Examples](examples.md) for adapter usage.

## Building the Daemon from Source

If you prefer to build the daemon yourself instead of using the auto-downloaded binary:

```bash
git clone https://github.com/AgentAnycast/agentanycast-node.git
cd agentanycast-node
go build -o agentanycastd ./cmd/agentanycastd/
```

Then tell the SDK where to find it:

```python
async with Node(card=card, daemon_path="/path/to/agentanycastd") as node:
    ...
```

## Next Steps

- [Architecture](architecture.md) — understand the sidecar model, security, and NAT traversal
- [Python SDK Reference](python-sdk.md) — complete API documentation
- [Examples](examples.md) — multi-skill agents, streaming, framework adapters, LLM integration
- [Deployment](deployment.md) — production relay setup, security hardening
- [Protocol Reference](protocol.md) — A2A envelope format, task lifecycle
