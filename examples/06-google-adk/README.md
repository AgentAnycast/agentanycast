# Google ADK over P2P

Turn any Google ADK agent into a P2P agent with one function call.

## Run

```bash
pip install agentanycast[adk] google-adk
python main.py
```

The agent is now reachable from any network. Other agents can send tasks to it by PeerID or by skill (`help`).

## How It Works

`serve_adk_agent()` wraps your Google ADK agent in an AgentAnycast node:
- Incoming A2A tasks are translated into ADK `Content` messages
- ADK output events are collected and translated back into A2A artifacts
- Each task runs in a fresh session with a unique session ID
- All communication is end-to-end encrypted
