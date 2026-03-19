"""Expose a CrewAI crew as a P2P agent — reachable from any network.

Run:
    pip install agentanycast[crewai] crewai
    python main.py

Other agents can now send tasks to this crew by PeerID or skill.
"""

import asyncio
from crewai import Agent, Crew, Task
from agentanycast import AgentCard, Skill
from agentanycast.adapters.crewai import serve_crew


def build_crew():
    researcher = Agent(
        role="Researcher",
        goal="Find concise answers to questions",
        backstory="You are an expert researcher.",
    )
    crew = Crew(
        agents=[researcher],
        tasks=[Task(description="{input}", agent=researcher, expected_output="A concise answer")],
    )
    return crew


async def main():
    crew = build_crew()
    card = AgentCard(
        name="Research Crew",
        description="A CrewAI research team accessible over P2P",
        skills=[Skill(id="research", description="Answer research questions")],
    )

    print("CrewAI Research Crew is now a P2P agent!")
    await serve_crew(crew, card=card)


if __name__ == "__main__":
    asyncio.run(main())
