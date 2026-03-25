#!/usr/bin/env python3
from __future__ import annotations

import argparse

from orchestrator_common import (
    append_jsonl,
    append_progress_log,
    ensure_state_root,
    ensure_task_exists,
    load_state,
    save_state,
    sync_task_to_ledger,
    task_file_map,
    task_md_from_state,
    utc_now,
    write_text,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Sync task.md from state.json.")
    parser.add_argument("task_id", help="Task ID")
    parser.add_argument("--state-root", help="Path to orchestrator-state")
    parser.add_argument("--notes", help="Optional Chinese notes appended as a remarks section")
    parser.add_argument("--event-type", default="task_doc_synced", help="Event type to append")
    parser.add_argument("--progress-note", help="Optional Chinese progress note")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    state_root = ensure_state_root(args.state_root)
    ensure_task_exists(state_root, args.task_id)

    state = load_state(state_root, args.task_id)
    paths = task_file_map(state_root, args.task_id)
    now = utc_now()

    write_text(paths["task"], task_md_from_state(state, extra_notes=args.notes))
    save_state(state_root, args.task_id, state)
    sync_task_to_ledger(state_root, state)

    append_jsonl(
        paths["events"],
        {
            "ts": now,
            "type": args.event_type,
            "task_id": args.task_id,
            "phase": state.get("phase"),
            "status": state.get("status"),
        },
    )
    if args.progress_note:
        append_progress_log(paths["progress"], args.progress_note, ts=now)

    print(f"Synchronized task.md for {args.task_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
