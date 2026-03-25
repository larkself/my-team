#!/usr/bin/env python3
from __future__ import annotations

import argparse

from orchestrator_common import (
    append_jsonl,
    append_progress_log,
    ensure_state_root,
    ensure_task_exists,
    load_state,
    parse_key_value_pairs,
    save_state,
    sync_task_to_ledger,
    task_file_map,
    utc_now,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Append one event to a task's events.jsonl.")
    parser.add_argument("task_id", help="Task ID")
    parser.add_argument("event_type", help="Event type")
    parser.add_argument("--state-root", help="Path to orchestrator-state")
    parser.add_argument("--message", help="Human-readable event message")
    parser.add_argument("--reason", help="Reason for the event")
    parser.add_argument("--phase", help="Related phase")
    parser.add_argument("--step-id", help="Related step ID")
    parser.add_argument("--progress-note", help="Optional Chinese progress note to append")
    parser.add_argument(
        "--field",
        action="append",
        default=[],
        help="Additional event fields as key=value",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    state_root = ensure_state_root(args.state_root)
    ensure_task_exists(state_root, args.task_id)

    state = load_state(state_root, args.task_id)
    now = utc_now()
    event = {
        "ts": now,
        "type": args.event_type,
        "task_id": args.task_id,
        "phase": args.phase or state.get("phase"),
        "status": state.get("status"),
        "revision": state.get("revision"),
    }
    if args.message:
        event["message"] = args.message
    if args.reason:
        event["reason"] = args.reason
    if args.step_id:
        event["step_id"] = args.step_id
    event.update(parse_key_value_pairs(args.field))

    paths = task_file_map(state_root, args.task_id)
    append_jsonl(paths["events"], event)

    state["updated_at"] = now
    save_state(state_root, args.task_id, state)
    sync_task_to_ledger(state_root, state)

    if args.progress_note:
        append_progress_log(paths["progress"], args.progress_note, ts=now)

    print(f"Appended event {args.event_type} to {args.task_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
