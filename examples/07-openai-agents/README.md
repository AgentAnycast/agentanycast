# OpenAI Agents SDK over P2P

Turn any OpenAI Agent into a P2P agent with one function call.

## Run

```bash
pip install agentanycast[openai-agents] openai-agents
python main.py
```

The agent is now reachable from any network. Other agents can send tasks to it by PeerID or by skill (`help`).

## How It Works

`serve_openai_agent()` wraps your OpenAI Agent in an AgentAnycast node:
- Incoming A2A tasks are forwarded to `Runner.run()` as text input
- The agent's `final_output` is translated back into A2A artifacts
- All communication is end-to-end encrypted
