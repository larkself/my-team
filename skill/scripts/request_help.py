#!/usr/bin/env python3
"""Allow a member to request the team leader to spin up a new member for discovered work."""
from __future__ import annotations

import argparse

from orchestrator_common import (
    append_jsonl,
    append_progress_log,
    append_workspace_session_note,
    ensure_state_root,
    ensure_task_exists,
    ensure_workspace_scaffold,
    help_requests_dir,
    resolve_workspace_root,
    task_file_map,
    utc_now,
    write_json,
    write_text,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Member requests help: signal the team leader to assign new member(s) for discovered independent work.",
    )
    parser.add_argument("request_id", help="Stable help-request ID, for example HR-001")
    parser.add_argument("--task-id", required=True, help="Current task the member is working on")
    parser.add_argument("--state-root", help="Path to orchestrator-state")
    parser.add_argument("--workspace", help="Path to the long-lived workspace root")
    parser.add_argument("--requester", required=True, help="Member owner ID making the request, e.g. member-coding-1")
    parser.add_argument("--title", required=True, help="Short title of the discovered work")
    parser.add_argument("--description", required=True, help="Description of the work and why it should be independent")
    parser.add_argument(
        "--suggested-task-type",
        choices=["analysis", "design", "coding", "testing", "review", "docs", "release", "integration"],
        help="Suggested member role type for the new work",
    )
    parser.add_argument("--urgency", choices=["low", "medium", "high"], default="medium", help="Urgency level")
    parser.add_argument("--reason", default="", help="Why this should be handled by a separate member")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    state_root = ensure_state_root(args.state_root)
    workspace_root = resolve_workspace_root(args.workspace, state_root=state_root)
    ensure_workspace_scaffold(workspace_root, state_root=state_root)
    ensure_task_exists(state_root, args.task_id)

    hr_dir = help_requests_dir(state_root)
    hr_path = hr_dir / f"{args.request_id}.json"
    if hr_path.exists():
        raise SystemExit(f"Help request already exists: {hr_path}")

    now = utc_now()
    request_data = {
        "request_id": args.request_id,
        "source_task_id": args.task_id,
        "requester": args.requester,
        "title": args.title,
        "description": args.description,
        "suggested_task_type": args.suggested_task_type,
        "urgency": args.urgency,
        "reason": args.reason,
        "status": "pending",
        "created_at": now,
        "resolved_at": None,
    }

    hr_dir.mkdir(parents=True, exist_ok=True)
    write_json(hr_path, request_data)

    # Also write a human-readable summary in the source task directory
    task_paths = task_file_map(state_root, args.task_id)
    hr_task_dir = task_paths["handoff"].parent / "help-requests"
    hr_task_dir.mkdir(parents=True, exist_ok=True)
    summary_lines = [
        f"# Help Request {args.request_id}",
        "",
        f"- Requester: {args.requester}",
        f"- Source task: {args.task_id}",
        f"- Title: {args.title}",
        f"- Urgency: {args.urgency}",
        f"- Suggested task type: {args.suggested_task_type or 'TBD'}",
        "",
        "## Description",
        "",
        args.description,
        "",
    ]
    if args.reason:
        summary_lines.extend(["## Reason for separate member", "", args.reason, ""])
    write_text(hr_task_dir / f"{args.request_id}.md", "\n".join(summary_lines))

    # Append event to the source task
    append_jsonl(
        task_paths["events"],
        {
            "ts": now,
            "type": "help_requested",
            "task_id": args.task_id,
            "request_id": args.request_id,
            "requester": args.requester,
            "title": args.title,
            "suggested_task_type": args.suggested_task_type,
            "urgency": args.urgency,
        },
    )
    append_progress_log(
        task_paths["progress"],
        f"成员 {args.requester} 发现独立工作项，已提交协助请求 {args.request_id}：{args.title}",
        ts=now,
    )
    append_workspace_session_note(
        workspace_root,
        f"help request {args.request_id} created by {args.requester}",
        [
            f"source_task: {args.task_id}",
            f"title: {args.title}",
            f"urgency: {args.urgency}",
        ],
        ts=now,
    )

    print(f"Help request {args.request_id} created from task {args.task_id} by {args.requester}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
