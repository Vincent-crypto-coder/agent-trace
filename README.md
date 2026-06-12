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

<p align="center">
  <a href="#why">Why</a> •
  <a href="#quick-start">Quick Start</a> •
  <a href="#features">Features</a> •
  <a href="#how-it-works">How It Works</a> •
  <a href="#api-reference">API</a> •
  <a href="#roadmap">Roadmap</a>
</p>

---

## Why?

Agents make 5-20 LLM and tool calls per request. When something breaks, good luck figuring out which step failed, which one was slow, or which one cost you $0.50.

**The problem:**

```
User: "Book me the cheapest flight tomorrow"

Agent internally:
  1. LLM call → understands intent → OK
  2. Tool call → search_flights → returns 3 results → OK
  3. LLM call → picks cheapest → WRONG (hallucinated the price)
  4. Tool call → books wrong flight → 💥

You see: wrong booking. But WHERE did it go wrong?
```

**Agent Trace** records every step and shows you exactly what happened:

```
╭──────────────── Agent Trace — flight-booking ────────────────╮
│ Trace ID  │ Steps │ Tokens │   Cost │ Duration │  Status    │
├───────────┼───────┼────────┼────────┼──────────┼────────────┤
│ a3f8b2c1  │     4 │    430 │ $0.005 │   2.6s   │  ❌ Error  │
╰───────────┴───────┴────────┴────────┴──────────┴────────────╯

Step-by-step:
  🤖 ✅ plan — 245ms, 70 tokens
     → "I will search for flights and book the cheapest one"

  🔧 ✅ search_flights(date="2026-06-11") — 1.2s
     → [{"flight": "CA123", "price": 1200}, {"flight": "MU456", "price": 980}]

  🤖 ❌ decide — 320ms, 95 tokens
     → "CA123 is cheapest at $800"  ← WRONG! Actual: MU456 at $980
     → Model hallucinated the price comparison

  🔧 ✅ book_flight(flight="CA123") — 0.8s
     → {"status": "success", "booking_id": "ABC123"}
```

**Found it.** Step 3 hallucinated. Now you know to fix the prompt or add price verification.

---

## Quick Start

### 1. Install

```bash
pip install agent-trace
```

### 2. Trace your agent

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

### 3. See the results

```
┌──────────┬───────┬────────┬────────┬──────────┬────────┐
│ Trace ID │ Steps │ Tokens │  Cost  │ Duration │ Status │
├──────────┼───────┼────────┼────────┼──────────┼────────┤
│ a3f8b2c1 │     2 │     70 │ $0.001 │   1.5s   │   ✅   │
└──────────┴───────┴────────┴────────┴──────────┴────────┘
```

---

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
| **Error tracking** | See which step failed and why |

---

## How It Works

### Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     Your Agent Code                      │
│                                                          │
│   tracer.run(agent_fn, input="...")                      │
│       │                                                  │
│       ├── tracer.span("step1", kind="llm")              │
│       │   └── Records: model, input, output, tokens     │
│       │                                                  │
│       ├── tracer.span("step2", kind="tool")             │
│       │   └── Records: tool_name, args, result          │
│       │                                                  │
│       └── tracer.span("step3", kind="llm")              │
│           └── Records: model, input, output, tokens     │
│                                                          │
├─────────────────────────────────────────────────────────┤
│                     Agent Trace                          │
│                                                          │
│   Tracer ──→ Trace ──→ [Span, Span, Span, ...]         │
│       │                                                  │
│       ├── Storage (SQLite / Memory)                      │
│       └── Reporter (Terminal / Web Dashboard)            │
└─────────────────────────────────────────────────────────┘
```

### Data Model

```
Trace (one agent execution)
├── trace_id: "a3f8b2c1"
├── project: "my-agent"
├── input: "Book a flight"
├── output: "Booked CA123"
├── duration_ms: 2600
├── total_tokens: 430
├── total_cost: $0.005
│
├── Span 1 (root)
│   ├── kind: "llm"
│   ├── model: "gpt-4o-mini"
│   ├── input_text: "Book a flight"
│   ├── output_text: "I should search..."
│   ├── prompt_tokens: 50
│   ├── completion_tokens: 20
│   └── children: []
│
├── Span 2 (root)
│   ├── kind: "tool"
│   ├── tool_name: "search_flights"
│   ├── tool_args: {"date": "2026-06-11"}
│   ├── tool_result: [{"flight": "CA123", ...}]
│   └── children: []
│
└── Span 3 (root)
    ├── kind: "llm"
    ├── model: "gpt-4o-mini"
    ├── ...
    └── children: [Span 3.1 (nested child)]
