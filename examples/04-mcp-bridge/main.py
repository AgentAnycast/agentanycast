"""Map MCP tools to A2A skills and expose them over P2P.

This example shows how to take existing MCP tools and make them
discoverable and callable as A2A skills on the P2P network.

Run:
    pip install agentanycast
    python main.py
"""

import asyncio
from agentanycast import Node
from agentanycast.mcp import mcp_tools_to_agent_card, MCPTool


# Example MCP tools (normally these come from an MCP server)
mcp_tools = [
    MCPTool(
        name="translate",
        description="Translate text between languages",
        input_schema={
            "type": "object",
            "properties": {
                "text": {"type": "string"},
                "target_lang": {"type": "string"},
            },
        },
    ),
    MCPTool(
        name="summarize",
        description="Summarize a long document",
        input_schema={
            "type": "object",
            "properties": {
                "text": {"type": "string"},
                "max_length": {"type": "integer"},
            },
        },
    ),
]


async def main():
    # Convert MCP tools to an A2A AgentCard with skills
    card = mcp_tools_to_agent_card("MCP Bridge Agent", mcp_tools)

    async with Node(card=card) as node:
        print(f"MCP Bridge Agent started!")
        print(f"   PeerID: {node.peer_id}")
        print(f"   Skills: {[s.id for s in card.skills]}")
        print(f"\n   MCP tools are now discoverable as A2A skills on the P2P network.\n")

        @node.on_task
        async def handle(task):
            # Route to appropriate MCP tool based on target skill
            skill = task.target_skill_id
            text = task.messages[-1].parts[0].text
            print(f"   Task for skill '{skill}': {text[:50]}...")
            # In production, you'd call the actual MCP tool here
            await task.complete(artifacts=[{"parts": [{"text": f"[{skill}] processed: {text}"}]}])

        await node.serve_forever()


if __name__ == "__main__":
    asyncio.run(main())
