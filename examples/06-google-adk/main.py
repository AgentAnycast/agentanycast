"""Expose a Google ADK agent as a P2P agent — reachable from any network.

Run:
    pip install agentanycast[adk] google-adk
    python main.py

Other agents can now send tasks to this agent by PeerID or skill.
"""

import asyncio

from google.adk.agents import Agent

from agentanycast import AgentCard, Skill
from agentanycast.adapters.adk import serve_adk_agent


def build_agent() -> Agent:
    return Agent(
        name="helper",
        model="gemini-2.0-flash",
        instruction="You are a helpful assistant. Answer questions concisely.",
    )


async def main() -> None:
    agent = build_agent()
    card = AgentCard(
        name="ADK Helper Agent",
        description="A Google ADK agent accessible over P2P",
        skills=[Skill(id="help", description="Answer general questions")],
    )

    print("Google ADK Helper Agent is now a P2P agent!")
    await serve_adk_agent(agent, card=card)


if __name__ == "__main__":
    asyncio.run(main())
