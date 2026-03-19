"""Expose a LangGraph graph as a P2P agent.

Run:
    pip install agentanycast[langgraph] langgraph
    python main.py
"""

import asyncio
from langgraph.graph import StateGraph, START, END
from typing import TypedDict
from agentanycast import AgentCard, Skill
from agentanycast.adapters.langgraph import serve_graph


class State(TypedDict):
    input: str
    output: str


def build_graph():
    def process(state: State) -> State:
        return {"input": state["input"], "output": f"Processed: {state['input']}"}

    graph = StateGraph(State)
    graph.add_node("process", process)
    graph.add_edge(START, "process")
    graph.add_edge("process", END)
    return graph.compile()


async def main():
    graph = build_graph()
    card = AgentCard(
        name="LangGraph Processor",
        description="A LangGraph agent accessible over P2P",
        skills=[Skill(id="process", description="Process text input")],
    )

    print("LangGraph agent is now a P2P agent!")
    await serve_graph(graph, card=card)


if __name__ == "__main__":
    asyncio.run(main())
