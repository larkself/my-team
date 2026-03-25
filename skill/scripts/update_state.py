#!/usr/bin/env python3
from __future__ import annotations

import argparse

from orchestrator_common import (
    append_jsonl,
    append_transition_events,
    append_progress_log,
    ensure_state_root,
    ensure_task_exists,
    load_state,
    STANDARD_MEMBER_TASK_TYPE_CHOICES,
    parse_key_value_pairs,
    persist_state_snapshot,
    task_file_map,
    utc_now,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Update task state.json and ledger.json.")
    parser.add_argument("task_id", help="Task ID")
    parser.add_argument("--state-root", help="Path to orchestrator-state")
    parser.add_argument("--status", help="New task status")
    parser.add_argument("--phase", help="New task phase")
    parser.add_argument("--revision", type=int, help="New revision number")
    parser.add_argument("--goal", help="New task goal")
    parser.add_argument("--scope", help="New task scope")
    parser.add_argument("--priority", help="New task priority")
    parser.add_argument("--owner-agent-id", help="New owner agent ID")
    parser.add_argument(
        "--task-type",
        choices=STANDARD_MEMBER_TASK_TYPE_CHOICES,
        help="Optional member task type; member_role_name is normalized to the canonical role and owner_agent_id may be that role or a role-matched instance",
    )
    parser.add_argument("--parent-task-id", help="Parent task ID")
    parser.add_argument("--current-step-id", help="Current step ID")
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
    parser.add_argument(
        "--field",
        action="append",
        default=[],
        help="Additional key=value updates applied to state.json",
    )
    parser.add_argument("--event-type", help="Optional event type to append")
    parser.add_argument("--event-message", help="Optional event message")
    parser.add_argument("--progress-note", help="Optional Chinese progress log note")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    state_root = ensure_state_root(args.state_root)
    ensure_task_exists(state_root, args.task_id)

    state = load_state(state_root, args.task_id)
    previous_state = dict(state)
    if args.status:
        state["status"] = args.status
    if args.phase:
        state["phase"] = args.phase
    if args.revision is not None:
        state["revision"] = args.revision
    if args.goal:
        state["goal"] = args.goal
    if args.scope:
        state["scope"] = args.scope
    if args.priority:
        state["priority"] = args.priority
    if args.owner_agent_id:
        state["owner_agent_id"] = args.owner_agent_id
    if args.task_type:
        state["task_type"] = args.task_type
    if args.parent_task_id:
        state["parent_task_id"] = args.parent_task_id
    if args.current_step_id is not None:
        state["current_step_id"] = args.current_step_id
    if args.acceptance_criterion is not None:
        state["acceptance_criteria"] = args.acceptance_criterion
    if args.dependency is not None:
        state["dependencies"] = args.dependency

    extra_fields = parse_key_value_pairs(args.field)
    state.update(extra_fields)

    paths = task_file_map(state_root, args.task_id)
    now = utc_now()
    persist_state_snapshot(state_root, args.task_id, state)
    append_transition_events(paths["events"], args.task_id, previous_state, state, ts=now)
    if args.event_type:
        event = {
            "ts": now,
            "type": args.event_type,
            "task_id": args.task_id,
            "phase": state.get("phase"),
            "status": state.get("status"),
        }
        if args.event_message:
            event["message"] = args.event_message
        append_jsonl(paths["events"], event)
    if args.progress_note:
        append_progress_log(paths["progress"], args.progress_note, ts=now)

    print(f"Updated state for {args.task_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
