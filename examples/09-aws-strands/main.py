"""Expose an AWS Strands Agent as a P2P agent — reachable from any network.

Run:
    pip install agentanycast[strands] strands-agents
    python main.py

Other agents can now send tasks to this agent by PeerID or skill.
"""

import asyncio

from strands import Agent

from agentanycast import AgentCard, Skill
from agentanycast.adapters.strands import serve_strands_agent


def build_agent() -> Agent:
    return Agent(
        system_prompt="You are a helpful assistant. Answer questions concisely.",
    )


async def main() -> None:
    agent = build_agent()
    card = AgentCard(
        name="Strands Helper Agent",
        description="An AWS Strands agent accessible over P2P",
        skills=[Skill(id="help", description="Answer general questions")],
    )

    print("Strands Helper Agent is now a P2P agent!")
    await serve_strands_agent(agent, card=card)


if __name__ == "__main__":
    asyncio.run(main())
