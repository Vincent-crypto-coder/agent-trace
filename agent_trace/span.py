"""
Data structures for traces and spans.
"""

import time
import uuid
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Span:
    """A single step in an agent execution."""
    span_id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])
    parent_id: str | None = None
    name: str = ""
    kind: str = "llm"  # llm | tool | agent | custom
    status: str = "ok"  # ok | error

    # Timing
    start_time: float = field(default_factory=time.time)
    end_time: float = 0.0

    # LLM fields
    model: str = ""
    input_text: str = ""
    output_text: str = ""
    prompt_tokens: int = 0
    completion_tokens: int = 0

    # Tool fields
    tool_name: str = ""
    tool_args: dict = field(default_factory=dict)
    tool_result: Any = None

    # Error
    error_message: str = ""

    # Metadata
    metadata: dict = field(default_factory=dict)

    # Children
    children: list = field(default_factory=list)

    @property
    def duration_ms(self) -> float:
        end = self.end_time if self.end_time else time.time()
        return round((end - self.start_time) * 1000, 1)

    @property
    def total_tokens(self) -> int:
        return self.prompt_tokens + self.completion_tokens

    def finish(self, status="ok", error_message=""):
        self.end_time = time.time()
        self.status = status
        self.error_message = error_message

    def to_dict(self) -> dict:
        return {
            "span_id": self.span_id,
            "parent_id": self.parent_id,
            "name": self.name,
            "kind": self.kind,
            "status": self.status,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration_ms": self.duration_ms,
            "model": self.model,
            "input_text": self.input_text[:500],
            "output_text": self.output_text[:500],
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "tool_name": self.tool_name,
            "tool_args": self.tool_args,
            "tool_result": str(self.tool_result)[:500] if self.tool_result else None,
            "error_message": self.error_message,
            "metadata": self.metadata,
            "children": [c.to_dict() for c in self.children],
        }


@dataclass
class Trace:
    """A complete agent execution trace."""
    trace_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    project: str = "default"
    input_text: str = ""
    output_text: str = ""
    start_time: float = field(default_factory=time.time)
    end_time: float = 0.0
    spans: list = field(default_factory=list)
    metadata: dict = field(default_factory=dict)

    @property
    def duration_ms(self) -> float:
        end = self.end_time if self.end_time else time.time()
        return round((end - self.start_time) * 1000, 1)

    @property
    def total_tokens(self) -> int:
        return sum(s.total_tokens for s in self._all_spans())

    @property
    def total_cost(self) -> float:
        from .tracer import estimate_cost
        cost = 0.0
        for s in self._all_spans():
            if s.model:
                cost += estimate_cost(s.model, s.prompt_tokens, s.completion_tokens)
        return round(cost, 6)

    @property
    def step_count(self) -> int:
        return len(self._all_spans())

    def _all_spans(self) -> list:
        result = []
        for s in self.spans:
            result.append(s)
            result.extend(s.children)
        return result

    def finish(self):
        self.end_time = time.time()

    def to_dict(self) -> dict:
        return {
            "trace_id": self.trace_id,
            "project": self.project,
            "input_text": self.input_text[:200],
            "output_text": self.output_text[:200],
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration_ms": self.duration_ms,
            "total_tokens": self.total_tokens,
            "total_cost": self.total_cost,
            "step_count": self.step_count,
            "spans": [s.to_dict() for s in self.spans],
            "metadata": self.metadata,
        }
