<p align="center">
  <img src="https://img.shields.io/badge/Agent-Trace-blue?style=for-the-badge&logo=opentelemetry" alt="Agent Trace">
  <img src="https://img.shields.io/badge/Python-3.10+-yellow?style=for-the-badge&logo=python" alt="Python">
  <img src="https://img.shields.io/pypi/v/agent-trace?style=for-the-badge&logo=pypi" alt="PyPI">
  <img src="https://img.shields.io/github/stars/Vincent-crypto-coder/agent-trace?style=for-the-badge&logo=github" alt="Stars">
</p>

<h1 align="center">🔍 Agent Trace</h1>

<p align="center">
  <b>Debug AI agents like Chrome DevTools</b><br>
  <sub>Step-by-step tracing, cost analysis, and visualization for multi-step LLM agents</sub>
</p>

---

## Why?

Agents make 5-20 LLM and tool calls per request. When something breaks, good luck figuring out which step failed, which one was slow, or which one cost you $0.50.

**Agent Trace** records every step and shows you exactly what happened.

```python
from agent_trace import Tracer

tracer = Tracer(project="my-agent")

def agent(input):
    # Your agent logic here
    ...

result = tracer.run(agent, input="Book me a flight")
tracer.summary()
```

Output:

```
╭──────────────── Agent Trace — my-agent ────────────────╮
│ Trace ID  │ Steps │ Tokens │   Cost │ Duration │ Status │
├───────────┼───────┼────────┼────────┼──────────┼────────┤
│ a3f8b2c1  │     4 │    430 │ $0.005 │   2.6s   │   ✅   │
╰───────────┴───────┴────────┴────────┴──────────┴────────╯
```

## Quick Start

```bash
pip install agent-trace
```

```python
from agent_trace import Tracer

tracer = Tracer(project="my-agent")

def my_agent(input):
    with tracer.span("think", kind="llm") as span:
        span.model = "gpt-4o-mini"
        span.input_text = input
        span.output_text = "I should search for flights"
        span.prompt_tokens = 50
        span.completion_tokens = 20

    with tracer.span("search_flights", kind="tool") as span:
        span.tool_name = "search_flights"
        span.tool_args = {"date": "2026-06-11"}
        span.tool_result = [{"flight": "CA123", "price": 1200}]

    return "Booked CA123"

result = tracer.run(my_agent, input="Book a flight tomorrow")
tracer.summary()
```

## OpenAI SDK Auto-Instrumentation

No code changes needed — just patch once:

```python
from agent_trace import Tracer
from agent_trace.integrations.openai import patch_openai

patch_openai()  # All OpenAI calls are now traced automatically

tracer = Tracer(project="my-agent")

def agent(question):
    from openai import OpenAI
    client = OpenAI()
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": question}],
    )
    return response.choices[0].message.content

result = tracer.run(agent, input="What is 2+2?")
tracer.summary()
```

## Features

| Feature | Description |
|---------|-------------|
| **Step-by-step tracing** | Record every LLM call, tool call, and custom span |
| **Cost breakdown** | See exactly how much each step costs |
| **Token tracking** | Prompt + completion tokens per step |
| **OpenAI auto-patch** | Zero-code instrumentation for OpenAI SDK |
| **SQLite storage** | Persistent traces, no cloud needed |
| **Web dashboard** | `agent-trace serve` to view traces in browser |
| **CLI** | `agent-trace list` and `agent-trace show` |
| **Nested spans** | Full call tree with parent-child relationships |

## Web Dashboard

```bash
pip install agent-trace[dashboard]
agent-trace serve --port 8080
```

Open `http://localhost:8080` to view all traces.

## CLI

```bash
# List recent traces
agent-trace list --db agent_trace.db

# Show trace details
agent-trace show a3f8b2c1

# Start dashboard
agent-trace serve --port 8080
```

## SQLite Storage

Traces are persisted to SQLite by default:

```python
from agent_trace import Tracer
from agent_trace.storage.sqlite import SQLiteStorage

storage = SQLiteStorage("my_traces.db")
tracer = Tracer(project="prod", storage=storage)
```

## Cost Reference

Built-in pricing for popular models (per 1M tokens, USD):

| Model | Input | Output |
|-------|-------|--------|
| gpt-4o | $2.50 | $10.00 |
| gpt-4o-mini | $0.15 | $0.60 |
| deepseek-chat | $0.14 | $0.28 |
| qwen-plus | $0.40 | $1.20 |
| claude-3-5-sonnet | $3.00 | $15.00 |

## Comparison

| | Agent Trace | Langfuse | Opik |
|---|---|---|---|
| Setup | `pip install` | Self-host or cloud | Self-host or cloud |
| Storage | Local SQLite | PostgreSQL | PostgreSQL |
| Focus | Agent debugging | General observability | Evaluation |
| OpenAI auto-patch | ✅ | ❌ | ❌ |
| Dashboard | ✅ | ✅ | ✅ |
| Best for | Quick debugging | Production monitoring | Eval pipelines |

## License

[MIT](LICENSE)

---

⭐ Star this repo if you find it useful!
