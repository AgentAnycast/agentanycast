# Dify Integration

[Dify](https://dify.ai) is an open-source low-code AI agent platform. This
guide shows how to connect AgentAnycast's MCP Server to Dify so your agents
and workflows can discover and communicate with remote P2P agents.

## Prerequisites

- Dify instance (cloud or self-hosted)
- AgentAnycast MCP Server running in HTTP mode (see [MCP Server Setup](mcp-setup.md))

Start the MCP Server:

```bash
agentanycastd --mcp-listen :8080
```

## Install the MCP Plugin

Dify supports MCP tools through its plugin ecosystem.

1. Open your Dify instance and navigate to **Plugins** in the top menu.
2. Search for **MCP Server** in the plugin marketplace.
3. Install the MCP Server plugin (community-maintained).
4. After installation, the plugin appears under your available tool providers.

<!-- screenshot: Dify plugin marketplace showing MCP Server plugin -->

## Configure the Tool Provider

1. Go to **Tools** in the left sidebar and click **Add Tool Provider**.
2. Select the **MCP Server** plugin.
3. Enter the connection details:
   - **Server URL:** `http://localhost:8080` (or your daemon's address)
   - **Transport:** Streamable HTTP
4. Click **Test Connection** to verify, then **Save**.

<!-- screenshot: Dify tool provider configuration form -->

Once connected, Dify imports the seven AgentAnycast tools automatically. They
appear as usable tools in both Agent and Workflow modes.

## Example: Agent Mode

Create a new Agent app in Dify and enable the AgentAnycast tools:

1. Go to **Studio** and create a new **Agent** app.
2. Under **Tools**, enable the AgentAnycast tools you need (e.g.,
   `discover_agents`, `send_task_by_skill`).
3. In the system prompt, instruct the agent to use these tools for
   cross-agent communication.

The agent can now discover and delegate tasks to remote P2P agents as part of
its reasoning loop.

## Example: Workflow Mode

Build a workflow that routes user requests to specialized remote agents:

1. Create a new **Workflow** app.
2. Add nodes in this order:
   - **Start** -- receives user input
   - **Tool: discover_agents** -- finds agents with a matching skill
   - **Tool: send_task_by_skill** -- sends the user's request via anycast
   - **Tool: get_task_status** -- polls until the task completes
   - **End** -- returns the remote agent's response

<!-- screenshot: Dify workflow canvas with the four-node pipeline -->

3. Connect the nodes and configure each tool's input parameters.
4. Publish and test the workflow.

## Tips

- For self-hosted Dify running in Docker, ensure the AgentAnycast daemon is
  reachable from the Dify container (use host networking or expose the port).
- If the MCP plugin is not available in the marketplace, check the
  [Dify Plugin Repository](https://github.com/langgenius/dify-plugins) for
  manual installation instructions.
