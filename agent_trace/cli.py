"""
CLI entry point.
"""

import argparse
import json
from rich.console import Console
from rich.table import Table

console = Console()


def main():
    parser = argparse.ArgumentParser(description="Agent Trace — Debug AI agents")
    sub = parser.add_subparsers(dest="command")

    # list
    p_list = sub.add_parser("list", help="List recent traces")
    p_list.add_argument("--project", default=None)
    p_list.add_argument("--limit", type=int, default=20)
    p_list.add_argument("--db", default="agent_trace.db")

    # show
    p_show = sub.add_parser("show", help="Show trace details")
    p_show.add_argument("trace_id")
    p_show.add_argument("--db", default="agent_trace.db")

    # serve
    p_serve = sub.add_parser("serve", help="Start web dashboard")
    p_serve.add_argument("--port", type=int, default=8080)
    p_serve.add_argument("--db", default="agent_trace.db")

    args = parser.parse_args()

    if args.command == "list":
        from .storage.sqlite import SQLiteStorage
        storage = SQLiteStorage(args.db)
        traces = storage.list_traces(project=args.project, limit=args.limit)
        if not traces:
            console.print("[yellow]No traces found.[/yellow]")
            return
        table = Table(title="Recent Traces")
        table.add_column("ID", style="cyan")
        table.add_column("Project")
        table.add_column("Steps", justify="center")
        table.add_column("Tokens", justify="center")
        table.add_column("Cost", justify="center")
        table.add_column("Duration", justify="center")
        table.add_column("Time")
        for t in traces:
            table.add_row(
                t["trace_id"][:8], t["project"],
                str(t["step_count"]), str(t["total_tokens"]),
                f"${t['total_cost']:.4f}" if t["total_cost"] else "$0",
                f"{t['duration_ms']:.0f}ms",
                str(t.get("created_at", ""))[:19],
            )
        console.print(table)

    elif args.command == "show":
        from .storage.sqlite import SQLiteStorage
        storage = SQLiteStorage(args.db)
        t = storage.get_trace(args.trace_id)
        if not t:
            console.print(f"[red]Trace {args.trace_id} not found[/red]")
            return
        console.print(f"[bold cyan]Trace: {t['trace_id']}[/bold cyan]")
        console.print(f"  Project: {t['project']}")
        console.print(f"  Duration: {t['duration_ms']:.0f}ms")
        console.print(f"  Tokens: {t['total_tokens']}")
        console.print(f"  Cost: ${t['total_cost']:.4f}")
        console.print()
        spans = json.loads(t.get("spans_json", "[]"))
        _print_spans(spans, indent=2)

    elif args.command == "serve":
        from .dashboard.app import create_app
        import uvicorn
        app = create_app(args.db)
        console.print(f"[green]Dashboard: http://localhost:{args.port}[/green]")
        uvicorn.run(app, host="0.0.0.0", port=args.port)

    else:
        parser.print_help()


def _print_spans(spans, indent=2):
    for s in spans:
        prefix = " " * indent
        icon = "🤖" if s["kind"] == "llm" else "🔧" if s["kind"] == "tool" else "📌"
        status = "✅" if s["status"] == "ok" else "❌"
        console.print(f"{prefix}{icon} {status} {s['name']} — {s['duration_ms']:.0f}ms")
        if s.get("model"):
            console.print(f"{prefix}  Model: {s['model']}  Tokens: {s['prompt_tokens']}+{s['completion_tokens']}")
        if s.get("input_text"):
            console.print(f"{prefix}  Input: {s['input_text'][:100]}...")
        if s.get("output_text"):
            console.print(f"{prefix}  Output: {s['output_text'][:100]}...")
        if s.get("error_message"):
            console.print(f"{prefix}  [red]Error: {s['error_message']}[/red]")
        if s.get("children"):
            _print_spans(s["children"], indent + 2)
