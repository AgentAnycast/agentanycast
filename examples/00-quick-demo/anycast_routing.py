"""Skill-based anycast routing — discover agents and route by capability.

Run in two terminals:

    # Terminal 1 — start a multi-skill agent
    python anycast_routing.py --serve

    # Terminal 2 — discover and send tasks via anycast
    python anycast_routing.py --discover

In production, agents run as separate processes on separate machines.
The network automatically routes tasks to agents matching the requested skill.
"""

import argparse
import asyncio
import time

from agentanycast import AgentCard, Artifact, IncomingTask, Message, Node, Part, Skill
from agentanycast.did import peer_id_to_did_key

# ---------------------------------------------------------------------------
# ANSI helpers
# ---------------------------------------------------------------------------

BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"
GREEN = "\033[32m"
CYAN = "\033[36m"
YELLOW = "\033[33m"
RED = "\033[31m"
WHITE = "\033[97m"
MAGENTA = "\033[35m"

BULLET = f"{DIM}[*]{RESET}"
OK = f"{GREEN}[+]{RESET}"
WARN = f"{YELLOW}[!]{RESET}"
ARROW = f"{CYAN}-->{RESET}"


def header(text: str) -> str:
    width = max(len(text), 48)
    line = "=" * width
    return f"\n{BOLD}{WHITE}{text}{RESET}\n{DIM}{line}{RESET}\n"


def kv(key: str, value: str, color: str = CYAN) -> str:
    return f"    {DIM}{key}:{RESET}  {color}{value}{RESET}"


def skill_badge(skill_id: str) -> str:
    colors = {
        "translate": CYAN,
        "summarize": GREEN,
        "code-review": MAGENTA,
    }
    c = colors.get(skill_id, WHITE)
    return f"{c}[{skill_id}]{RESET}"


# ---------------------------------------------------------------------------
# Skill handlers
# ---------------------------------------------------------------------------

SKILL_RESPONSES = {
    "translate": "Translated: '{text}' -> 'Hola desde el otro lado!'",
    "summarize": "Summary: The message '{text}' conveys a greeting in {n} words.",
    "code-review": "Review: The code looks clean. No issues found in '{text}'.",
}


def make_response(skill_id: str, text: str) -> str:
    template = SKILL_RESPONSES.get(skill_id, "Processed: {text}")
    return template.format(text=text, n=len(text.split()))


# ---------------------------------------------------------------------------
# Server mode — one agent with multiple skills
# ---------------------------------------------------------------------------


async def run_server() -> None:
    print(header("AgentAnycast Multi-Skill Agent"))

    skills = [
        Skill(id="translate", description="Translate text between languages"),
        Skill(id="summarize", description="Summarize text content"),
        Skill(id="code-review", description="Review code for issues"),
    ]

    card = AgentCard(
        name="Swiss-Army Agent",
        description="A multi-skill agent demonstrating anycast routing.",
        skills=skills,
    )

    print(f"{BULLET} Starting multi-skill agent...")
    async with Node(card=card) as node:
        print(f"{OK} Agent started")
        print(kv("PeerID", node.peer_id))
        print(kv("DID", peer_id_to_did_key(node.peer_id)))
        print()
        print(f"    {DIM}Registered skills:{RESET}")
        for s in skills:
            print(f"      {skill_badge(s.id)}  {DIM}{s.description}{RESET}")
        print()
        print(f"{BULLET} Listening for anycast tasks...\n")
        print(f"    {DIM}Tip: run in another terminal:{RESET}")
        print(f"    {CYAN}python anycast_routing.py --discover{RESET}\n")

        @node.on_task
        async def handle(task: IncomingTask) -> None:
            text = task.messages[-1].parts[0].text
            # Determine which skill was targeted (from task metadata or message)
            # For the demo, we parse a simple "skill:message" format
            skill_id = "translate"  # default
            if ":" in text:
                maybe_skill, rest = text.split(":", 1)
                maybe_skill = maybe_skill.strip().lower()
                if maybe_skill in SKILL_RESPONSES:
                    skill_id = maybe_skill
                    text = rest.strip()

            sender = task.peer_id or "unknown"
            sender_short = sender[:16] + "..." if len(sender) > 16 else sender

            print(f"{OK} Task received  {ARROW}  {skill_badge(skill_id)}")
            print(kv("From", sender_short))
            print(kv("Input", repr(text), WHITE))

            reply = make_response(skill_id, text)
            await task.complete(
                artifacts=[Artifact(name=skill_id, parts=[Part(text=reply)])]
            )
            print(kv("Output", repr(reply), GREEN))
            print()

        await node.serve_forever()


# ---------------------------------------------------------------------------
# Client mode — discover agents and send via anycast
# ---------------------------------------------------------------------------


async def run_discover() -> None:
    print(header("AgentAnycast Skill Discovery + Anycast"))

    card = AgentCard(name="Discovery Client")

    print(f"{BULLET} Starting client node...")
    async with Node(card=card) as node:
        print(f"{OK} Client started")
        print(kv("PeerID", node.peer_id))
        print()

        # Discover agents for each skill
        target_skills = ["translate", "summarize", "code-review"]

        print(f"{BOLD}{WHITE}Phase 1: Discovery{RESET}")
        print(f"    {DIM}Searching the P2P network for agents by skill...{RESET}\n")

        for skill_id in target_skills:
            print(f"    {BULLET} Discovering {skill_badge(skill_id)} ...", end=" ")
            t0 = time.monotonic()
            agents = await node.discover(skill_id)
            elapsed = (time.monotonic() - t0) * 1000

            if agents:
                print(f"{GREEN}found {len(agents)} agent(s){RESET} {DIM}({elapsed:.0f}ms){RESET}")
                for agent in agents:
                    name = agent.get("agent_name", "unnamed")
                    pid = agent["peer_id"][:16] + "..."
                    print(f"        {DIM}-{RESET} {name} {DIM}({pid}){RESET}")
            else:
                print(f"{YELLOW}none found{RESET} {DIM}({elapsed:.0f}ms){RESET}")

        # Send tasks via anycast
        print(f"\n{BOLD}{WHITE}Phase 2: Anycast Routing{RESET}")
        print(f"    {DIM}Sending tasks — the network routes to the best agent...{RESET}\n")

        test_messages = [
            ("translate", "Hello from the decentralized world!"),
            ("summarize", "AgentAnycast enables P2P agent communication"),
            ("code-review", "def add(a, b): return a + b"),
        ]

        for skill_id, text in test_messages:
            print(f"    {ARROW} Anycast {skill_badge(skill_id)}: {DIM}{text!r}{RESET}")

            t0 = time.monotonic()
            msg = Message(
                role="user",
                parts=[Part(text=f"{skill_id}: {text}")],
            )
            handle = await node.send_task(msg, skill=skill_id)
            result = await handle.wait(timeout=30)
            elapsed = (time.monotonic() - t0) * 1000

            reply = result.artifacts[0].parts[0].text
            print(f"       {OK} {GREEN}{reply}{RESET}")
            print(f"       {DIM}Routed + processed in {elapsed:.0f}ms{RESET}\n")

        print(f"{OK} All tasks completed via encrypted anycast routing.\n")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Skill-based anycast routing demo"
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--serve", action="store_true", help="Run as multi-skill agent"
    )
    group.add_argument(
        "--discover", action="store_true", help="Discover agents and send tasks"
    )
    args = parser.parse_args()

    try:
        if args.serve:
            asyncio.run(run_server())
        else:
            asyncio.run(run_discover())
    except KeyboardInterrupt:
        print(f"\n{BULLET} Shutting down.")


if __name__ == "__main__":
    main()
