# MCP <-> A2A Bridge

Bridge MCP tools as A2A skills on the P2P network.

## Run

```bash
pip install agentanycast
python main.py
```

## How It Works

`mcp_tools_to_agent_card()` converts MCP tool definitions into A2A Skills:
- Tool `name` -> Skill `id`
- Tool `description` -> Skill `description`
- Tool `inputSchema` -> Skill `input_schema` (JSON string)

Any MCP-compatible tool can be exposed as an A2A skill, discoverable by other agents on the network.
