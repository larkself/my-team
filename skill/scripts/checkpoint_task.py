#!/usr/bin/env python3
from __future__ import annotations

import argparse

from orchestrator_common import (
    append_jsonl,
    append_transition_events,
    append_progress_log,
    append_workspace_memory_entries,
    append_workspace_session_note,
    ensure_state_root,
    ensure_task_exists,
    ensure_workspace_scaffold,
    load_state,
    persist_state_snapshot,
    read_text_source,
    resolve_workspace_root,
    task_file_map,
    utc_now,
    write_text,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Checkpoint task state and optional handoff note.")
    parser.add_argument("task_id", help="Task ID")
    parser.add_argument("--state-root", help="Path to orchestrator-state")
    parser.add_argument("--workspace", help="Path to the long-lived workspace root")
    parser.add_argument("--phase", help="New phase")
    parser.add_argument("--status", help="New status")
    parser.add_argument("--current-step-id", help="Current step ID")
    parser.add_argument("--revision", type=int, help="Set revision to an exact value")
    parser.add_argument("--bump-revision", action="store_true", help="Increment revision by one")
    parser.add_argument("--event-type", default="checkpoint", help="Event type to append")
    parser.add_argument("--message", help="Checkpoint message")
    parser.add_argument("--reason", help="Checkpoint reason")
    parser.add_argument("--progress-note", help="Chinese progress log note")
    parser.add_argument("--handoff-body", help="Inline handoff body")
    parser.add_argument("--handoff-file", help="Read handoff body from file")
    parser.add_argument("--handoff-stdin", action="store_true", help="Read handoff body from stdin")
    parser.add_argument("--append-handoff", action="store_true", help="Append to handoff instead of replace")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    state_root = ensure_state_root(args.state_root)
    workspace_root = resolve_workspace_root(args.workspace, state_root=state_root)
    ensure_workspace_scaffold(workspace_root, state_root=state_root)
    ensure_task_exists(state_root, args.task_id)

    state = load_state(state_root, args.task_id)
    previous_state = dict(state)
    paths = task_file_map(state_root, args.task_id)
    now = utc_now()

    if args.phase:
        state["phase"] = args.phase
    if args.status:
        state["status"] = args.status
    if args.current_step_id is not None:
        state["current_step_id"] = args.current_step_id
    if args.revision is not None:
        state["revision"] = args.revision
    elif args.bump_revision:
        state["revision"] = int(state.get("revision", 1)) + 1

    handoff_supplied = any([args.handoff_body is not None, args.handoff_file is not None, args.handoff_stdin])
    if handoff_supplied:
        handoff_text = read_text_source(
            body=args.handoff_body,
            body_file=args.handoff_file,
            use_stdin=args.handoff_stdin,
        ).rstrip()
        if args.append_handoff and paths["handoff"].exists():
            existing = paths["handoff"].read_text(encoding="utf-8").rstrip()
            merged = f"{existing}\n\n{handoff_text}\n"
        else:
            merged = f"{handoff_text}\n"
        write_text(paths["handoff"], merged)

    persist_state_snapshot(state_root, args.task_id, state)
    append_transition_events(paths["events"], args.task_id, previous_state, state, ts=now)
    append_workspace_memory_entries(
        workspace_root,
        [
            ("decision", f"checkpoint_task.py updated {args.task_id} to phase {state.get('phase')} and status {state.get('status')}"),
        ],
        source="checkpoint_task.py",
        ts=now,
    )
    append_workspace_session_note(
        workspace_root,
        f"checkpoint recorded for {args.task_id}",
        [
            f"phase: {state.get('phase')}",
            f"status: {state.get('status')}",
            f"revision: {state.get('revision')}",
            f"current_step_id: {state.get('current_step_id') or 'none'}",
        ],
        ts=now,
    )

    event = {
        "ts": now,
        "type": args.event_type,
        "task_id": args.task_id,
        "phase": state.get("phase"),
        "status": state.get("status"),
        "revision": state.get("revision"),
        "current_step_id": state.get("current_step_id"),
    }
    if args.message:
        event["message"] = args.message
    if args.reason:
        event["reason"] = args.reason
    append_jsonl(paths["events"], event)

    if args.progress_note:
        append_progress_log(paths["progress"], args.progress_note, ts=now)

    print(f"Checkpointed task {args.task_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
