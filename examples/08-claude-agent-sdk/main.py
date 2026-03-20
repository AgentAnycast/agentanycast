"""Expose a Claude Agent as a P2P agent — reachable from any network.

Run:
    pip install agentanycast[claude] claude-agent-sdk
    python main.py

Other agents can now send tasks to this agent by PeerID or skill.
"""

import asyncio

from agentanycast import AgentCard, Skill
from agentanycast.adapters.claude_agent import serve_claude_agent


async def main() -> None:
    card = AgentCard(
        name="Claude Code Assistant",
        description="A Claude-powered assistant accessible over P2P",
        skills=[Skill(id="code_review", description="Review code and suggest improvements")],
    )

    print("Claude Code Assistant is now a P2P agent!")
    await serve_claude_agent(
        prompt_template="You are a code review assistant. Analyze the code and suggest improvements.",
        card=card,
    )


if __name__ == "__main__":
    asyncio.run(main())
