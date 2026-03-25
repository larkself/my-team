#!/usr/bin/env python3
from __future__ import annotations

import argparse

from orchestrator_common import (
    append_jsonl,
    append_progress_log,
    ensure_state_root,
    ensure_task_scaffold,
    STANDARD_MEMBER_TASK_TYPE_CHOICES,
    persist_state_snapshot,
    task_dir,
    task_file_map,
    utc_now,
    write_json,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Initialize a task in orchestrator-state.")
    parser.add_argument("task_id", help="Stable task ID, for example T-001")
    parser.add_argument("--state-root", help="Path to orchestrator-state")
    parser.add_argument("--goal", required=True, help="Task goal")
    parser.add_argument("--scope", default="待补充", help="Task scope")
    parser.add_argument("--parent-task-id", help="Optional parent task ID")
    parser.add_argument("--owner-agent-id", default="main", help="Agent responsible for the task")
    parser.add_argument(
        "--task-type",
        choices=STANDARD_MEMBER_TASK_TYPE_CHOICES,
        help="Optional member task type; if set, member_role_name becomes canonical and owner_agent_id may be that role or a role-matched instance",
    )
    parser.add_argument("--priority", default="medium", help="Task priority")
    parser.add_argument("--status", default="in_progress", help="Task status")
    parser.add_argument("--phase", default="received", help="Task phase")
    parser.add_argument(
        "--acceptance-criterion",
        action="append",
        default=[],
        help="Repeatable acceptance criterion",
    )
    parser.add_argument(
        "--dependency",
        action="append",
        default=[],
        help="Repeatable dependency task ID or note",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    state_root = ensure_state_root(args.state_root)
    task_path = task_dir(state_root, args.task_id)
    if task_path.exists():
        raise SystemExit(f"Task already exists: {task_path}")

    now = utc_now()
    state = {
        "task_id": args.task_id,
        "parent_task_id": args.parent_task_id,
        "owner_agent_id": args.owner_agent_id,
        "task_type": args.task_type,
        "member_role_name": None,
        "status": args.status,
        "phase": args.phase,
        "revision": 1,
        "goal": args.goal,
        "scope": args.scope,
        "priority": args.priority,
        "dependencies": args.dependency,
        "acceptance_criteria": args.acceptance_criterion,
        "current_step_id": None,
        "created_at": now,
        "updated_at": now,
    }

    paths = ensure_task_scaffold(state_root, state)
    persist_state_snapshot(state_root, args.task_id, state)
    write_json(paths["steps"], {"task_id": args.task_id, "updated_at": now, "steps": []})

    append_jsonl(
        task_file_map(state_root, args.task_id)["events"],
        {
            "ts": now,
            "type": "task_received",
            "task_id": args.task_id,
            "goal": args.goal,
            "phase": args.phase,
            "status": args.status,
        },
    )
    append_progress_log(paths["progress"], f"任务已创建，当前阶段为 {args.phase}。", ts=now)

    print(f"Initialized task {args.task_id} at {task_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
