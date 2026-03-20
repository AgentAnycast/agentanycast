# TypeScript SDK Reference

The TypeScript SDK provides a Node.js interface for AgentAnycast. It communicates with the Go daemon over gRPC, giving your TypeScript/JavaScript agents full access to the P2P network.

## Installation

```bash
npm install agentanycast
```

The daemon binary is automatically downloaded on install. Skip with `AGENTANYCAST_SKIP_DOWNLOAD=1` if building from source.

With specific framework integrations:

```bash
npm install agentanycast    # Core SDK
```

## Requirements

- **Node.js 18+** (ES2022 modules)
- The `agentanycastd` daemon (auto-downloaded, or [build from source](https://github.com/AgentAnycast/agentanycast-node))

## Quick Start

### Server Agent

```typescript
import { Node, type AgentCard } from "agentanycast";

const card: AgentCard = {
  name: "EchoAgent",
  description: "Echoes back any message",
  skills: [{ id: "echo", description: "Echo the input" }],
};

const node = new Node({ card });
await node.start();
console.log(`Peer ID: ${node.peerId}`);

node.onTask(async (task) => {
  const text = task.messages.at(-1)?.parts[0]?.text ?? "";
  await task.complete([{ parts: [{ text: `Echo: ${text}` }] }]);
});

await node.serveForever();
```

### Client Agent

```typescript
const node = new Node({
  card: { name: "Client", skills: [] },
  home: "/tmp/agentanycast-client",
});
await node.start();

const handle = await node.sendTask(
  { role: "user", parts: [{ text: "Hello!" }] },
  { peerId: "12D3KooW..." },
);

const result = await handle.wait(30_000);
console.log(result.artifacts[0].parts[0].text); // "Echo: Hello!"

await node.stop();
```

## Node Class

The `Node` class is the main entry point for the SDK.

### Constructor

```typescript
const node = new Node({
  card: AgentCard,          // Required: agent capability descriptor
  home?: string,            // Data directory (default: ~/.agentanycast)
  relay?: string,           // Relay multiaddr for cross-network
  daemonPath?: string,      // Path to agentanycastd binary
  daemonPort?: number,      // gRPC port (default: auto)
});
```

### Methods

| Method | Description |
|---|---|
| `start()` | Launch daemon, connect gRPC, register card |
| `stop()` | Stop daemon and clean up |
| `sendTask(message, target)` | Send a task (by `peerId`, `skill`, or `url`) |
| `getCard(peerId)` | Fetch a remote agent's card |
| `discover(skill, options?)` | Find agents by skill with optional tag filtering |
| `onTask(handler)` | Register handler for incoming tasks |
| `serveForever()` | Block until stopped, processing incoming tasks |

### Properties

| Property | Type | Description |
|---|---|---|
| `peerId` | `string` | This node's libp2p Peer ID |
| `didKey` | `string` | W3C `did:key` derived from the Ed25519 key |

## Three Ways to Send a Task

```typescript
// 1. Direct — by Peer ID
await node.sendTask(message, { peerId: "12D3KooW..." });

// 2. Anycast — by Skill
await node.sendTask(message, { skill: "translate" });

// 3. HTTP Bridge — by URL
await node.sendTask(message, { url: "https://agent.example.com" });
```

## Skill Discovery

```typescript
// Find all agents with a specific skill
const agents = await node.discover("translate");

// Filter by tags
const frenchAgents = await node.discover("translate", {
  tags: { lang: "fr" },
});

// Use the results
for (const agent of agents) {
  console.log(`${agent.name} (${agent.peerId})`);
}
```

## AgentCard Interface

```typescript
interface AgentCard {
  name: string;
  description?: string;
  version?: string;
  protocolVersion?: string;
  skills: Skill[];

  // Read-only (populated by daemon):
  peerId?: string;
  supportedTransports?: string[];
  relayAddresses?: string[];
  didKey?: string;                    // W3C did:key
  didWeb?: string;                    // did:web identifier
  didDns?: string;                    // did:dns identifier
  verifiableCredentials?: string[];   // JSON-encoded VCs
}

interface Skill {
  id: string;
  description?: string;
  tags?: Record<string, string>;
  inputSchema?: string;               // JSON Schema
  outputSchema?: string;              // JSON Schema
}
```

## TaskHandle

Returned by `sendTask()`, allows you to track task progress:

```typescript
const handle = await node.sendTask(message, { peerId: "..." });

// Wait for completion (with timeout)
const result = await handle.wait(30_000);

// Access results
console.log(result.status);           // "completed"
console.log(result.artifacts);        // Artifact[]
console.log(result.messages);         // Message[]
```

## IncomingTask

Received by `onTask()` handler:

```typescript
node.onTask(async (task) => {
  // Read the incoming message
  const lastMessage = task.messages.at(-1);
  const text = lastMessage?.parts[0]?.text ?? "";

  // Update status
  await task.updateStatus("working");

  // Complete with artifacts
  await task.complete([
    {
      name: "result",
      parts: [{ text: `Processed: ${text}` }],
    },
  ]);

  // Or fail
  // await task.fail("Something went wrong");

  // Or request more input
  // await task.requestInput("Please provide more details");
});
```

## DID Interoperability

Convert between Peer IDs and W3C DIDs:

```typescript
import {
  peerIdToDIDKey,
  didKeyToPeerId,
  didWebToUrl,
  urlToDidWeb,
} from "agentanycast";

// Peer ID ↔ did:key
const did = peerIdToDIDKey("12D3KooW...");       // "did:key:z6Mk..."
const peerId = didKeyToPeerId("did:key:z6Mk..."); // "12D3KooW..."

// did:web ↔ URL
const url = didWebToUrl("did:web:example.com:agents:myagent");
const didWeb = urlToDidWeb("https://example.com/agents/myagent");
```

## MCP Tool Mapping

Bidirectional mapping between MCP tools and A2A skills:

```typescript
import {
  mcpToolToSkill,
  skillToMcpTool,
  mcpToolsToAgentCard,
} from "agentanycast";

// MCP Tool → A2A Skill
const skill = mcpToolToSkill(mcpTool);

// A2A Skill → MCP Tool
const tool = skillToMcpTool(skill);

// Convert all tools to an AgentCard
const card = mcpToolsToAgentCard(tools, {
  name: "MyMCPAgent",
  description: "Agent wrapping MCP tools",
});
```

## Error Handling

The SDK provides a hierarchy of error classes:

```typescript
import {
  AgentAnycastError,    // Base error
  ConnectionError,      // Network/connection issues
  DaemonError,          // Daemon management issues
  TaskError,            // Task-related errors
  TimeoutError,         // Operation timeout
  NotFoundError,        // Resource not found
} from "agentanycast";

try {
  const handle = await node.sendTask(message, { peerId: "..." });
  const result = await handle.wait(10_000);
} catch (err) {
  if (err instanceof TimeoutError) {
    console.error("Task timed out");
  } else if (err instanceof ConnectionError) {
    console.error("Could not reach peer");
  }
}
```

## Configuration

### Environment Variables

| Variable | Description |
|---|---|
| `AGENTANYCAST_HOME` | Data directory (default: `~/.agentanycast`) |
| `AGENTANYCAST_BOOTSTRAP_PEERS` | Relay multiaddr(s), comma-separated |
| `AGENTANYCAST_SKIP_DOWNLOAD` | Set to `1` to skip daemon auto-download |
| `AGENTANYCAST_DAEMON_PATH` | Path to `agentanycastd` binary |

### Programmatic Configuration

```typescript
const node = new Node({
  card,
  home: "/custom/data/dir",
  relay: "/ip4/1.2.3.4/tcp/4001/p2p/12D3KooW...",
  daemonPath: "/usr/local/bin/agentanycastd",
});
```

## Development

```bash
npm install                  # Install dependencies
npm run build                # Compile TypeScript → dist/
npm test                     # Run tests (vitest)
npm run lint                 # ESLint
npm run clean                # Remove dist/
```

## Interoperability with Python

TypeScript and Python agents are fully interoperable — they use the same daemon and protocol. A TypeScript server can receive tasks from a Python client and vice versa:

```typescript
// TypeScript server
const node = new Node({ card });
await node.start();

node.onTask(async (task) => {
  // This handler works with both TypeScript and Python clients
  const text = task.messages.at(-1)?.parts[0]?.text ?? "";
  await task.complete([{ parts: [{ text: `Hello from TypeScript: ${text}` }] }]);
});
```

```python
# Python client sending to the TypeScript server
async with Node(card=card) as node:
    handle = await node.send_task(
        peer_id="12D3KooW...",  # TypeScript agent's Peer ID
        message={"role": "user", "parts": [{"text": "Hello!"}]},
    )
    result = await handle.wait()
    print(result.artifacts[0].parts[0].text)  # "Hello from TypeScript: Hello!"
```
