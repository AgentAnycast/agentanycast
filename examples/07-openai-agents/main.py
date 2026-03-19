"""Expose an OpenAI Agent as a P2P agent — reachable from any network.

Run:
    pip install agentanycast[openai-agents] openai-agents
    python main.py

Other agents can now send tasks to this agent by PeerID or skill.
"""

import asyncio

from agents import Agent

from agentanycast import AgentCard, Skill
from agentanycast.adapters.openai_agents import serve_openai_agent


def build_agent() -> Agent:
    return Agent(
        name="helper",
        instructions="You are a helpful assistant. Answer questions concisely.",
        model="gpt-4o",
    )


async def main() -> None:
    agent = build_agent()
    card = AgentCard(
        name="OpenAI Helper Agent",
        description="An OpenAI agent accessible over P2P",
        skills=[Skill(id="help", description="Answer general questions")],
    )

    print("OpenAI Helper Agent is now a P2P agent!")
    await serve_openai_agent(agent, card=card)


if __name__ == "__main__":
    asyncio.run(main())
