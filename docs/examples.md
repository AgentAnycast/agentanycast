# Examples

Practical patterns for building agents with AgentAnycast.

## Basic Echo Agent

The simplest possible agent — receives a message and echoes it back.

**Server:**

```python
import asyncio
from agentanycast import Node, AgentCard, Skill

card = AgentCard(
    name="EchoAgent",
    description="Echoes back any message",
    skills=[Skill(id="echo", description="Echo the input")],
)

async def main():
    async with Node(card=card) as node:
        print(f"Peer ID: {node.peer_id}")

        @node.on_task
        async def handle(task):
            text = task.messages[-1].parts[0].text
            await task.complete(
                artifacts=[{"parts": [{"text": f"Echo: {text}"}]}]
            )

        await node.serve_forever()

asyncio.run(main())
```

**Client:**

```python
import asyncio
from agentanycast import Node, AgentCard

card = AgentCard(name="Client", description="Sends tasks", skills=[])

async def main():
    async with Node(card=card, home="/tmp/client") as node:
        handle = await node.send_task(
            peer_id="12D3KooW...",
            message={"role": "user", "parts": [{"text": "Hello!"}]},
        )
        result = await handle.wait(timeout=30)
        print(result.artifacts[0].parts[0].text)  # "Echo: Hello!"

asyncio.run(main())
```

## Multi-Skill Agent

An agent that exposes multiple skills and routes tasks accordingly.

```python
import asyncio
from agentanycast import Node, AgentCard, Skill

card = AgentCard(
    name="UtilityAgent",
    description="A multi-purpose utility agent",
    skills=[
        Skill(id="upper", description="Convert text to uppercase"),
        Skill(id="lower", description="Convert text to lowercase"),
        Skill(id="reverse", description="Reverse the input text"),
    ],
)

async def main():
    async with Node(card=card) as node:
        print(f"Peer ID: {node.peer_id}")

        @node.on_task
        async def handle(task):
            text = task.messages[-1].parts[0].text
            await task.update_status("working")

            if task.target_skill_id == "upper":
                result = text.upper()
            elif task.target_skill_id == "lower":
                result = text.lower()
            elif task.target_skill_id == "reverse":
                result = text[::-1]
            else:
                await task.fail(f"Unknown skill: {task.target_skill_id}")
                return

            await task.complete(
                artifacts=[{"name": task.target_skill_id, "parts": [{"text": result}]}]
            )

        await node.serve_forever()

asyncio.run(main())
```

Clients target a specific skill:

```python
handle = await node.send_task(
    peer_id="12D3KooW...",
    message={"role": "user", "parts": [{"text": "Hello World"}]},
    target_skill_id="upper",
)
result = await handle.wait()
print(result.artifacts[0].parts[0].text)  # "HELLO WORLD"
```

## Skill-Based Routing (Anycast)

Send tasks by capability instead of address. The relay's skill registry resolves the target automatically.

```python
import asyncio
from agentanycast import Node, AgentCard, Skill

card = AgentCard(name="Client", description="Sends tasks", skills=[])

async def main():
    async with Node(card=card, relay="/ip4/.../tcp/4001/p2p/12D3KooW...") as node:
        # Discover agents offering a skill
        agents = await node.discover("translate")
        for agent in agents:
            print(f"Found: {agent.name} ({agent.peer_id[:16]}...)")

        # Or skip discovery — just send by skill
        handle = await node.send_task(
            skill="translate",
            message={"role": "user", "parts": [{"text": "Hello, world!"}]},
        )
        result = await handle.wait(timeout=30)
        print(result.artifacts[0].parts[0].text)

asyncio.run(main())
```

### With Tag Filtering

```python
# Find French-capable translators
agents = await node.discover("translate", tags={"lang": "fr"})

# Find agents in a specific region
agents = await node.discover("summarize", tags={"region": "eu"})
```

## HTTP Bridge

Reach standard HTTP A2A agents from the P2P network.

```python
# Send a task to an HTTP A2A agent
handle = await node.send_task(
    url="https://agent.example.com",
    message={"role": "user", "parts": [{"text": "Summarize this document"}]},
)
result = await handle.wait(timeout=60)
```

No special configuration needed on the sending side — the daemon's HTTP bridge handles the translation between P2P and HTTP protocols automatically.

## Error Handling

Robust error handling for production agents.

