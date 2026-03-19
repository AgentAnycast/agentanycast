# LangGraph over P2P

Turn any LangGraph graph into a P2P agent with one function call.

## Run

```bash
pip install agentanycast[langgraph] langgraph
python main.py
```

## How It Works

`serve_graph()` wraps your LangGraph compiled graph in an AgentAnycast node. Incoming A2A messages become graph inputs, and the graph output is returned as A2A artifacts.
