"""End-to-end encrypted P2P chat — Noise_XX key exchange in action.

Run in two terminals:

    # Terminal 1 — start the server
    python encrypted_chat.py --server

    # Terminal 2 — connect as a client (copy PeerID from Terminal 1)
    python encrypted_chat.py --client 12D3KooW...

Every message travels over a Noise_XX encrypted channel
(Curve25519 ECDH + ChaCha20-Poly1305). No central server, no TLS certs.
"""

import argparse
import asyncio
import time

from agentanycast import AgentCard, Artifact, IncomingTask, Message, Node, Part, Skill
from agentanycast.did import peer_id_to_did_key

# ---------------------------------------------------------------------------
# ANSI helpers — no external deps
# ---------------------------------------------------------------------------

BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"
GREEN = "\033[32m"
CYAN = "\033[36m"
YELLOW = "\033[33m"
RED = "\033[31m"
WHITE = "\033[97m"
BLUE = "\033[34m"

BULLET = f"{DIM}[*]{RESET}"
OK = f"{GREEN}[+]{RESET}"
WARN = f"{YELLOW}[!]{RESET}"
ERR = f"{RED}[-]{RESET}"


def header(text: str) -> str:
    width = max(len(text), 48)
    line = "=" * width
    return f"\n{BOLD}{WHITE}{text}{RESET}\n{DIM}{line}{RESET}\n"


def kv(key: str, value: str, color: str = CYAN) -> str:
    return f"    {DIM}{key}:{RESET}  {color}{value}{RESET}"


# ---------------------------------------------------------------------------
# Server mode
# ---------------------------------------------------------------------------


async def run_server() -> None:
    print(header("AgentAnycast Encrypted P2P Chat"))

    card = AgentCard(
        name="Secure Echo Agent",
        description="Echoes messages over Noise_XX encrypted P2P.",
        skills=[Skill(id="echo", description="Echo the input message")],
    )

    print(f"{BULLET} Starting P2P node...")
    async with Node(card=card) as node:
        print(f"{OK} Node started")
        print(kv("PeerID", node.peer_id))
        print(kv("DID", peer_id_to_did_key(node.peer_id)))
        print(kv("Crypto", "Noise_XX (Curve25519 + ChaCha20-Poly1305)", YELLOW))
        print(kv("Skills", "[echo]"))
        print(f"\n{BULLET} Waiting for encrypted connections...\n")
        print(f"    {DIM}Tip: run in another terminal:{RESET}")
        print(f"    {CYAN}python encrypted_chat.py --client {node.peer_id}{RESET}\n")

        task_count = 0

        @node.on_task
        async def handle(task: IncomingTask) -> None:
            nonlocal task_count
            t0 = time.monotonic()
            task_count += 1

            text = task.messages[-1].parts[0].text
            sender = task.peer_id or "unknown"
            sender_short = sender[:16] + "..." if len(sender) > 16 else sender

            print(f"    {DIM}{'- ' * 24}{RESET}")
            print(f"{OK} Task #{task_count} received {GREEN}(encrypted channel){RESET}")
            print(kv("From", sender_short))
            print(kv("Message", repr(text), WHITE))

            reply_text = f"Echo: {text}"
            await task.complete(
                artifacts=[Artifact(name="echo", parts=[Part(text=reply_text)])]
            )

            elapsed = (time.monotonic() - t0) * 1000
            print(kv("Reply", repr(reply_text), GREEN))
            print(kv("Latency", f"{elapsed:.1f}ms", YELLOW))
            print()

        await node.serve_forever()


# ---------------------------------------------------------------------------
# Client mode
# ---------------------------------------------------------------------------


async def run_client(peer_id: str) -> None:
    print(header("AgentAnycast Encrypted P2P Client"))

    card = AgentCard(name="Chat Client")

    print(f"{BULLET} Starting client node...")
    async with Node(card=card) as node:
        print(f"{OK} Client started")
        print(kv("PeerID", node.peer_id))
        print(kv("DID", peer_id_to_did_key(node.peer_id)))
        print(kv("Crypto", "Noise_XX (Curve25519 + ChaCha20-Poly1305)", YELLOW))
        print()

        target_short = peer_id[:16] + "..." if len(peer_id) > 16 else peer_id
        print(f"{BULLET} Target: {CYAN}{target_short}{RESET}")
        print(f"{BULLET} Establishing encrypted connection...")

        # Interactive message loop
        msg_num = 0
        print(f"\n{OK} Ready — type messages below (Ctrl+C to quit)\n")

        while True:
            try:
                text = await asyncio.get_event_loop().run_in_executor(
                    None, lambda: input(f"  {BLUE}>{RESET} ")
                )
            except (EOFError, KeyboardInterrupt):
                print(f"\n{BULLET} Disconnected.")
                break

            text = text.strip()
            if not text:
                continue

            msg_num += 1
            print(f"\n{BULLET} Sending message #{msg_num} (encrypted)...")

            t0 = time.monotonic()
            msg = Message(role="user", parts=[Part(text=text)])
            handle = await node.send_task(msg, peer_id=peer_id)
            result = await handle.wait(timeout=30)
            elapsed = (time.monotonic() - t0) * 1000

            reply = result.artifacts[0].parts[0].text
            print(f"{OK} Response: {GREEN}{reply}{RESET}")
            print(f"    {DIM}Round-trip: {elapsed:.1f}ms (encrypted){RESET}\n")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(
        description="End-to-end encrypted P2P chat demo"
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--server", action="store_true", help="Run as echo server")
    group.add_argument("--client", metavar="PEER_ID", help="Connect to a server")
    args = parser.parse_args()

    try:
        if args.server:
            asyncio.run(run_server())
        else:
            asyncio.run(run_client(args.client))
    except KeyboardInterrupt:
        print(f"\n{BULLET} Shutting down.")


if __name__ == "__main__":
    main()
