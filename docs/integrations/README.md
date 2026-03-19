# Platform Integrations

AgentAnycast provides a built-in [MCP Server](mcp-setup.md) that exposes P2P
agent networking as tools. Any platform supporting the Model Context Protocol
can use AgentAnycast to discover, communicate with, and orchestrate remote
agents over an encrypted P2P network.

## Common Setup

Before integrating with any platform, see the [MCP Server Setup](mcp-setup.md)
guide for installation, startup modes, and available tools.

## Supported Platforms

| Platform | Type | Integration Method |
|----------|------|-------------------|
| [Dify](dify.md) | Low-code AI agent platform | MCP plugin (Streamable HTTP) |
| [n8n](n8n.md) | Workflow automation | MCP Client node (stdio or HTTP) |
| [Langflow](langflow.md) | Visual agent builder | MCP tools component (stdio or HTTP) |

## AI IDE Support

The MCP Server also works with AI-powered IDEs and CLI tools. See the
[MCP Server Setup](mcp-setup.md#ide-configuration) guide for copy-paste
configurations for Claude Desktop, Cursor, VS Code, and Gemini CLI.
