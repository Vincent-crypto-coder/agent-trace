"""
Auto-instrument OpenAI SDK calls.

Usage:
    from agent_trace.integrations.openai import patch_openai
    patch_openai()  # Call once, all OpenAI calls are now traced automatically
"""

import functools
from ..span import Span
from ..tracer import get_current_trace, get_current_span


_patched = False


def patch_openai():
    """Monkey-patch OpenAI client to auto-trace all chat completions calls."""
    global _patched
    if _patched:
        return
    try:
        import openai
    except ImportError:
        raise ImportError("openai package required. Install: pip install agent-trace[openai]")

    original_create = openai.OpenAI.chat.completions.create
    original_async_create = openai.AsyncOpenAI.chat.completions.create

    @functools.wraps(original_create)
    def traced_create(self, *args, **kwargs):
        trace = get_current_trace()
        if not trace:
            return original_create(self, *args, **kwargs)

        span = Span(
            name="openai.chat.completions.create",
            kind="llm",
            model=kwargs.get("model", ""),
            input_text=str(kwargs.get("messages", ""))[:500],
        )
        parent = get_current_span()
        if parent:
            span.parent_id = parent.span_id
            parent.children.append(span)
        else:
            trace.spans.append(span)

        try:
            response = original_create(self, *args, **kwargs)
            if hasattr(response, "usage") and response.usage:
                span.prompt_tokens = response.usage.prompt_tokens or 0
                span.completion_tokens = response.usage.completion_tokens or 0
            if hasattr(response, "choices") and response.choices:
                span.output_text = response.choices[0].message.content or ""
            span.finish()
            return response
        except Exception as e:
            span.finish(status="error", error_message=str(e))
            raise

    @functools.wraps(original_async_create)
    async def traced_async_create(self, *args, **kwargs):
        trace = get_current_trace()
        if not trace:
            return await original_async_create(self, *args, **kwargs)

        span = Span(
            name="openai.chat.completions.create (async)",
            kind="llm",
            model=kwargs.get("model", ""),
            input_text=str(kwargs.get("messages", ""))[:500],
        )
        parent = get_current_span()
        if parent:
            span.parent_id = parent.span_id
            parent.children.append(span)
        else:
            trace.spans.append(span)

        try:
            response = await original_async_create(self, *args, **kwargs)
            if hasattr(response, "usage") and response.usage:
                span.prompt_tokens = response.usage.prompt_tokens or 0
                span.completion_tokens = response.usage.completion_tokens or 0
            if hasattr(response, "choices") and response.choices:
                span.output_text = response.choices[0].message.content or ""
            span.finish()
            return response
        except Exception as e:
            span.finish(status="error", error_message=str(e))
            raise

    openai.OpenAI.chat.completions.create = traced_create
    openai.AsyncOpenAI.chat.completions.create = traced_async_create
    _patched = True
