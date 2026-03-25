#!/usr/bin/env python3
from __future__ import annotations

import argparse

from orchestrator_common import (
    append_jsonl,
    append_progress_log,
    doc_refresh_log_path,
    ensure_state_root,
    ensure_task_exists,
    task_file_map,
    utc_now,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Record one document refresh decision.")
    parser.add_argument("--state-root", help="Path to orchestrator-state")
    parser.add_argument("--scope", choices=["skill", "task"], default="skill", help="Refresh scope")
    parser.add_argument("--task-id", help="Task ID when scope=task")
    parser.add_argument("--message-summary", required=True, help="Short summary of the triggering instruction")
    parser.add_argument("--considered-doc", action="append", default=[], help="Repeatable considered doc name")
    parser.add_argument("--updated-doc", action="append", default=[], help="Repeatable updated doc name")
    parser.add_argument("--note", help="Optional note")
    parser.add_argument("--progress-note", help="Optional Chinese progress note for task scope")
    parser.add_argument(
        "--status",
        choices=["updated", "checked", "not_needed"],
        default="checked",
        help="Refresh decision status",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    state_root = ensure_state_root(args.state_root)
    if args.scope == "task" and not args.task_id:
        raise SystemExit("--task-id is required when --scope=task")
    if args.scope == "task":
        ensure_task_exists(state_root, args.task_id)

    payload = {
        "ts": utc_now(),
        "type": "doc_refresh",
        "scope": args.scope,
        "status": args.status,
        "message_summary": args.message_summary,
        "considered_docs": args.considered_doc,
        "updated_docs": args.updated_doc,
    }
    if args.task_id:
        payload["task_id"] = args.task_id
    if args.note:
        payload["note"] = args.note
    append_jsonl(doc_refresh_log_path(state_root), payload)
    if args.scope == "task":
        task_paths = task_file_map(state_root, args.task_id)
        append_jsonl(
            task_paths["events"],
            {
                "ts": payload["ts"],
                "type": "task_doc_refresh",
                "task_id": args.task_id,
                "status": args.status,
                "considered_docs": args.considered_doc,
                "updated_docs": args.updated_doc,
            },
        )
        if args.progress_note:
            append_progress_log(task_paths["progress"], args.progress_note, ts=payload["ts"])
    print(f"Recorded doc refresh decision at {doc_refresh_log_path(state_root)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
