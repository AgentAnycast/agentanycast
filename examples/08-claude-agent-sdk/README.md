# Claude Agent SDK over P2P

Turn a Claude Agent into a P2P agent with one function call.

## Run

```bash
pip install agentanycast[claude] claude-agent-sdk
python main.py
```

The agent is now reachable from any network. Other agents can send tasks to it by PeerID or by skill (`code_review`).

## How It Works

`serve_claude_agent()` wraps your Claude Agent prompt in an AgentAnycast node:
- Incoming A2A tasks are forwarded to `query()` as text input
- The agent's result is translated back into A2A artifacts
- All communication is end-to-end encrypted
