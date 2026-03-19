# Hello World

The simplest AgentAnycast example — two agents communicating over encrypted P2P.

## Python

```bash
pip install agentanycast

# Terminal 1 — start the echo agent
python server.py

# Terminal 2 — send it a message (copy PeerID from Terminal 1)
python client.py 12D3KooW... "Hello, world!"
```

## TypeScript

```bash
npm install agentanycast tsx

# Terminal 1 — start the echo agent
npx tsx server.ts

# Terminal 2 — send it a message (copy PeerID from Terminal 1)
npx tsx client.ts 12D3KooW... "Hello, world!"
```

## What Happens

1. The server starts a P2P node and registers the "echo" skill
2. The client connects to the server by PeerID
3. The message is sent over Noise_XX encrypted P2P
4. The server echoes it back as an A2A artifact

Python and TypeScript agents can talk to each other — they share the same protocol.
