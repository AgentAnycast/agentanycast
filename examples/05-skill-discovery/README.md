# Skill Discovery & Anycast

Discover agents by skill and send tasks without knowing their address.

## Run

```bash
# Terminal 1 — start an echo agent
agentanycast demo

# Terminal 2 — discover and call it by skill
python main.py
```

## How It Works

1. `node.discover("echo")` queries the skill registry (DHT + Relay) for agents offering the "echo" skill
2. `node.send_task(msg, skill="echo")` uses anycast routing — the network picks the best available agent
3. You never need to know the agent's PeerID or IP address
