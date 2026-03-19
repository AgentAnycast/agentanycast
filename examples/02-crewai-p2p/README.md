# CrewAI over P2P

Turn any CrewAI crew into a P2P agent with one function call.

## Run

```bash
pip install agentanycast[crewai] crewai
python main.py
```

The crew is now reachable from any network. Other agents can send research tasks to it by PeerID or by skill (`research`).

## How It Works

`serve_crew()` wraps your CrewAI crew in an AgentAnycast node:
- Incoming A2A tasks are translated into CrewAI task inputs
- CrewAI output is translated back into A2A artifacts
- All communication is end-to-end encrypted
