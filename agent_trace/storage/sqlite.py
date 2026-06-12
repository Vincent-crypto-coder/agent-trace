"""
SQLite storage for persistent traces.
"""

import json
import sqlite3
from ..span import Trace, Span


class SQLiteStorage:
    def __init__(self, db_path: str = "agent_trace.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS traces (
                trace_id TEXT PRIMARY KEY,
                project TEXT,
                input_text TEXT,
                output_text TEXT,
                start_time REAL,
                end_time REAL,
                duration_ms REAL,
                total_tokens INTEGER,
                total_cost REAL,
                step_count INTEGER,
                spans_json TEXT,
                metadata_json TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        conn.close()

    def save(self, trace: Trace):
        d = trace.to_dict()
        conn = sqlite3.connect(self.db_path)
        conn.execute(
            "INSERT OR REPLACE INTO traces VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (trace.trace_id, trace.project, trace.input_text, trace.output_text,
             trace.start_time, trace.end_time, trace.duration_ms,
             trace.total_tokens, trace.total_cost, trace.step_count,
             json.dumps(d["spans"]), json.dumps(trace.metadata),
             None))
        conn.commit()
        conn.close()

    def list_traces(self, project: str = None, limit: int = 50) -> list:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        if project:
            rows = conn.execute(
                "SELECT * FROM traces WHERE project=? ORDER BY start_time DESC LIMIT ?",
                (project, limit)).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM traces ORDER BY start_time DESC LIMIT ?",
                (limit,)).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def get_trace(self, trace_id: str) -> dict | None:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        row = conn.execute("SELECT * FROM traces WHERE trace_id=?", (trace_id,)).fetchone()
        conn.close()
        return dict(row) if row else None
