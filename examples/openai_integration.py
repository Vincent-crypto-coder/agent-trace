"""
OpenAI SDK auto-instrumentation.
"""

import os
from agent_trace import Tracer
from agent_trace.integrations.openai import patch_openai

# 1. Patch OpenAI — all calls are now auto-traced
patch_openai()

# 2. Create tracer
tracer = Tracer(project="openai-demo")


def my_agent(question: str):
    from openai import OpenAI
    client = OpenAI()  # Uses OPENAI_API_KEY env var

    with tracer.span("ask", kind="llm") as span:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": question}],
        )
        return response.choices[0].message.content


# 3. Run — OpenAI calls are traced automatically
result = tracer.run(my_agent, input="What is 2+2?", question="What is 2+2?")
print(f"Answer: {result}")

# 4. View traces
tracer.summary()
