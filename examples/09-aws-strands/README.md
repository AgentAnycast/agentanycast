# AWS Strands Agent over P2P

Turn any AWS Strands Agent into a P2P agent with one function call.

## Run

```bash
pip install agentanycast[strands] strands-agents
python main.py
```

The agent is now reachable from any network. Other agents can send tasks to it by PeerID or by skill (`help`).

## How It Works

`serve_strands_agent()` wraps your Strands Agent in an AgentAnycast node:
- Incoming A2A tasks are forwarded to the agent's `__call__` method
- The agent's response is translated back into A2A artifacts
- All communication is end-to-end encrypted
