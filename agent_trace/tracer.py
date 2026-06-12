"""
Core tracer — records agent execution steps.
"""

import time
import functools
from contextvars import ContextVar
from typing import Callable

from .span import Span, Trace

# Current trace context (thread-safe via contextvars)
_current_trace: ContextVar[Trace | None] = ContextVar("current_trace", default=None)
_current_span: ContextVar[Span | None] = ContextVar("current_span", default=None)

# Cost per 1M tokens (USD)
PRICING = {
    "gpt-4o": {"input": 2.50, "output": 10.00},
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "gpt-4-turbo": {"input": 10.00, "output": 30.00},
    "gpt-3.5-turbo": {"input": 0.50, "output": 1.50},
    "deepseek-chat": {"input": 0.14, "output": 0.28},
    "deepseek-coder": {"input": 0.14, "output": 0.28},
    "qwen-turbo": {"input": 0.05, "output": 0.10},
    "qwen-plus": {"input": 0.40, "output": 1.20},
    "qwen-max": {"input": 2.40, "output": 9.60},
    "claude-3-5-sonnet": {"input": 3.00, "output": 15.00},
    "claude-3-5-haiku": {"input": 0.80, "output": 4.00},
    "claude-sonnet-4": {"input": 3.00, "output": 15.00},
    "claude-haiku-3.5": {"input": 0.80, "output": 4.00},
}


def estimate_cost(model: str, prompt_tokens: int, completion_tokens: int) -> float:
    pricing = PRICING.get(model, {"input": 1.0, "output": 3.0})
    return (prompt_tokens * pricing["input"] + completion_tokens * pricing["output"]) / 1_000_000


class Tracer:
    """Record agent execution traces."""

    def __init__(self, project: str = "default", storage=None):
        self.project = project
        self.storage = storage
        self._traces = []

    def run(self, fn: Callable = None, *, input: str = "", **kwargs):
        """Run a function and trace it. Can be used as decorator or direct call."""
        if fn is not None:
            return self._trace_fn(fn, input=input, **kwargs)
        # Decorator mode: @tracer.run(input="...")
        def decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kw):
                return self._trace_fn(func, input=input, *args, **kw)
            return wrapper
        return decorator

    def _trace_fn(self, fn, input="", *args, **kwargs):
        trace = Trace(project=self.project, input_text=input)
        token = _current_trace.set(trace)
        try:
            result = fn(*args, **kwargs)
            trace.output_text = str(result)[:200] if result else ""
            trace.finish()
            self._save(trace)
            return result
        except Exception as e:
            trace.finish()
            self._save(trace)
            raise
        finally:
            _current_trace.reset(token)

    def span(self, name: str, kind: str = "custom"):
        """Context manager for a traced span."""
        return _SpanContext(name=name, kind=kind, tracer=self)

    def _save(self, trace: Trace):
        self._traces.append(trace)
        if self.storage:
            self.storage.save(trace)

    def get_traces(self) -> list:
        return self._traces

    def summary(self):
        """Print a summary table."""
        from rich.console import Console
        from rich.table import Table
        console = Console()
        table = Table(title=f"Agent Trace — {self.project}")
        table.add_column("Trace ID", style="cyan")
        table.add_column("Steps", justify="center")
        table.add_column("Tokens", justify="center")
        table.add_column("Cost", justify="center")
        table.add_column("Duration", justify="center")
        table.add_column("Status", justify="center")
        for t in self._traces:
            status = "✅" if all(s.status == "ok" for s in t._all_spans()) else "❌"
            table.add_row(t.trace_id[:8], str(t.step_count),
                          str(t.total_tokens), f"${t.total_cost:.4f}",
                          f"{t.duration_ms:.0f}ms", status)
        console.print(table)


class _SpanContext:
    """Context manager for creating spans."""

    def __init__(self, name, kind, tracer):
        self.name = name
        self.kind = kind
        self.tracer = tracer
        self.span = None

    def __enter__(self) -> Span:
        trace = _current_trace.get()
        self.span = Span(name=self.name, kind=self.kind)
        if trace:
            parent = _current_span.get()
            if parent:
                self.span.parent_id = parent.span_id
                parent.children.append(self.span)
            else:
                trace.spans.append(self.span)
        token = _current_span.set(self.span)
        self._token = token
        return self.span

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self.span.finish(status="error", error_message=str(exc_val))
        else:
            self.span.finish()
        _current_span.reset(self._token)
        return False


def get_current_trace() -> Trace | None:
    return _current_trace.get()


def get_current_span() -> Span | None:
    return _current_span.get()
