# Dify Integration

[Dify](https://dify.ai) is an open-source low-code platform for building AI agents and workflows with visual orchestration. This guide shows how to connect AgentAnycast's MCP Server to Dify so your agents and workflows can discover and communicate with remote P2P agents.

## Prerequisites

- Dify instance (cloud at [cloud.dify.ai](https://cloud.dify.ai) or self-hosted)
- AgentAnycast daemon installed via the Python SDK or standalone binary
- A running relay server if agents are on different networks (see [Deployment Guide](../deployment.md))

## Start the MCP Server

The daemon's built-in MCP server must be running in Streamable HTTP mode for Dify to connect.

```bash
# Option 1: Start the daemon directly
agentanycastd --mcp-listen :8080

# Option 2: Start via environment variable
AGENTANYCAST_MCP_LISTEN=:8080 agentanycastd

# Option 3: Configure in config.toml
# [mcp]
# enabled = true
# listen = ":3000"
```

Verify the server is running:

```bash
curl -s http://localhost:8080/mcp | head -c 100
```

## Install the MCP Plugin

Dify supports MCP tools through its plugin ecosystem.

1. Open your Dify instance and navigate to **Plugins** in the top menu.
2. Search for **MCP Server** in the plugin marketplace.
3. Install the MCP Server plugin (community-maintained).
4. After installation, the plugin appears under your available tool providers.

If the plugin is not available in the marketplace, you can install it manually from the [Dify Plugin Repository](https://github.com/langgenius/dify-plugins).

## Configure the Tool Provider

1. Go to **Tools** in the left sidebar and click **Add Tool Provider**.
2. Select the **MCP Server** plugin.
3. Enter the connection details:
   - **Server URL:** `http://localhost:8080` (or your daemon's address)
   - **Transport:** Streamable HTTP
4. Click **Test Connection** to verify, then **Save**.

Once connected, Dify imports the seven AgentAnycast tools automatically:

| Tool | Description |
|---|---|
| `toolGetNodeInfo` | Get local node identity and connection status |
| `toolListConnectedPeers` | List all currently connected peers |
| `toolGetAgentCard` | Retrieve a peer's Agent Card (capabilities) |
| `toolDiscoverAgents` | Find agents by skill via registry or DHT |
| `toolSendTask` | Send a task to a specific peer by Peer ID |
| `toolSendTaskBySkill` | Send a task via anycast routing by skill |
| `toolGetTaskStatus` | Check the status and result of a sent task |

## Example: Agent Mode

Create a conversational agent that can delegate tasks to remote P2P agents:

1. Go to **Studio** and create a new **Agent** app.
2. Under **Tools**, enable the AgentAnycast tools you need (e.g., `toolDiscoverAgents`, `toolSendTaskBySkill`).
3. In the system prompt, instruct the agent:

   ```
   You are an orchestrator agent. When the user asks for a task that requires
   a specialized skill (e.g., translation, code review, summarization), use
   the discover_agents tool to find a capable agent, then send_task_by_skill
   to delegate the work. Report the result back to the user.
   ```

4. Test by asking the agent to perform a task that matches a skill registered on your P2P network.

The agent can now discover and delegate tasks to remote P2P agents as part of its reasoning loop.

## Example: Workflow Mode

Build a deterministic workflow that routes user requests to specialized remote agents:

1. Create a new **Workflow** app.
2. Add nodes in this order:
   - **Start** -- receives user input with a `skill` variable and a `message` variable
   - **Tool: toolDiscoverAgents** -- finds agents with the specified skill
   - **Tool: toolSendTaskBySkill** -- sends the user's message via anycast
   - **Tool: toolGetTaskStatus** -- polls until the task completes
   - **End** -- returns the remote agent's response

3. Connect the nodes and configure each tool's input parameters:
   - `toolDiscoverAgents`: set `skill` to `{{#start.skill#}}`
   - `toolSendTaskBySkill`: set `skill` to `{{#start.skill#}}`, `message` to `{{#start.message#}}`
   - `toolGetTaskStatus`: set `task_id` to the output of the previous node

4. Publish and test the workflow.

## Troubleshooting

**Connection refused when testing the tool provider:**

- Ensure the daemon is running: `curl http://localhost:8080/mcp`
- For Dify in Docker, the daemon must be reachable from the container. Use `host.docker.internal:8080` (Docker Desktop) or configure host networking.

**Tools not appearing after connection:**

- Click **Refresh** on the tool provider configuration to re-fetch the tool list.
- Check daemon logs for MCP-related errors.

**Tasks timing out:**

- Verify the target agent is online: use `toolListConnectedPeers` to check connectivity.
- Ensure bootstrap peers are configured if agents are on different networks.
- Check relay server availability if using cross-network communication.

**Self-hosted Dify in Docker Compose:**

Add the daemon to the same Docker network, or use host networking:

```yaml
services:
  dify:
    # ... existing Dify configuration
    extra_hosts:
      - "host.docker.internal:host-gateway"
```

Then use `http://host.docker.internal:8080` as the Server URL.
