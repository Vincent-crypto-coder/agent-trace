"""
Web dashboard for viewing traces.
"""

import json
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from ..storage.sqlite import SQLiteStorage

templates_dir = Path(__file__).parent / "templates"


def create_app(db_path: str = "agent_trace.db") -> FastAPI:
    app = FastAPI(title="Agent Trace Dashboard")
    storage = SQLiteStorage(db_path)

    @app.get("/", response_class=HTMLResponse)
    async def index(request: Request):
        traces = storage.list_traces(limit=50)
        return templates.TemplateResponse("index.html", {"request": request, "traces": traces})

    @app.get("/api/traces")
    async def api_traces(project: str = None, limit: int = 50):
        return storage.list_traces(project=project, limit=limit)

    @app.get("/api/traces/{trace_id}")
    async def api_trace(trace_id: str):
        t = storage.get_trace(trace_id)
        if not t:
            return {"error": "not found"}
        if "spans_json" in t:
            t["spans"] = json.loads(t["spans_json"])
        return t

    return app
