# Agent 调试太难了？这个工具帮你像 Chrome DevTools 一样调试 AI Agent

> Agent 调用 5-20 次 LLM 和工具，出错后像黑盒。这个工具记录每一步，帮你快速定位问题。

## 引言

上周调试一个 Agent，它需要调用 3 次 LLM 和 2 次工具才能完成任务。结果返回了错误答案。

问题来了：**到底是哪一步出错了？**

是第一次 LLM 理解错了意图？还是工具返回了异常数据？还是最后一次 LLM 推理错了？

我只能把每一步的输入输出都 print 出来，一行一行看。花了 2 小时。

**如果有 Chrome DevTools 那样的调试工具就好了。**

于是我写了 **Agent Trace** —— 专门给 AI Agent 用的调试工具。

## 核心功能

### 一行代码开始追踪

```python
from agent_trace import Tracer

tracer = Tracer(project="my-agent")

result = tracer.run(agent_function, input="帮我订明天的机票")
tracer.summary()
```

自动记录每一步的：
- LLM 调用（模型、输入、输出、Token 数）
- 工具调用（函数名、参数、返回值）
- 耗时和成本

### 输出示例

```
┌──────────┬───────┬────────┬────────┬──────────┬────────┐
│ Trace ID │ Steps │ Tokens │  Cost  │ Duration │ Status │
├──────────┼───────┼────────┼────────┼──────────┼────────┤
│ a3f8b2c1 │     4 │    430 │ $0.005 │   2.6s   │   ✅   │
└──────────┴───────┴────────┴────────┴──────────┴────────┘
```

### 每步详情

```
🤖 ✅ plan — 245ms
  Model: gpt-4o-mini  Tokens: 50+20
  Input: "帮我订明天的机票"
  Output: "我应该先搜索航班"
🔧 ✅ search_flights — 1.2s
  Args: {"date": "2026-06-11"}
  Result: [{"flight": "CA123", "price": 1200}, ...]
🤖 ✅ decide — 320ms
  Model: gpt-4o-mini  Tokens: 80+15
  Input: "从3个航班中选择最便宜的"
  Output: "MU456最便宜，980元"
🔧 ✅ book_flight — 0.8s
  Args: {"flight": "MU456"}
  Result: {"status": "success", "booking_id": "ABC123"}
```

一眼看出：哪步最慢、哪步最贵、每步的输入输出是什么。

### OpenAI SDK 自动 Hook

如果你用 OpenAI SDK，不需要改任何代码：

```python
from agent_trace.integrations.openai import patch_openai
patch_openai()  # 一行搞定，所有 OpenAI 调用自动追踪
```

### Web 可视化

```bash
agent-trace serve --port 8080
```

打开浏览器看调用链时间线、Token 分布、成本分析。

## 跟 Langfuse 有什么区别？

| | Agent Trace | Langfuse |
|---|---|---|
| 上手 | pip install 就能用 | 需要注册或自部署 |
| 存储 | 本地 SQLite | 需要 PostgreSQL |
| 定位 | 专注 Agent 调试 | 通用可观测平台 |
| 特色 | 步进调试 + 成本分析 | Dashboard + Evals |

**Langfuse 是生产监控工具，Agent Trace 是开发调试工具。**

就像 Chrome DevTools 不是用来替代服务器监控的，而是帮你开发时快速定位问题。

## 实际使用场景

**场景 1：Agent 返回错误答案**

用 Agent Trace 看每步的输入输出，找出是哪步理解错了。

**场景 2：Agent 响应太慢**

用 Agent Trace 看每步的耗时，找出瓶颈是哪个 LLM 调用或工具调用。

**场景 3：API 花费太高**

用 Agent Trace 看每步的 Token 数和成本，找出最贵的步骤优化。

**场景 4：工具调用失败**

用 Agent Trace 看工具的参数和返回值，找出是参数传错了还是工具本身有 bug。

## 安装

```bash
pip install agent-trace

# 可选：Web Dashboard
pip install agent-trace[dashboard]

# 可选：OpenAI 自动追踪
pip install agent-trace[openai]
```

## 接下来

这个项目还在早期，TODO 里有很多想做的：
- LangChain / LlamaIndex 自动 Hook
- 调用链回放（从任意步骤重新执行）
- Agent 性能基线（跑多次，检测退化）

但核心功能已经能用了。如果你也在调试 Agent，可以试试。

---

**GitHub**: https://github.com/Vincent-crypto-coder/agent-trace

觉得有用的话，给个 ⭐ 吧！