```python
import asyncio
from agentanycast import Node, AgentCard
from agentanycast.exceptions import (
    PeerNotFoundError,
    SkillNotFoundError,
    TaskTimeoutError,
    TaskFailedError,
    TaskCanceledError,
    BridgeConnectionError,
)

card = AgentCard(name="Client", description="Robust client", skills=[])

async def main():
    async with Node(card=card, relay="...") as node:
        try:
            handle = await node.send_task(
                skill="translate",
                message={"role": "user", "parts": [{"text": "Hello"}]},
            )
            result = await handle.wait(timeout=60)
            for artifact in result.artifacts:
                for part in artifact.parts:
                    if part.text:
                        print(f"Result: {part.text}")

        except SkillNotFoundError:
            print("No agents found for 'translate'")
        except PeerNotFoundError:
            print("Resolved agent is unreachable")
        except TaskTimeoutError:
            print("Agent didn't respond in time")
        except TaskFailedError as e:
            print(f"Agent reported an error: {e}")
        except TaskCanceledError:
            print("Task was canceled")
        except BridgeConnectionError:
            print("HTTP bridge connection failed")

asyncio.run(main())
```

## Server-Side Error Handling

Gracefully handle errors in task handlers:

```python
@node.on_task
async def handle(task):
    try:
        await task.update_status("working")
        text = task.messages[-1].parts[0].text
        result = process(text)  # your business logic
        await task.complete(
            artifacts=[{"parts": [{"text": result}]}]
        )
    except ValueError as e:
        await task.fail(f"Invalid input: {e}")
    except Exception as e:
        await task.fail(f"Internal error: {e}")
```

## Structured Data Exchange

Exchange JSON-structured data between agents.

**Server (weather agent):**

```python
import json

card = AgentCard(
    name="WeatherAgent",
    description="Returns weather data",
    skills=[Skill(
        id="weather",
        description="Get weather for a city",
        input_schema='{"type": "object", "properties": {"city": {"type": "string"}}}',
    )],
)

@node.on_task
async def handle(task):
    data = task.messages[-1].parts[0].data
    city = data["city"]

    weather = {"city": city, "temp_f": 72, "condition": "sunny"}
    await task.complete(artifacts=[{
        "name": "weather",
        "parts": [{"data": weather, "media_type": "application/json"}],
    }])
```

**Client:**

```python
handle = await node.send_task(
    peer_id="12D3KooW...",
    message={
        "role": "user",
        "parts": [{"data": {"city": "San Francisco"}, "media_type": "application/json"}],
    },
    target_skill_id="weather",
)
result = await handle.wait()
weather = result.artifacts[0].parts[0].data
print(f"{weather['city']}: {weather['temp_f']}°F, {weather['condition']}")
```

## CrewAI Integration

Expose a CrewAI crew as a P2P agent with one function call.

```python
import asyncio
from crewai import Agent, Task, Crew
from agentanycast import AgentCard, Skill
from agentanycast.adapters.crewai import serve_crew

# Define your CrewAI crew
researcher = Agent(role="Researcher", goal="Find information", ...)
crew = Crew(agents=[researcher], tasks=[...])

# Expose it as a P2P agent
card = AgentCard(
    name="ResearchCrew",
    description="A research team powered by CrewAI",
    skills=[Skill(id="research", description="Research a topic")],
)

async def main():
    await serve_crew(crew, card=card, relay="...")

asyncio.run(main())
```

Install: `pip install agentanycast[crewai]`

## LangGraph Integration

Expose a LangGraph workflow as a P2P agent.

```python
import asyncio
from langgraph.graph import StateGraph
from agentanycast import AgentCard, Skill
from agentanycast.adapters.langgraph import serve_graph

# Define your LangGraph workflow
graph = StateGraph(...)
# ... add nodes and edges ...
compiled = graph.compile()

# Expose it as a P2P agent
card = AgentCard(
    name="WorkflowAgent",
    description="A workflow powered by LangGraph",
    skills=[Skill(id="process", description="Run the workflow")],
)

async def main():
    await serve_graph(compiled, card=card, relay="...")

asyncio.run(main())
```

Install: `pip install agentanycast[langgraph]`

## MCP Tool Mapping

Convert MCP (Model Context Protocol) tools into A2A skills:

```python
from agentanycast.mcp import mcp_tools_to_agent_card, MCPTool

# Define MCP tools
tools = [
    MCPTool(name="search", description="Search the web", input_schema={...}),
    MCPTool(name="calculate", description="Perform calculations", input_schema={...}),
]

# Create an AgentCard from MCP tools
card = mcp_tools_to_agent_card(tools, name="MCPBridge")

# Now serve it as a P2P agent
async with Node(card=card) as node:
    @node.on_task
    async def handle(task):
        # Route to the appropriate MCP tool based on target_skill_id
        ...
    await node.serve_forever()
```

## W3C DID Identity

Work with W3C Decentralized Identifiers alongside Peer IDs:

```python
from agentanycast.did import peer_id_to_did_key, did_key_to_peer_id

# Convert Peer ID to DID
did = peer_id_to_did_key("12D3KooWAbCdEf...")
print(did)  # "did:key:z6MkhaXgBZ..."

# Convert DID back to Peer ID
peer_id = did_key_to_peer_id("did:key:z6MkhaXgBZ...")
print(peer_id)  # "12D3KooWAbCdEf..."

# The AgentCard also includes the DID
async with Node(card=card) as node:
    remote_card = await node.get_card("12D3KooW...")
    print(remote_card.did_key)  # "did:key:z6Mk..."
```

## Cross-Network Communication

Agents on different networks communicating through a relay.

**Agent on Machine A (behind NAT):**

```python
relay = "/ip4/203.0.113.50/tcp/4001/p2p/12D3KooWRelay..."

async with Node(card=server_card, relay=relay) as node:
    print(f"Server Peer ID: {node.peer_id}")

    @node.on_task
    async def handle(task):
        await task.complete(artifacts=[{"parts": [{"text": "Hello from behind NAT!"}]}])

    await node.serve_forever()
```

**Agent on Machine B (behind different NAT):**

```python
relay = "/ip4/203.0.113.50/tcp/4001/p2p/12D3KooWRelay..."

async with Node(card=client_card, relay=relay) as node:
    handle = await node.send_task(
        peer_id="12D3KooWServerPeerId...",
        message={"role": "user", "parts": [{"text": "Hello!"}]},
    )
    result = await handle.wait()
    print(result.artifacts[0].parts[0].text)  # "Hello from behind NAT!"
```

## Running Multiple Agents on One Machine

Use separate `home` directories to avoid daemon conflicts:

```python
import asyncio
from agentanycast import Node, AgentCard, Skill

async def main():
    agent1_card = AgentCard(name="Agent1", description="First agent", skills=[
        Skill(id="greet", description="Greet the user"),
    ])
    agent2_card = AgentCard(name="Agent2", description="Second agent", skills=[])

    async with Node(card=agent1_card, home="/tmp/agent1") as agent1:
        async with Node(card=agent2_card, home="/tmp/agent2") as agent2:
            @agent1.on_task
            async def handle_task(task):
                await task.complete(
                    artifacts=[{"parts": [{"text": "Hello from Agent 1!"}]}]
                )

            handle = await agent2.send_task(
                peer_id=agent1.peer_id,
                message={"role": "user", "parts": [{"text": "Hi!"}]},
            )
            result = await handle.wait(timeout=10)
            print(result.artifacts[0].parts[0].text)

asyncio.run(main())
```

## LLM-Powered Agent

Integrate with an LLM (e.g., via the Anthropic API) to build an intelligent agent.

```python
import asyncio
import anthropic
from agentanycast import Node, AgentCard, Skill

client = anthropic.AsyncAnthropic()

card = AgentCard(
    name="ClaudeAgent",
    description="An AI assistant powered by Claude",
    skills=[Skill(id="chat", description="Chat with Claude")],
)

async def main():
    async with Node(card=card) as node:
        print(f"Claude Agent ready. Peer ID: {node.peer_id}")

        @node.on_task
        async def handle(task):
            await task.update_status("working")

            text = task.messages[-1].parts[0].text

            response = await client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1024,
                messages=[{"role": "user", "content": text}],
            )

            reply = response.content[0].text
            await task.complete(
                artifacts=[{"name": "response", "parts": [{"text": reply}]}]
            )

        await node.serve_forever()

asyncio.run(main())
```

This creates a Claude-powered agent that any other AgentAnycast agent can talk to — no HTTP server, no public IP, fully encrypted.

## AGNTCY Directory Discovery

Discover agents across ecosystems via the AGNTCY directory:

```python
from agentanycast.compat.agntcy import AGNTCYDirectory

directory = AGNTCYDirectory(base_url="https://directory.agntcy.org")
agents = await directory.search("translation")
for agent in agents:
    print(f"{agent['name']}: {agent['description']}")
```