```

---

## OpenAI SDK Auto-Instrumentation

No code changes needed — just patch once at startup:

```python
from agent_trace import Tracer
from agent_trace.integrations.openai import patch_openai

patch_openai()  # All OpenAI calls are now traced automatically

tracer = Tracer(project="my-agent")

def agent(question):
    from openai import OpenAI
    client = OpenAI()

    # This call is traced automatically — no manual span needed
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": question}],
    )
    return response.choices[0].message.content

result = tracer.run(agent, input="What is 2+2?")
tracer.summary()
```

**What gets captured automatically:**
- Model name
- Input messages
- Output text
- Prompt tokens + completion tokens
- Latency
- Errors

---

## Web Dashboard

```bash
pip install agent-trace[dashboard]
agent-trace serve --port 8080
```

Open `http://localhost:8080` to view all traces in a dark-themed web UI.

The dashboard shows:
- All traces in a table (ID, project, steps, tokens, cost, duration)
- Sortable by any column
- Click a trace to see step-by-step details

---

## CLI

```bash
# List recent traces
agent-trace list --db agent_trace.db

# List traces for a specific project
agent-trace list --project my-agent --limit 10

# Show trace details (step-by-step)
agent-trace show a3f8b2c1

# Start web dashboard
agent-trace serve --port 8080
```

---

## SQLite Storage

Traces are persisted to SQLite by default. No external database needed.

```python
from agent_trace import Tracer
from agent_trace.storage.sqlite import SQLiteStorage

storage = SQLiteStorage("my_traces.db")
tracer = Tracer(project="prod", storage=storage)
```

You can also use in-memory storage (traces are lost when the process exits):

```python
from agent_trace.storage.memory import MemoryStorage

storage = MemoryStorage()
tracer = Tracer(project="test", storage=storage)
```

---

## Cost Reference

Built-in pricing for popular models (per 1M tokens, USD):

| Model | Input | Output |
|-------|-------|--------|
| gpt-4o | $2.50 | $10.00 |
| gpt-4o-mini | $0.15 | $0.60 |
| gpt-4-turbo | $10.00 | $30.00 |
| gpt-3.5-turbo | $0.50 | $1.50 |
| deepseek-chat | $0.14 | $0.28 |
| deepseek-coder | $0.14 | $0.28 |
| qwen-turbo | $0.05 | $0.10 |
| qwen-plus | $0.40 | $1.20 |
| qwen-max | $2.40 | $9.60 |
| claude-3-5-sonnet | $3.00 | $15.00 |
| claude-3-5-haiku | $0.80 | $4.00 |

Unknown models default to $1.00 / $3.00 per 1M tokens.

---

## Comparison

| | Agent Trace | Langfuse | Opik |
|---|---|---|---|
| **Setup** | `pip install` | Self-host or cloud | Self-host or cloud |
| **Storage** | Local SQLite | PostgreSQL | PostgreSQL |
| **Focus** | Agent debugging | General observability | Evaluation |
| **OpenAI auto-patch** | ✅ | ❌ | ❌ |
| **Dashboard** | ✅ | ✅ | ✅ |
| **Best for** | Quick debugging | Production monitoring | Eval pipelines |
| **Dependencies** | 2 (rich, httpx) | 20+ | 20+ |
| **Size** | ~50KB | ~5MB | ~5MB |

