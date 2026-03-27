#!/usr/bin/env python3
from __future__ import annotations

import argparse

from orchestrator_common import (
    append_jsonl,
    append_progress_log,
    append_workspace_session_note,
    discussion_file_map,
    ensure_discussion_exists,
    ensure_state_root,
    ensure_workspace_scaffold,
    load_discussion_state,
    persist_discussion_snapshot,
    read_text_source,
    resolve_workspace_root,
    task_file_map,
    utc_now,
    write_text,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Resolve a member-to-member discussion with a recorded decision.")
    parser.add_argument("discussion_id", help="Discussion ID")
    parser.add_argument("--state-root", help="Path to orchestrator-state")
    parser.add_argument("--workspace", help="Path to the long-lived workspace root")
    parser.add_argument("--resolver", required=True, help="Participant or team leader that resolves the discussion")
    parser.add_argument("--summary", required=True, help="Short resolution summary")
    parser.add_argument("--decision-body", help="Inline detailed decision body")
    parser.add_argument("--decision-file", help="Read detailed decision body from file")
    parser.add_argument("--decision-stdin", action="store_true", help="Read detailed decision body from stdin")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    state_root = ensure_state_root(args.state_root)
    workspace_root = resolve_workspace_root(args.workspace, state_root=state_root)
    ensure_workspace_scaffold(workspace_root, state_root=state_root)
    ensure_discussion_exists(state_root, args.discussion_id)

    state = load_discussion_state(state_root, args.discussion_id)
    participants = list(state.get("participants") or [])
    if args.resolver not in participants and args.resolver not in {"main", "leader"}:
        raise SystemExit(f"Resolver {args.resolver} is not a participant or team leader for discussion {args.discussion_id}")

    now = utc_now()
    resolver_label = "team leader" if args.resolver in {"main", "leader"} else args.resolver
    detailed_body = None
    if any([args.decision_body is not None, args.decision_file is not None, args.decision_stdin]):
        detailed_body = read_text_source(
            body=args.decision_body,
            body_file=args.decision_file,
            use_stdin=args.decision_stdin,
        ).rstrip()

    decision_text = (
        detailed_body
        if detailed_body is not None
        else (
            f"# Discussion {args.discussion_id} Decision\n\n"
            f"- Resolver: {resolver_label}\n"
            f"- Summary: {args.summary}\n"
            f"- Linked tasks: {', '.join(state.get('linked_task_ids') or []) or 'none'}\n"
        )
    )
    write_text(discussion_file_map(state_root, args.discussion_id)["decision"], decision_text.rstrip() + "\n")
    append_jsonl(
        discussion_file_map(state_root, args.discussion_id)["messages"],
        {
            "ts": now,
            "type": "discussion_resolved",
            "discussion_id": args.discussion_id,
            "sender": resolver_label,
            "kind": "decision",
            "body": args.summary,
        },
    )

    state["status"] = "resolved"
    state["resolution_summary"] = args.summary
    state["resolved_at"] = now
    state["last_message_at"] = now
    persist_discussion_snapshot(state_root, args.discussion_id, state)

    for task_id in state.get("linked_task_ids") or []:
        append_jsonl(
            task_file_map(state_root, task_id)["events"],
            {
                "ts": now,
                "type": "discussion_resolved",
                "task_id": task_id,
                "discussion_id": args.discussion_id,
                "summary": args.summary,
                "resolver": resolver_label,
            },
        )
        append_progress_log(
            task_file_map(state_root, task_id)["progress"],
            f"成员讨论 {args.discussion_id} 已收敛：{args.summary}",
            ts=now,
        )

    append_workspace_session_note(
        workspace_root,
        f"discussion {args.discussion_id} resolved",
        [
            f"resolver: {resolver_label}",
            f"summary: {args.summary}",
        ],
        ts=now,
    )

    print(f"Resolved discussion {args.discussion_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
