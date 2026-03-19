"""Discover agents on the network by skill and send tasks via anycast.

Run:
    pip install agentanycast
    python main.py
"""

import asyncio
from agentanycast import Node, AgentCard, Message, Part


async def main():
    card = AgentCard(name="Discovery Client")

    async with Node(card=card) as node:
        # Discover all agents offering the "echo" skill
        print("Searching for agents with skill 'echo'...")
        agents = await node.discover("echo")

        if not agents:
            print("   No agents found. Start an echo agent first:")
            print("   agentanycast demo")
            return

        print(f"   Found {len(agents)} agent(s):\n")
        for agent in agents:
            print(f"   - {agent['agent_name']} ({agent['peer_id'][:16]}...)")

        # Send a task via anycast — the network routes to the best agent
        print("\nSending task via anycast (skill='echo')...")
        msg = Message(role="user", parts=[Part(text="Hello via anycast!")])
        handle = await node.send_task(msg, skill="echo")
        result = await handle.wait(timeout=30)

        reply = result.artifacts[0].parts[0].text
        print(f"Response: {reply}")


if __name__ == "__main__":
    asyncio.run(main())
