# Python SDK Reference

Complete API reference for the `agentanycast` Python SDK.

```bash
pip install agentanycast
```

Requires Python 3.10+.

## Node

The main entry point. Manages the daemon lifecycle, sends and receives tasks.

### Constructor

```python
Node(
    card: AgentCard,
    relay: str | None = None,
    key_path: str | Path | None = None,
    daemon_addr: str | None = None,
    daemon_bin: str | Path | None = None,
    daemon_path: str | Path | None = None,
    home: str | Path | None = None,
)
```

| Parameter | Description | Default |
|---|---|---|
| `card` | Agent's capability descriptor | Required |
| `relay` | Relay server multiaddr for cross-network communication | `None` (LAN only) |
| `key_path` | Path to Ed25519 identity key file | `<home>/key` |
| `daemon_addr` | Address of an externally managed daemon | Auto-managed |
| `daemon_bin` | Name of daemon binary to find on PATH | `agentanycastd` |
| `daemon_path` | Absolute path to daemon binary | Auto-download |
| `home` | Data directory for daemon state | `~/.agentanycast` |

### Usage as Async Context Manager

The recommended way to use `Node`:

```python
async with Node(card=card) as node:
    # node.start() is called automatically
    ...
# node.stop() is called automatically
```

### Properties

| Property | Type | Description |
|---|---|---|
| `peer_id` | `str` | This node's Peer ID (available after `start()`) |
| `is_running` | `bool` | Whether the node is currently running |

### Methods

#### `start()`

```python
await node.start()
```

Starts the daemon process and connects the gRPC channel. Called automatically when using `async with`.

#### `stop()`

```python
await node.stop()
```

Stops the daemon process and closes the gRPC channel. Called automatically when using `async with`.

#### `send_task()`

```python
handle = await node.send_task(
    peer_id: str | None = None,
    skill: str | None = None,
    url: str | None = None,
    message: dict | Message,
    target_skill_id: str | None = None,
    context_id: str | None = None,
    metadata: dict[str, str] | None = None,
) -> TaskHandle
```

Sends a task to a remote agent. Exactly one of `peer_id`, `skill`, or `url` must be provided.

| Parameter | Description |
|---|---|
| `peer_id` | **Direct mode** — target agent's Peer ID |
| `skill` | **Anycast mode** — skill ID to route by (relay resolves the target) |
| `url` | **HTTP Bridge mode** — URL of an HTTP A2A agent |
| `message` | The message to send (dict or `Message` object) |
| `target_skill_id` | Optional skill to target on the remote agent (for direct mode) |
| `context_id` | Optional context ID for multi-turn conversations |
| `metadata` | Optional key-value metadata for the task |

**Returns:** A `TaskHandle` for tracking the task's progress.

**Examples:**

```python
# Direct — by Peer ID
handle = await node.send_task(
    peer_id="12D3KooW...",
    message={"role": "user", "parts": [{"text": "Hello!"}]},
)

# Anycast — by skill
handle = await node.send_task(
    skill="translate",
    message={"role": "user", "parts": [{"text": "Hello!"}]},
)

# HTTP Bridge — by URL
handle = await node.send_task(
    url="https://agent.example.com",
    message={"role": "user", "parts": [{"text": "Hello!"}]},
)
```

#### `discover()`

```python
agents = await node.discover(
    skill: str,
    tags: dict[str, str] | None = None,
    limit: int | None = None,
) -> list[DiscoveredAgent]
```

Finds agents offering a specific skill via the relay's skill registry or DHT.

| Parameter | Description |
|---|---|
| `skill` | Skill ID to search for |
| `tags` | Optional tag filters for fine-grained matching |
| `limit` | Max number of results to return |

**Returns:** A list of `DiscoveredAgent` objects with `peer_id`, `name`, `description`, and `skills`.

```python
agents = await node.discover("translate", tags={"lang": "fr"})
for agent in agents:
    print(f"{agent.name} ({agent.peer_id})")
```

#### `get_card()`

```python
card = await node.get_card(peer_id: str) -> AgentCard
```

Fetches a remote agent's Agent Card, describing its capabilities and skills.

#### `connect_peer()`

```python
await node.connect_peer(
    peer_id: str,
    addresses: list[str] | None = None,
)
```

Explicitly connects to a peer. Usually not needed — peers connect automatically via mDNS or relay.

#### `list_peers()`

```python
peers = await node.list_peers() -> list[dict]
```

Returns a list of currently connected peers with connection metadata.

#### `on_task`

```python
@node.on_task
async def handle(task: IncomingTask):
    ...
```

Decorator that registers a handler for incoming tasks. Only one handler can be registered per node.

#### `serve_forever()`

```python
await node.serve_forever()
```

Blocks until the node is stopped (e.g., via Ctrl+C or `node.stop()`). Use this for server-mode agents that wait for incoming tasks.

---

## AgentCard

Describes an agent's identity, capabilities, and metadata. Compatible with the [A2A Agent Card](https://github.com/a2aproject/A2A) specification.

