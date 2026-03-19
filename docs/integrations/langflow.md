# Langflow Integration

[Langflow](https://langflow.org) is a visual agent builder by DataStax. This
guide shows how to connect AgentAnycast's MCP Server to Langflow so your
visual agent pipelines can discover and communicate with remote P2P agents.

## Prerequisites

- Langflow instance (v1.1+)
- AgentAnycast installed (see [MCP Server Setup](mcp-setup.md))

## Configure MCP Tools

Langflow supports MCP tool integration through its component system.

### Stdio Mode

1. Open Langflow and create a new flow (or edit an existing one).
2. In the component sidebar, search for **MCP Tools** (under the Tools
   category) and drag it onto the canvas.
3. Configure the component:
   - **Command:** `agentanycastd --mcp-listen stdio`
4. Langflow launches the daemon and imports the available tools.

### HTTP Mode

Start the MCP Server first:

```bash
agentanycastd --mcp-listen :8080
```

1. Drag an **MCP Tools** component onto the canvas.
2. Configure the component:
   - **URL:** `http://localhost:8080`
3. Langflow connects to the running daemon and imports the tools.

<!-- screenshot: Langflow MCP Tools component configuration panel -->

## Example: Chat Agent with P2P Routing

Build a conversational agent that routes questions to specialized remote agents:

1. Add a **Chat Input** component.
2. Add an **Agent** component (connects to your LLM of choice).
3. Add an **MCP Tools** component configured with AgentAnycast (as above).
4. Connect the MCP Tools output to the Agent's tools input.
5. Add a **Chat Output** component.
6. Wire the flow: Chat Input -> Agent -> Chat Output.

<!-- screenshot: Langflow canvas with chat-input, agent, mcp-tools, chat-output -->

With this setup, the agent can call `discover_agents` and `send_task_by_skill`
during its reasoning steps to find and delegate work to remote agents.

## Example: Deterministic Pipeline

For workflows that always follow the same steps, use Langflow's tool-calling
components directly:

1. **Chat Input** -- receives user message
2. **MCP Tools** (discover) -- calls `discover_agents` with a fixed skill
3. **MCP Tools** (send) -- calls `send_task_by_skill` with the user's message
4. **Parse Output** -- extracts the response from the task result
5. **Chat Output** -- displays the result

Connect the components in sequence to create a deterministic routing pipeline
without LLM-driven tool selection.

## Tips

- If the MCP Tools component is not available in your Langflow version,
  check the [Langflow documentation](https://docs.langflow.org) for custom
  component installation.
- For Langflow running in Docker, use HTTP mode and ensure the daemon port
  is accessible from the container network.
- The Agent component works best with models that support tool calling
  (GPT-4, Claude, Gemini).
