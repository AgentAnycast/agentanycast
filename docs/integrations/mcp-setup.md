# MCP Server Setup

AgentAnycast includes a built-in MCP Server in the Go daemon (`agentanycastd`).
This guide covers setup and configuration common to all platform integrations.

## Prerequisites

Install the Python SDK, which auto-downloads the daemon binary:

```bash
pip install agentanycast
```

Verify the daemon is available:

```bash
agentanycastd --version
```

## Starting the MCP Server

### Stdio Mode

Stdio mode is used by AI IDEs and tools that launch the MCP server as a child process:

```bash
agentanycastd --mcp-listen stdio
```

The daemon reads JSON-RPC from stdin and writes responses to stdout.

### Streamable HTTP Mode

HTTP mode is used by platforms that connect to a remote MCP endpoint:

```bash
agentanycastd --mcp-listen :8080
```

The server listens on `http://localhost:8080` and accepts Streamable HTTP
connections. You can bind to a specific interface:

```bash
agentanycastd --mcp-listen 0.0.0.0:8080
```

## Available Tools

The MCP Server exposes seven tools:

| Tool | Description |
|------|-------------|
| `discover_agents` | Find agents by skill name via DHT and relay registry |
| `send_task` | Send an encrypted task to a remote agent by PeerID |
| `send_task_by_skill` | Anycast routing -- discover and send in one step |
| `get_task_status` | Check the status of a previously sent task |
| `get_agent_card` | Retrieve an agent's capability card (skills, DID, endpoints) |
| `list_connected_peers` | List all currently connected P2P peers |
| `get_node_info` | Get local node info: PeerID, DID (`did:key`), listen addresses |

## IDE Configuration

### Claude Desktop

Add to `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS)
or `%APPDATA%\Claude\claude_desktop_config.json` (Windows):

```json
{
  "mcpServers": {
    "agentanycast": {
      "command": "agentanycastd",
      "args": ["--mcp-listen", "stdio"]
    }
  }
}
```

### Cursor

Add to `.cursor/mcp.json` in your project root:

```json
{
  "mcpServers": {
    "agentanycast": {
      "command": "agentanycastd",
      "args": ["--mcp-listen", "stdio"]
    }
  }
}
```

### VS Code (Copilot)

Add to `.vscode/mcp.json` in your project root:

```json
{
  "servers": {
    "agentanycast": {
      "type": "stdio",
      "command": "agentanycastd",
      "args": ["--mcp-listen", "stdio"]
    }
  }
}
```

### Gemini CLI

Add to `~/.gemini/settings.json`:

```json
{
  "mcpServers": {
    "agentanycast": {
      "command": "agentanycastd",
      "args": ["--mcp-listen", "stdio"]
    }
  }
}
```

## Troubleshooting

**Daemon binary not found:** Ensure the Python SDK is installed (`pip install agentanycast`) and `agentanycastd` is on your `PATH`. The SDK downloads the binary to `~/.agentanycast/bin/`.

**Port already in use (HTTP mode):** Another process is using the port. Choose a different port with `--mcp-listen :9090`.

**Connection refused:** Confirm the daemon is running and the listen address matches your client configuration. For HTTP mode, verify there is no firewall blocking the port.

**Stdio mode produces no output:** Ensure no other process is reading from the same stdin/stdout. Only one client should connect in stdio mode.