```python
@dataclass
class AgentCard:
    name: str
    description: str = ""
    version: str = "1.0.0"
    protocol_version: str = "a2a/0.3"
    skills: list[Skill] = field(default_factory=list)
    # Read-only (populated by the daemon after start):
    peer_id: str | None = None
    supported_transports: list[str] = field(default_factory=list)
    relay_addresses: list[str] = field(default_factory=list)
    did_key: str | None = None
```

| Field | Description |
|---|---|
| `name` | Human-readable agent name |
| `description` | What this agent does |
| `version` | Agent version string |
| `protocol_version` | A2A protocol version |
| `skills` | List of skills this agent can perform |
| `peer_id` | This agent's Peer ID (set by daemon, read-only) |
| `supported_transports` | Active transport protocols (read-only) |
| `relay_addresses` | Connected relay addresses (read-only) |
| `did_key` | W3C DID representation of the Peer ID (read-only) |

### Methods

```python
card.to_dict() -> dict        # Serialize to dictionary
AgentCard.from_dict(d) -> AgentCard  # Deserialize from dictionary
```

---

## Skill

Defines a single capability an agent can perform.

```python
@dataclass
class Skill:
    id: str
    description: str = ""
    input_schema: str | None = None   # JSON Schema string
    output_schema: str | None = None  # JSON Schema string
```

| Field | Description |
|---|---|
| `id` | Unique skill identifier (e.g., `"echo"`, `"translate"`) |
| `description` | Human-readable description of what the skill does |
| `input_schema` | Optional JSON Schema describing expected input |
| `output_schema` | Optional JSON Schema describing output format |

**Example with schemas:**

```python
Skill(
    id="translate",
    description="Translate text between languages",
    input_schema='{"type": "object", "properties": {"text": {"type": "string"}, "target_lang": {"type": "string"}}}',
    output_schema='{"type": "object", "properties": {"translated": {"type": "string"}}}',
)
```

---

## TaskHandle

Returned by `send_task()`. Tracks a remote task's progress.

### Properties

| Property | Type | Description |
|---|---|---|
| `task_id` | `str` | Unique task identifier |
| `status` | `TaskStatus` | Current task status |
| `artifacts` | `list[Artifact]` | Result artifacts (available after completion) |

### Methods

#### `wait()`

```python
result = await handle.wait(timeout: float | None = None) -> Task
```

Blocks until the task reaches a terminal state (completed, failed, or canceled).

| Parameter | Description |
|---|---|
| `timeout` | Max seconds to wait. `None` for no timeout. |

**Returns:** The completed `Task` object with all artifacts.

**Raises:** `TaskTimeoutError`, `TaskFailedError`, `TaskCanceledError`

#### `cancel()`

```python
await handle.cancel()
```

Requests cancellation of the task.

---

## IncomingTask

Passed to `@on_task` handlers. Represents a task received from a remote agent.

### Properties

| Property | Type | Description |
|---|---|---|
| `task_id` | `str` | Unique task identifier |
| `peer_id` | `str` | Sender's Peer ID |
| `messages` | `list[Message]` | Messages from the sender |
| `target_skill_id` | `str` | Which skill the sender is targeting |
| `sender_card` | `AgentCard \| None` | Sender's Agent Card (if available) |

### Methods

#### `update_status()`

```python
await task.update_status(status: str)
```

Updates the task's status. Use `"working"` to indicate processing has started.

#### `complete()`

```python
await task.complete(artifacts: list[dict | Artifact] | None = None)
```

Marks the task as completed with optional result artifacts.

**Example:**

```python
await task.complete(artifacts=[
    {"name": "result", "parts": [{"text": "The answer is 42"}]},
])
```

#### `fail()`

```python
await task.fail(error: str)
```

Marks the task as failed with an error message.

#### `request_input()`

```python
await task.request_input(message: dict | Message | None = None)
```

Requests additional input from the sender. Sets the task status to `INPUT_REQUIRED`.

---

## Task

Complete task state, returned by `TaskHandle.wait()`.

```python
@dataclass
class Task:
    task_id: str
    context_id: str = ""
    status: TaskStatus = TaskStatus.SUBMITTED
    messages: list[Message] = field(default_factory=list)
    artifacts: list[Artifact] = field(default_factory=list)
    target_skill_id: str = ""
    originator_peer_id: str = ""
    created_at: datetime | None = None
    updated_at: datetime | None = None
```

---

## Message

A single communication turn in a task conversation.

```python
@dataclass
class Message:
    role: str           # "user" or "agent"
    parts: list[Part] = field(default_factory=list)
    message_id: str = ""
    created_at: datetime | None = None
```

Messages can be created from dicts for convenience:

```python
# These are equivalent:
Message(role="user", parts=[Part(text="Hello")])
Message.from_dict({"role": "user", "parts": [{"text": "Hello"}]})
```

---

## Part

A content unit within a Message or Artifact.

```python
@dataclass
class Part:
    text: str | None = None
    data: dict[str, Any] | None = None
    url: str | None = None
    raw: bytes | None = None
    media_type: str | None = None
    metadata: dict[str, str] | None = None
```

Parts support multiple content types:

