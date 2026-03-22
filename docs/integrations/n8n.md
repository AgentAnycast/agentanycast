# n8n Integration

[n8n](https://n8n.io) is an open-source workflow automation platform with a built-in MCP Client node for connecting to MCP-compatible tool servers. This guide shows how to connect AgentAnycast's MCP Server to n8n for automated agent discovery and task routing.

## Prerequisites

- n8n instance (cloud or self-hosted, v1.76+ for MCP Client support)
- AgentAnycast daemon installed via the Python SDK or standalone binary
- A running relay server if agents are on different networks (see [Deployment Guide](../deployment.md))

## Option A: Stdio Mode

Stdio mode works when n8n and the daemon run on the same machine. The daemon is launched as a child process by n8n.

1. In your n8n workflow, add an **MCP Client** node.
2. Create a new MCP credential with transport type **Stdio**.
3. Configure the command:
   - **Command:** `agentanycastd`
   - **Arguments:** `--mcp-listen stdio`
4. Save the credential. n8n launches the daemon as a child process and communicates via stdin/stdout.

**When to use:** Local development, single-machine deployments where n8n runs directly on the host (not in Docker).

## Option B: Streamable HTTP Mode

HTTP mode works for remote or containerized deployments where the daemon runs as a separate process.

Start the MCP Server:

```bash
agentanycastd --mcp-listen :8080
```

1. In your n8n workflow, add an **MCP Client** node.
2. Create a new MCP credential with transport type **Streamable HTTP**.
3. Set the **URL** to `http://localhost:8080` (or the daemon's address).
4. Save the credential.

**When to use:** Docker deployments, remote daemons, or when multiple n8n workflows share the same daemon.

## Using AgentAnycast Tools in a Workflow

Once the MCP Client node is configured, you can call any of the seven AgentAnycast tools. Set the **Tool Name** and **Tool Parameters** fields on the MCP Client node.

Available tools:

| Tool Name | Parameters | Description |
|---|---|---|
| `toolGetNodeInfo` | (none) | Get local node identity and status |
| `toolListConnectedPeers` | (none) | List connected peers |
| `toolGetAgentCard` | `peer_id` | Get a peer's capabilities |
| `toolDiscoverAgents` | `skill`, `tags` (optional) | Find agents by skill |
| `toolSendTask` | `peer_id`, `message` | Send task to a specific peer |
| `toolSendTaskBySkill` | `skill`, `message` | Send task via anycast |
| `toolGetTaskStatus` | `task_id` | Check task status and result |

## Example Workflow: Webhook to Agent

Build a workflow that receives HTTP requests, routes them to a remote agent, and returns the result:

1. **Webhook** node -- listens for incoming POST requests with `skill` and `message` in the body
2. **MCP Client** node (discover) -- calls `toolDiscoverAgents` with the skill from the webhook body
3. **MCP Client** node (send) -- calls `toolSendTaskBySkill` with the user's message
4. **Wait** node -- pauses for a configurable duration (e.g., 5 seconds) to allow the remote agent to process
5. **MCP Client** node (poll) -- calls `toolGetTaskStatus` to retrieve the result
6. **Respond to Webhook** node -- returns the agent's response

### Node Configuration

**Discover step** (MCP Client node):

- **Tool Name:** `toolDiscoverAgents`
- **Tool Parameters:**
  ```json
  {
    "skill": "{{ $json.body.skill }}"
  }
  ```

**Send step** (MCP Client node):

- **Tool Name:** `toolSendTaskBySkill`
- **Tool Parameters:**
  ```json
  {
    "skill": "{{ $json.body.skill }}",
    "message": "{{ $node.Webhook.json.body.message }}"
  }
  ```

**Poll step** (MCP Client node):

- **Tool Name:** `toolGetTaskStatus`
- **Tool Parameters:**
  ```json
  {
    "task_id": "{{ $node['MCP Client (send)'].json.task_id }}"
  }
  ```

## Example Workflow: Scheduled Agent Check-in

Create a workflow that periodically queries the P2P network:

1. **Schedule Trigger** node -- runs every 5 minutes
2. **MCP Client** node -- calls `toolListConnectedPeers`
3. **IF** node -- checks if peer count dropped below a threshold
4. **Send Email** / **Slack** node -- alerts on connectivity issues

## Troubleshooting

**MCP Client node shows "Connection refused":**

- Verify the daemon is running: `curl http://localhost:8080/mcp`
- For n8n in Docker, use `host.docker.internal:8080` or configure the daemon to listen on `0.0.0.0:8080`.

**Stdio mode fails to start the daemon:**

- Ensure `agentanycastd` is in the system PATH visible to n8n.
- Check n8n logs for process spawn errors.
- Try HTTP mode instead if running in a containerized environment.

**Tasks return empty results:**

- Use the **Wait** node between send and poll steps. Remote agents may need several seconds to process.
- Increase the wait duration for compute-intensive tasks.
- Check that the target agent is online and has the requested skill registered.

**Tool list not updating after daemon config change:**

- The MCP Client node caches the tool list. Delete and re-add the MCP credential, or restart the n8n workflow.

**n8n in Docker Compose:**

Ensure the daemon port is accessible:

```yaml
services:
  n8n:
    image: n8nio/n8n
    extra_hosts:
      - "host.docker.internal:host-gateway"
    environment:
      - N8N_RUNNERS_ENABLED=true
```

Use `http://host.docker.internal:8080` as the MCP server URL.
