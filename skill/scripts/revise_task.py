#!/usr/bin/env python3
from __future__ import annotations

import argparse

from orchestrator_common import (
    append_jsonl,
    append_progress_log,
    append_transition_events,
    ensure_state_root,
    ensure_task_exists,
    load_state,
    persist_state_snapshot,
    read_text_source,
    task_file_map,
    utc_now,
    write_text,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Accept a task revision with checkpoint-first workflow.")
    parser.add_argument("task_id", help="Task ID")
    parser.add_argument("--state-root", help="Path to orchestrator-state")
    parser.add_argument("--goal", help="Revised task goal")
    parser.add_argument("--scope", help="Revised task scope")
    parser.add_argument("--priority", help="Revised priority")
    parser.add_argument("--owner-agent-id", help="Revised owner agent ID; may be a canonical member role or a role-matched instance such as member-coding-2")
    parser.add_argument("--parent-task-id", help="Revised parent task ID")
    parser.add_argument(
        "--acceptance-criterion",
        action="append",
        default=None,
        help="Replace acceptance criteria with repeated values",
    )
    parser.add_argument(
        "--dependency",
        action="append",
        default=None,
        help="Replace dependencies with repeated values",
    )
    parser.add_argument("--reenter-phase", default="analysis", help="Phase to re-enter after accepting revision")
    parser.add_argument("--status", default="revising", help="Status to store after accepting revision")
    parser.add_argument(
        "--checkpoint-message",
        default="收到修订请求，已先记录 checkpoint。",
        help="Message for the checkpoint event",
    )
    parser.add_argument("--checkpoint-reason", help="Reason for the revision request")
    parser.add_argument(
        "--checkpoint-progress-note",
        help="Chinese progress note for the pre-revision checkpoint",
    )
    parser.add_argument(
        "--revision-message",
        default="已接受修订并回到重新分析阶段。",
        help="Message for the revision_accepted event",
    )
    parser.add_argument(
        "--progress-note",
        help="Chinese progress note after revision acceptance",
    )
    parser.add_argument("--handoff-body", help="Inline handoff body")
    parser.add_argument("--handoff-file", help="Read handoff body from file")
    parser.add_argument("--handoff-stdin", action="store_true", help="Read handoff body from stdin")
    parser.add_argument("--append-handoff", action="store_true", help="Append to handoff instead of replace")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    state_root = ensure_state_root(args.state_root)
    ensure_task_exists(state_root, args.task_id)

    state = load_state(state_root, args.task_id)
    previous_state = dict(state)
    paths = task_file_map(state_root, args.task_id)
    checkpoint_ts = utc_now()

    append_jsonl(
        paths["events"],
        {
            "ts": checkpoint_ts,
            "type": "checkpoint",
            "task_id": args.task_id,
            "phase": state.get("phase"),
            "status": state.get("status"),
            "revision": state.get("revision"),
            "current_step_id": state.get("current_step_id"),
            "message": args.checkpoint_message,
            "reason": args.checkpoint_reason,
        },
    )
    append_progress_log(
        paths["progress"],
        args.checkpoint_progress_note or args.checkpoint_message,
        ts=checkpoint_ts,
    )

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

    if args.goal:
        state["goal"] = args.goal
    if args.scope:
        state["scope"] = args.scope
    if args.priority:
        state["priority"] = args.priority
    if args.owner_agent_id:
        state["owner_agent_id"] = args.owner_agent_id
    if args.parent_task_id is not None:
        state["parent_task_id"] = args.parent_task_id
    if args.acceptance_criterion is not None:
        state["acceptance_criteria"] = args.acceptance_criterion
    if args.dependency is not None:
        state["dependencies"] = args.dependency

    state["revision"] = int(state.get("revision", 1)) + 1
    state["status"] = args.status
    state["phase"] = args.reenter_phase
    state["current_step_id"] = None

    revision_ts = utc_now()
    persist_state_snapshot(state_root, args.task_id, state)
    append_transition_events(paths["events"], args.task_id, previous_state, state, ts=revision_ts)
    append_jsonl(
        paths["events"],
        {
            "ts": revision_ts,
            "type": "revision_accepted",
            "task_id": args.task_id,
            "from_revision": previous_state.get("revision"),
            "to_revision": state.get("revision"),
            "phase": state.get("phase"),
            "status": state.get("status"),
            "message": args.revision_message,
            "reason": args.checkpoint_reason,
        },
    )
    append_progress_log(
        paths["progress"],
        args.progress_note or f"已接受修订，revision 升至 {state['revision']}，重新进入 {state['phase']} 阶段。",
        ts=revision_ts,
    )

    print(f"Accepted revision for {args.task_id}, now at revision {state['revision']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
