#!/usr/bin/env python3
from __future__ import annotations

import argparse

from orchestrator_common import (
    append_jsonl,
    append_progress_log,
    append_workspace_session_note,
    canonical_member_role_name,
    ensure_state_root,
    ensure_task_scaffold,
    ensure_workspace_scaffold,
    persist_state_snapshot,
    STANDARD_MEMBER_TASK_TYPE_CHOICES,
    resolve_workspace_root,
    task_dir,
    task_file_map,
    utc_now,
    write_json,
    write_text,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Create a standardized subtask with parent linkage and member assignment.")
    parser.add_argument("task_id", help="Stable task ID, for example T-001")
    parser.add_argument("--state-root", help="Path to orchestrator-state")
    parser.add_argument("--workspace", help="Path to the long-lived workspace root")
    parser.add_argument("--goal", required=True, help="Task goal")
    parser.add_argument("--parent-task-id", required=True, help="Parent task ID")
    parser.add_argument("--task-type", required=True, choices=STANDARD_MEMBER_TASK_TYPE_CHOICES, help="Task type used to derive the member role")
    parser.add_argument("--scope", default="待补充", help="Task scope")
    parser.add_argument("--priority", default="medium", help="Task priority")
    parser.add_argument("--status", default="in_progress", help="Task status")
    parser.add_argument("--phase", default="received", help="Task phase")
    parser.add_argument(
        "--owner-agent-id",
        help="Optional concrete member instance, for example member-coding-2. Defaults to the canonical role name.",
    )
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
    parser.add_argument("--progress-note", help="Optional custom progress log note")
    parser.add_argument("--handoff-note", help="Optional custom handoff note")
    return parser


def build_default_handoff(
    task_id: str,
    parent_task_id: str,
    task_type: str,
    member_role_name: str,
    owner_agent_id: str,
) -> str:
    owner_line = (
        f"{owner_agent_id}"
        if owner_agent_id == member_role_name
        else f"{owner_agent_id} (role {member_role_name})"
    )
    return (
        f"# Task {task_id} Handoff\n\n"
        f"- Current checkpoint: subtask created for {owner_line}\n"
        f"- Resume guidance: continue the {task_type} work for parent {parent_task_id}; confirm the latest milestone and next owner before resuming\n"
    )


def main() -> int:
    args = build_parser().parse_args()
    state_root = ensure_state_root(args.state_root)
    workspace_root = resolve_workspace_root(args.workspace, state_root=state_root)
    ensure_workspace_scaffold(workspace_root, state_root=state_root)
    task_path = task_dir(state_root, args.task_id)
    if task_path.exists():
        raise SystemExit(f"Task already exists: {task_path}")

    member_role_name = canonical_member_role_name(args.task_type)
    owner_agent_id = args.owner_agent_id or member_role_name
    now = utc_now()
    state = {
        "task_id": args.task_id,
        "parent_task_id": args.parent_task_id,
        "owner_agent_id": owner_agent_id,
        "task_type": args.task_type,
        "member_role_name": member_role_name,
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
    persist_state_snapshot(
        state_root,
        args.task_id,
        state,
        task_notes=(
            f"子任务已创建，标准成员角色为 {member_role_name}，"
            f"实例负责人为 {owner_agent_id}，父任务为 {args.parent_task_id}。"
        ),
    )
    write_json(paths["steps"], {"task_id": args.task_id, "updated_at": now, "steps": []})

    handoff_text = args.handoff_note or build_default_handoff(
        args.task_id,
        args.parent_task_id,
        args.task_type,
        member_role_name,
        owner_agent_id,
    )
    write_text(paths["handoff"], handoff_text.rstrip() + "\n")
    append_workspace_session_note(
        workspace_root,
        f"subtask {args.task_id} created",
        [
            f"owner: {owner_agent_id}",
            f"role: {member_role_name}",
            f"parent: {args.parent_task_id}",
            f"status: {args.status}",
            f"phase: {args.phase}",
        ],
        ts=now,
    )

    append_jsonl(
        task_file_map(state_root, args.task_id)["events"],
        {
            "ts": now,
            "type": "subtask_created",
            "task_id": args.task_id,
            "parent_task_id": args.parent_task_id,
            "task_type": args.task_type,
            "member_role_name": member_role_name,
            "owner_agent_id": owner_agent_id,
        },
    )
    append_progress_log(
        paths["progress"],
        args.progress_note
        or (
            f"子任务已创建，父任务 {args.parent_task_id}，标准角色 {member_role_name}。"
            if owner_agent_id == member_role_name
            else f"子任务已创建，父任务 {args.parent_task_id}，标准角色 {member_role_name}，实例负责人 {owner_agent_id}。"
        ),
        ts=now,
    )

    print(
        f"Created subtask {args.task_id} under {args.parent_task_id} as {owner_agent_id}"
        + ("" if owner_agent_id == member_role_name else f" (role {member_role_name})")
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
