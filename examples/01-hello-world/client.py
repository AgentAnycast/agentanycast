"""Send a task to an echo agent.

Run:
    python client.py <PEER_ID> "Hello, world!"
"""

import asyncio
import sys
from agentanycast import Node, AgentCard, Message, Part


async def main():
    if len(sys.argv) < 3:
        print("Usage: python client.py <PEER_ID> <MESSAGE>")
        sys.exit(1)

    peer_id, text = sys.argv[1], sys.argv[2]

    card = AgentCard(name="Client")
    async with Node(card=card) as node:
        print(f"Sending to {peer_id}: {text!r}")

        msg = Message(role="user", parts=[Part(text=text)])
        handle = await node.send_task(msg, peer_id=peer_id)
        result = await handle.wait(timeout=30)

        reply = result.artifacts[0].parts[0].text
        print(f"Response: {reply}")


if __name__ == "__main__":
    asyncio.run(main())
