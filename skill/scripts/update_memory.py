#!/usr/bin/env python3
from __future__ import annotations

import argparse

from orchestrator_common import (
    append_workspace_memory_entries,
    append_workspace_session_note,
    ensure_workspace_scaffold,
    resolve_state_root,
    resolve_workspace_root,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Append structured facts, decisions, preferences, and constraints to workspace memory.")
    parser.add_argument("--workspace", help="Workspace root")
    parser.add_argument("--state-root", help="Optional orchestrator-state path used to infer the workspace root")
    parser.add_argument("--fact", action="append", default=[], help="Repeatable fact entry")
    parser.add_argument("--decision", action="append", default=[], help="Repeatable decision entry")
    parser.add_argument("--preference", action="append", default=[], help="Repeatable preference entry")
    parser.add_argument("--constraint", action="append", default=[], help="Repeatable constraint entry")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    state_root = resolve_state_root(args.state_root) if args.state_root else None
    workspace_root = resolve_workspace_root(args.workspace, state_root=state_root)
    ensure_workspace_scaffold(workspace_root, state_root=state_root)

    entries: list[tuple[str, str]] = []
    entries.extend(("fact", item) for item in args.fact)
    entries.extend(("decision", item) for item in args.decision)
    entries.extend(("preference", item) for item in args.preference)
    entries.extend(("constraint", item) for item in args.constraint)

    if not entries:
        raise SystemExit("Provide at least one of --fact, --decision, --preference, or --constraint")

    append_workspace_memory_entries(workspace_root, entries, source="update_memory.py")
    append_workspace_session_note(
        workspace_root,
        "memory updated",
        [f"entries: {len(entries)}"],
    )
    print(f"Appended {len(entries)} memory entry(ies) to {workspace_root / 'MEMORY.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
