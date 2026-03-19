# n8n Integration

[n8n](https://n8n.io) is an open-source workflow automation platform with a
built-in MCP Client node. This guide shows how to connect AgentAnycast's MCP
Server to n8n for automated agent discovery and task routing.

## Prerequisites

- n8n instance (cloud or self-hosted, v1.76+)
- AgentAnycast installed (see [MCP Server Setup](mcp-setup.md))

## Option A: Stdio Mode

Stdio mode works when n8n and the daemon run on the same machine.

1. In your n8n workflow, add an **MCP Client** node.
2. Create a new MCP credential with transport type **Stdio**.
3. Configure the command:
   - **Command:** `agentanycastd`
   - **Arguments:** `--mcp-listen stdio`
4. Save the credential. n8n launches the daemon as a child process.

<!-- screenshot: n8n MCP Client credential form with stdio configuration -->

## Option B: Streamable HTTP Mode

HTTP mode works for remote or containerized deployments.

Start the MCP Server:

```bash
agentanycastd --mcp-listen :8080
```

1. In your n8n workflow, add an **MCP Client** node.
2. Create a new MCP credential with transport type **Streamable HTTP**.
3. Set the **URL** to `http://localhost:8080` (or the daemon's address).
4. Save the credential.

## Using AgentAnycast Tools in a Workflow

Once the MCP Client node is configured, you can call any of the seven
AgentAnycast tools. Set the **Tool Name** and **Tool Parameters** fields on
the MCP Client node.

### Example Workflow: Webhook to Agent

Build a workflow that receives HTTP requests, routes them to a remote agent,
and returns the result:

1. **Webhook** node -- listens for incoming POST requests
2. **MCP Client** node (discover) -- calls `discover_agents` with the skill
   from the webhook body
3. **MCP Client** node (send) -- calls `send_task` with the discovered
   agent's PeerID and the user's message
4. **MCP Client** node (poll) -- calls `get_task_status` to wait for completion
5. **Respond to Webhook** node -- returns the agent's response

<!-- screenshot: n8n workflow canvas with webhook-discover-send-respond chain -->

### Node Configuration Example

For the discover step, configure the MCP Client node:

- **Tool Name:** `discover_agents`
- **Tool Parameters:**
  ```json
  {
    "skill": "{{ $json.body.skill }}"
  }
  ```

For the send step:

- **Tool Name:** `send_task`
- **Tool Parameters:**
  ```json
  {
    "peer_id": "{{ $json.agents[0].peer_id }}",
    "message": "{{ $node.Webhook.json.body.message }}"
  }
  ```

## Tips

- For n8n running in Docker, use HTTP mode and ensure the daemon port is
  accessible from the n8n container.
- Use n8n's **Wait** node between send and poll steps if you expect the remote
  agent to take more than a few seconds.
- The MCP Client node caches the tool list. Restart the workflow if you change
  the daemon configuration.
