# Langflow Integration

[Langflow](https://langflow.org) is a visual agent builder by DataStax that lets you compose AI pipelines by connecting components on a canvas. This guide shows how to connect AgentAnycast's MCP Server to Langflow so your visual agent pipelines can discover and communicate with remote P2P agents.

## Prerequisites

- Langflow instance (v1.1+ for MCP Tools component support)
- AgentAnycast daemon installed via the Python SDK or standalone binary
- A running relay server if agents are on different networks (see [Deployment Guide](../deployment.md))

## Configure MCP Tools

Langflow supports MCP tool integration through its component system. You can connect using either stdio or HTTP mode.

### Stdio Mode

Stdio mode launches the daemon as a child process directly from Langflow. Best for local development.

1. Open Langflow and create a new flow (or edit an existing one).
2. In the component sidebar, search for **MCP Tools** (under the Tools category) and drag it onto the canvas.
3. Configure the component:
   - **Command:** `agentanycastd --mcp-listen stdio`
4. Langflow launches the daemon and imports the available tools automatically.

### HTTP Mode

HTTP mode connects to an externally running daemon. Best for Docker deployments or shared daemon instances.

Start the MCP Server first:

```bash
agentanycastd --mcp-listen :8080
```

1. Drag an **MCP Tools** component onto the canvas.
2. Configure the component:
   - **URL:** `http://localhost:8080`
3. Langflow connects to the running daemon and imports the tools.

Once connected, the MCP Tools component exposes all seven AgentAnycast tools:

| Tool | Description |
|---|---|
| `toolGetNodeInfo` | Get local node identity and connection status |
| `toolListConnectedPeers` | List all currently connected peers |
| `toolGetAgentCard` | Retrieve a peer's Agent Card (capabilities) |
| `toolDiscoverAgents` | Find agents by skill via registry or DHT |
| `toolSendTask` | Send a task to a specific peer by Peer ID |
| `toolSendTaskBySkill` | Send a task via anycast routing by skill |
| `toolGetTaskStatus` | Check the status and result of a sent task |

## Example: Chat Agent with P2P Routing

Build a conversational agent that routes questions to specialized remote agents based on LLM-driven tool selection:

1. Add a **Chat Input** component.
2. Add an **Agent** component and connect it to your LLM of choice (e.g., OpenAI, Anthropic).
3. Add an **MCP Tools** component configured with AgentAnycast (as above).
4. Connect the MCP Tools output to the Agent's **tools** input.
5. Add a **Chat Output** component.
6. Wire the flow: Chat Input -> Agent -> Chat Output.

With this setup, the agent can call `toolDiscoverAgents` and `toolSendTaskBySkill` during its reasoning steps to find and delegate work to remote agents. For example:

- User asks: "Translate this paragraph to French"
- Agent calls `toolDiscoverAgents` with skill `translate`
- Agent calls `toolSendTaskBySkill` with skill `translate` and the user's text
- Agent calls `toolGetTaskStatus` to retrieve the translated result
- Agent returns the translation to the user

The Agent component works best with models that support tool calling (GPT-4, Claude, Gemini).

## Example: Deterministic Pipeline

For workflows that always follow the same steps without LLM-driven tool selection, use Langflow's tool-calling components directly:

1. **Chat Input** -- receives user message
2. **MCP Tools** (discover) -- calls `toolDiscoverAgents` with a fixed skill (e.g., `summarize`)
3. **MCP Tools** (send) -- calls `toolSendTaskBySkill` with the user's message and the target skill
4. **Parse Output** -- extracts the response text from the task result JSON
5. **Chat Output** -- displays the result

Connect the components in sequence to create a deterministic routing pipeline without LLM-driven tool selection. This is useful when:

- The target skill is always known in advance
- You want predictable routing without LLM overhead
- The workflow is part of a larger automation pipeline

## Example: Multi-Agent Orchestration

Combine multiple MCP Tools components to orchestrate across several agent skills:

1. **Chat Input** -- receives a complex request
2. **Agent** (orchestrator) -- decides which skills to invoke
3. **MCP Tools** (skill A) -- configured for one skill (e.g., `research`)
4. **MCP Tools** (skill B) -- configured for another skill (e.g., `write`)
5. **Chat Output** -- presents the combined result

The orchestrator agent can invoke different skills in sequence or parallel depending on the task requirements.

## Troubleshooting

**MCP Tools component not found in the sidebar:**

- Ensure you are running Langflow v1.1 or later. The MCP Tools component was added in this version.
- Check the [Langflow documentation](https://docs.langflow.org) for custom component installation if using an older version.

**Connection refused when configuring HTTP mode:**

- Verify the daemon is running: `curl http://localhost:8080/mcp`
- For Langflow in Docker, the daemon must be reachable. Use `host.docker.internal:8080` or place both in the same Docker network.

**Tools imported but calls fail:**

- Check daemon logs for errors: `agentanycastd --log-level debug --mcp-listen :8080`
- Ensure the daemon has connectivity to the P2P network (bootstrap peers configured, relay reachable).
- Verify that target agents are online and have the expected skills registered.

**Stdio mode fails to launch the daemon:**

- Ensure `agentanycastd` is in the PATH accessible to the Langflow process.
- Check Langflow logs for process spawn errors.
- Fall back to HTTP mode for containerized deployments.

**Langflow in Docker Compose:**

```yaml
services:
  langflow:
    image: langflowai/langflow:latest
    extra_hosts:
      - "host.docker.internal:host-gateway"
    ports:
      - "7860:7860"
```

Use `http://host.docker.internal:8080` as the MCP server URL in the MCP Tools component.

**Slow response times:**

- P2P agent communication adds latency compared to local LLM calls. Use the deterministic pipeline approach to minimize round trips.
- Enable relay caching (`cache_ttl` in anycast config) to speed up repeated discovery queries.
- Consider running agents closer to the Langflow instance to reduce network latency.
