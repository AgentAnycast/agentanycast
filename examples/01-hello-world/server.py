"""Minimal echo agent — the simplest possible AgentAnycast server.

Run:
    pip install agentanycast
    python server.py
"""

import asyncio
from agentanycast import Node, AgentCard, Skill, IncomingTask, Part
from agentanycast.task import Artifact


async def main():
    card = AgentCard(
        name="Echo Agent",
        description="Echoes back any message it receives.",
        skills=[Skill(id="echo", description="Echo the input")],
    )

    async with Node(card=card) as node:
        print(f"Echo Agent started!")
        print(f"   PeerID:  {node.peer_id}")
        print(f"   Skills:  [echo]")
        print(f"\nWaiting for tasks... (Ctrl+C to stop)\n")

        @node.on_task
        async def handle(task: IncomingTask):
            text = task.messages[-1].parts[0].text
            print(f"   Received: {text!r}")
            await task.complete(
                artifacts=[Artifact(name="echo", parts=[Part(text=f"Echo: {text}")])]
            )
            print(f"   Replied:  Echo: {text!r}")

        await node.serve_forever()


if __name__ == "__main__":
    asyncio.run(main())
