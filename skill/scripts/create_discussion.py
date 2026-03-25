#!/usr/bin/env python3
from __future__ import annotations

import argparse

from orchestrator_common import (
    append_jsonl,
    append_progress_log,
    append_workspace_session_note,
    discussion_dir,
    discussion_file_map,
    ensure_discussion_scaffold,
    ensure_state_root,
    ensure_task_exists,
    ensure_workspace_scaffold,
    persist_discussion_snapshot,
    resolve_workspace_root,
    task_file_map,
    utc_now,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Create a member-to-member discussion artifact.")
    parser.add_argument("discussion_id", help="Stable discussion ID, for example D-001")
    parser.add_argument("--state-root", help="Path to orchestrator-state")
    parser.add_argument("--workspace", help="Path to the long-lived workspace root")
    parser.add_argument("--mode", choices=["consult", "sync"], default="consult", help="Discussion mode")
    parser.add_argument("--title", required=True, help="Short discussion topic")
    parser.add_argument("--context", default="", help="Optional context for the discussion")
    parser.add_argument("--initiator", required=True, help="Member owner ID that starts the discussion")
    parser.add_argument(
        "--participant",
        action="append",
        default=[],
        help="Repeatable member owner ID for discussion participants",
    )
    parser.add_argument(
        "--task-id",
        action="append",
        default=[],
        help="Repeatable linked task ID",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    state_root = ensure_state_root(args.state_root)
    workspace_root = resolve_workspace_root(args.workspace, state_root=state_root)
    ensure_workspace_scaffold(workspace_root, state_root=state_root)

    discussion_path = discussion_dir(state_root, args.discussion_id)
    if discussion_path.exists():
        raise SystemExit(f"Discussion already exists: {discussion_path}")

    for task_id in args.task_id:
        ensure_task_exists(state_root, task_id)

    now = utc_now()
    state = {
        "discussion_id": args.discussion_id,
        "mode": args.mode,
        "status": "open",
        "title": args.title,
        "context": args.context,
        "initiator": args.initiator,
        "participants": [args.initiator, *args.participant],
        "linked_task_ids": args.task_id,
        "resolution_summary": "",
        "created_at": now,
        "updated_at": now,
        "last_message_at": now,
        "resolved_at": None,
    }

    paths = ensure_discussion_scaffold(state_root, state)
    persist_discussion_snapshot(state_root, args.discussion_id, state)
    append_jsonl(
        paths["messages"],
        {
            "ts": now,
            "type": "discussion_started",
            "discussion_id": args.discussion_id,
            "mode": args.mode,
            "sender": args.initiator,
            "participants": state["participants"],
            "linked_task_ids": args.task_id,
            "title": args.title,
            "body": args.context or args.title,
        },
    )

    for task_id in args.task_id:
        append_jsonl(
            task_file_map(state_root, task_id)["events"],
            {
                "ts": now,
                "type": "discussion_started",
                "task_id": task_id,
                "discussion_id": args.discussion_id,
                "discussion_mode": args.mode,
                "participants": state["participants"],
                "title": args.title,
            },
        )
        append_progress_log(
            task_file_map(state_root, task_id)["progress"],
            f"成员讨论 {args.discussion_id} 已启动：{args.title}。",
            ts=now,
        )

    append_workspace_session_note(
        workspace_root,
        f"discussion {args.discussion_id} opened",
        [
            f"mode: {args.mode}",
            f"initiator: {args.initiator}",
            f"participants: {', '.join(state['participants'])}",
            f"tasks: {', '.join(args.task_id) or 'none'}",
            f"title: {args.title}",
        ],
        ts=now,
    )

    print(f"Created discussion {args.discussion_id} with participants {', '.join(state['participants'])}")
    print(f"Discussion artifacts: {discussion_file_map(state_root, args.discussion_id)['state'].parent}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
