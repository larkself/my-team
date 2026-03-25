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
    verify_task_integrity,
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
    parser.add_argument(
        "--repair",
        action="store_true",
        help="Repair an existing task whose scaffold is incomplete (ledger entry exists but files are missing)",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    state_root = ensure_state_root(args.state_root)
    task_path = task_dir(state_root, args.task_id)

    repairing = False
    if task_path.exists():
        if not args.repair:
            missing = verify_task_integrity(state_root, args.task_id)
            if missing:
                raise SystemExit(
                    f"Task {args.task_id} exists but is incomplete (missing: {', '.join(missing)}). "
                    f"Re-run with --repair to fix it."
                )
            raise SystemExit(f"Task already exists: {task_path}")
        repairing = True

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

    # If repairing, preserve created_at from existing state.json when available.
    if repairing:
        existing_state_path = task_file_map(state_root, args.task_id)["state"]
        if existing_state_path.exists():
            import json
            existing = json.loads(existing_state_path.read_text(encoding="utf-8"))
            if existing.get("created_at"):
                state["created_at"] = existing["created_at"]

    # ensure_task_scaffold is idempotent — only creates files that don't exist.
    paths = ensure_task_scaffold(state_root, state)
    persist_state_snapshot(state_root, args.task_id, state)
    write_json(paths["steps"], {"task_id": args.task_id, "updated_at": now, "steps": []})

    event_type = "task_repaired" if repairing else "task_received"
    append_jsonl(
        task_file_map(state_root, args.task_id)["events"],
        {
            "ts": now,
            "type": event_type,
            "task_id": args.task_id,
            "goal": args.goal,
            "phase": args.phase,
            "status": args.status,
        },
    )
    log_msg = f"任务已修复，当前阶段为 {args.phase}。" if repairing else f"任务已创建，当前阶段为 {args.phase}。"
    append_progress_log(paths["progress"], log_msg, ts=now)

    verb = "Repaired" if repairing else "Initialized"
    print(f"{verb} task {args.task_id} at {task_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