```python
# Text content
Part(text="Hello, world!")

# Structured data
Part(data={"temperature": 72, "unit": "F"}, media_type="application/json")

# URL reference
Part(url="https://example.com/image.png", media_type="image/png")

# Binary data
Part(raw=b"\x89PNG...", media_type="image/png")
```

---

## Artifact

An output produced by an agent when completing a task.

```python
@dataclass
class Artifact:
    artifact_id: str = ""
    name: str = ""
    parts: list[Part] = field(default_factory=list)
```

---

## TaskStatus

Enum representing the lifecycle state of a task.

```python
class TaskStatus(Enum):
    SUBMITTED = "submitted"
    WORKING = "working"
    INPUT_REQUIRED = "input_required"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELED = "canceled"
    REJECTED = "rejected"
```

| Property | Type | Description |
|---|---|---|
| `is_terminal` | `bool` | Whether this status represents a final state |

Terminal states: `COMPLETED`, `FAILED`, `CANCELED`, `REJECTED`.

---

## Exceptions

All exceptions inherit from `AgentAnycastError`.

```
AgentAnycastError
├── DaemonError
│   ├── DaemonNotFoundError     — daemon binary not found
│   ├── DaemonStartError        — daemon failed to start
│   └── DaemonConnectionError   — gRPC connection to daemon lost
├── PeerError
│   ├── PeerNotFoundError       — peer ID not found in the network
│   ├── PeerDisconnectedError   — peer disconnected during operation
│   ├── PeerAuthenticationError — Noise handshake failed
│   └── CardNotAvailableError   — peer's Agent Card not available
├── TaskError
│   ├── TaskNotFoundError       — task ID does not exist
│   ├── TaskTimeoutError        — wait() timed out
│   ├── TaskCanceledError       — task was canceled
│   ├── TaskFailedError         — remote agent failed the task
│   └── TaskRejectedError       — remote agent rejected the task
├── RoutingError
│   └── SkillNotFoundError      — no agents found for the requested skill
└── BridgeError
    ├── BridgeConnectionError   — HTTP bridge connection failed
    └── BridgeTranslationError  — failed to translate HTTP ↔ P2P
```

**Example error handling:**

```python
from agentanycast import Node, AgentCard
from agentanycast.exceptions import (
    TaskTimeoutError,
    PeerNotFoundError,
    SkillNotFoundError,
)

async with Node(card=card) as node:
    try:
        handle = await node.send_task(skill="translate", message=msg)
        result = await handle.wait(timeout=30)
    except SkillNotFoundError:
        print("No agents found for 'translate'")
    except PeerNotFoundError:
        print("Could not find the target agent")
    except TaskTimeoutError:
        print("Agent didn't respond within 30 seconds")
```

---

## DID Module

Convert between libp2p Peer IDs and W3C Decentralized Identifiers.

```python
from agentanycast.did import peer_id_to_did_key, did_key_to_peer_id

# PeerID → DID
did = peer_id_to_did_key("12D3KooW...")    # "did:key:z6Mk..."

# DID → PeerID
pid = did_key_to_peer_id("did:key:z6Mk...")  # "12D3KooW..."
```

---

## MCP Module

Map between MCP (Model Context Protocol) tools and A2A skills.

```python
from agentanycast.mcp import (
    MCPTool,
    mcp_tool_to_skill,
    skill_to_mcp_tool,
    mcp_tools_to_agent_card,
)

# Convert MCP tools to an AgentCard
card = mcp_tools_to_agent_card(mcp_tools, name="MCPBridge")

# Individual conversions
skill = mcp_tool_to_skill(mcp_tool)
tool = skill_to_mcp_tool(skill)
```

---

## Framework Adapters

### CrewAI Adapter

```python
from agentanycast.adapters.crewai import CrewAIAdapter, serve_crew

# Quick start
await serve_crew(crew, card=card, relay="...")

# Or use the adapter directly
adapter = CrewAIAdapter(crew)
async with Node(card=card) as node:
    @node.on_task
    async def handle(task):
        await adapter.handle(task)
    await node.serve_forever()
```

Install: `pip install agentanycast[crewai]`

### LangGraph Adapter

```python
from agentanycast.adapters.langgraph import LangGraphAdapter, serve_graph

# Quick start
await serve_graph(compiled_graph, card=card, relay="...")

# Or use the adapter directly
adapter = LangGraphAdapter(compiled_graph)
```

Install: `pip install agentanycast[langgraph]`

---

## AGNTCY Directory

Query the AGNTCY agent directory for cross-ecosystem discovery.

```python
from agentanycast.compat.agntcy import AGNTCYDirectory

directory = AGNTCYDirectory(base_url="https://directory.agntcy.org")
agents = await directory.search("translation")
```

---

## CLI

The SDK includes a command-line interface:

```bash
agentanycast demo [--relay ADDR] [--home DIR]  # Start an echo agent
agentanycast discover SKILL [-t key=value]     # Find agents by skill
agentanycast send PEER_ID MESSAGE              # Send a task
agentanycast status                            # Show node status
agentanycast info                              # Version & config info
```
