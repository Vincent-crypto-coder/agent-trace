"""
In-memory storage (default).
"""

from ..span import Trace


class MemoryStorage:
    def __init__(self):
        self.traces: list[Trace] = []

    def save(self, trace: Trace):
        self.traces.append(trace)

    def list_traces(self, project: str = None, limit: int = 50) -> list:
        traces = self.traces
        if project:
            traces = [t for t in traces if t.project == project]
        return traces[-limit:]

    def get_trace(self, trace_id: str) -> Trace | None:
        for t in self.traces:
            if t.trace_id == trace_id:
                return t
        return None
