# Quick Demo

Visual demos for terminal recordings and presentations.

## Encrypted P2P Chat

Two-terminal demo showing Noise_XX encrypted communication.

```bash
pip install agentanycast

# Terminal 1 — start the echo server
python encrypted_chat.py --server

# Terminal 2 — connect and chat (copy PeerID from Terminal 1)
python encrypted_chat.py --client 12D3KooW...
```

## Anycast Routing

Discover agents by skill and route tasks via anycast.

```bash
# Terminal 1 — start a multi-skill agent
python anycast_routing.py --serve

# Terminal 2 — discover skills and send tasks
python anycast_routing.py --discover
```

## What You'll See

- **Encrypted Chat** — live P2P messaging with round-trip timing, showing the Noise_XX handshake securing every message without TLS certificates.
- **Anycast Routing** — skill discovery across the network followed by automatic routing to the best-matching agent.

Both demos use ANSI colors for terminal readability. No dependencies beyond `agentanycast`.