**When to use Agent Trace:**
- You're developing an agent and need to debug it
- You want to see which step is slow or expensive
- You don't want to set up a database or cloud account

**When to use Langfuse:**
- You need production monitoring at scale
- You want user analytics and session tracking
- You're running multiple agents in production

---

## Use Cases

### 1. Debug wrong answers

```python
# Agent returns wrong answer — which step went wrong?
result = tracer.run(my_agent, input="What's the capital of France?")
# Check each step's input/output to find the hallucination
```

### 2. Find slow steps

```python
# Agent takes 10 seconds — which step is the bottleneck?
tracer.summary()
# See duration per step, optimize the slowest one
```

### 3. Reduce costs

```python
# Agent costs $0.10 per request — too expensive
tracer.summary()
# See cost per step, switch to cheaper model for non-critical steps
```

### 4. Debug tool failures

```python
# Agent fails intermittently — which tool is unreliable?
# Check tool_args and tool_result in each span
```

---

## API Reference

### `Tracer(project, storage)`

Main entry point for tracing.

```python
tracer = Tracer(project="my-agent")         # In-memory storage (default)
tracer = Tracer(project="prod", storage=SQLiteStorage("traces.db"))
```

### `tracer.run(fn, input, **kwargs)`

Run a function and trace it. Returns the function's return value.

```python
result = tracer.run(my_agent, input="Book a flight")
```

### `tracer.span(name, kind)`

Context manager for a traced span. Returns a `Span` object.

```python
with tracer.span("step_name", kind="llm") as span:
    span.model = "gpt-4o-mini"
    span.input_text = "..."
    span.output_text = "..."
    span.prompt_tokens = 50
    span.completion_tokens = 20
```

### `Span` fields

| Field | Type | Description |
|-------|------|-------------|
| `name` | str | Span name |
| `kind` | str | "llm", "tool", "agent", or "custom" |
| `status` | str | "ok" or "error" |
| `model` | str | LLM model name |
| `input_text` | str | LLM input |
| `output_text` | str | LLM output |
| `prompt_tokens` | int | Input tokens |
| `completion_tokens` | int | Output tokens |
| `tool_name` | str | Tool function name |
| `tool_args` | dict | Tool arguments |
| `tool_result` | Any | Tool return value |
| `error_message` | str | Error message (if failed) |
| `metadata` | dict | Custom metadata |

### `tracer.summary()`

Print a summary table of all traces.

### `patch_openai()`

Monkey-patch OpenAI SDK to auto-trace all `chat.completions.create` calls.

```python
from agent_trace.integrations.openai import patch_openai
patch_openai()
```

---

## FAQ

**Q: Does it work with async code?**

A: The OpenAI integration supports both sync and async. Manual spans use synchronous context managers currently. Async span support is on the roadmap.

**Q: Does it work with LangChain / LlamaIndex?**

A: Not yet with auto-instrumentation. You can manually wrap LangChain steps with `tracer.span()`. Auto-hook for LangChain is on the roadmap.

**Q: Is there a cloud version?**

A: No. Agent Trace is designed for local development. For production monitoring, use Langfuse or similar tools.

**Q: How much overhead does tracing add?**

A: Near zero. Span creation is ~0.01ms. SQLite writes are async. The overhead is negligible compared to LLM call latency (100-2000ms).

**Q: Can I export traces to JSON?**

A: Yes. `trace.to_dict()` returns a JSON-serializable dict.

---

## Roadmap

- [ ] LangChain auto-instrumentation
- [ ] LlamaIndex auto-instrumentation
- [ ] Async span support
- [ ] Trace replay (re-execute from any step)
- [ ] Performance baseline (run N times, detect regressions)
- [ ] Trace comparison (side-by-side diff of two traces)
- [ ] Token budget alerts
- [ ] OpenTelemetry export

---

## Contributing

Contributions are welcome! Here's how:

1. Fork the repo
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## License

[MIT](LICENSE)

---

<p align="center">
  ⭐ Star this repo if you find it useful!<br>
  <sub>Built with ❤️ for the AI agent community</sub>
</p>
