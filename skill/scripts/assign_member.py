#!/usr/bin/env python3
from __future__ import annotations

import argparse

from orchestrator_common import (
    append_jsonl,
    append_progress_log,
    append_transition_events,
    canonical_member_role_name,
    ensure_state_root,
    ensure_task_exists,
    load_state,
    persist_state_snapshot,
    STANDARD_MEMBER_TASK_TYPE_CHOICES,
    task_file_map,
    utc_now,
    validate_state_payload,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Assign a standardized member role to a task.")
    parser.add_argument("task_id", nargs="?", help="Optional task ID to update")
    parser.add_argument(
        "--task-type",
        required=True,
        choices=STANDARD_MEMBER_TASK_TYPE_CHOICES,
        help="Member task type used to derive the canonical role name",
    )
    parser.add_argument("--state-root", help="Path to orchestrator-state")
    parser.add_argument(
        "--owner-agent-id",
        help="Optional concrete member instance, for example member-coding-2. Defaults to the canonical role name.",
    )
    parser.add_argument("--progress-note", help="Optional progress log note")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    member_role_name = canonical_member_role_name(args.task_type)
    owner_agent_id = args.owner_agent_id or member_role_name
    validate_state_payload(
        {
            "task_type": args.task_type,
            "member_role_name": member_role_name,
            "owner_agent_id": owner_agent_id,
        }
    )

    if not args.task_id:
        print(owner_agent_id)
        return 0

    state_root = ensure_state_root(args.state_root)
    ensure_task_exists(state_root, args.task_id)

    state = load_state(state_root, args.task_id)
    previous_state = dict(state)
    state["task_type"] = args.task_type
    state["member_role_name"] = member_role_name
    state["owner_agent_id"] = owner_agent_id

    now = utc_now()
    paths = task_file_map(state_root, args.task_id)
    persist_state_snapshot(state_root, args.task_id, state)
    append_transition_events(paths["events"], args.task_id, previous_state, state, ts=now)
    append_jsonl(
        paths["events"],
        {
            "ts": now,
            "type": "member_assigned",
            "task_id": args.task_id,
            "task_type": args.task_type,
            "member_role_name": member_role_name,
            "owner_agent_id": owner_agent_id,
        },
    )
    append_progress_log(
        paths["progress"],
        args.progress_note
        or (
            f"成员已分配为 {member_role_name}。"
            if owner_agent_id == member_role_name
            else f"成员角色为 {member_role_name}，实例负责人为 {owner_agent_id}。"
        ),
        ts=now,
    )

    print(owner_agent_id)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
