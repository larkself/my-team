#!/usr/bin/env python3
from __future__ import annotations

import argparse

from orchestrator_common import (
    append_jsonl,
    append_workspace_session_note,
    discussion_file_map,
    ensure_discussion_exists,
    ensure_state_root,
    ensure_workspace_scaffold,
    load_discussion_state,
    persist_discussion_snapshot,
    read_text_source,
    resolve_workspace_root,
    utc_now,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Append one member-to-member discussion message.")
    parser.add_argument("discussion_id", help="Discussion ID")
    parser.add_argument("--state-root", help="Path to orchestrator-state")
    parser.add_argument("--workspace", help="Path to the long-lived workspace root")
    parser.add_argument("--sender", required=True, help="Member owner ID that sends the message")
    parser.add_argument("--to", action="append", default=[], help="Optional repeatable receiver member owner ID")
    parser.add_argument(
        "--kind",
        choices=["question", "answer", "proposal", "note"],
        default="note",
        help="Message kind",
    )
    parser.add_argument("--body", help="Inline message body")
    parser.add_argument("--body-file", help="Read message body from file")
    parser.add_argument("--stdin", action="store_true", help="Read message body from stdin")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    state_root = ensure_state_root(args.state_root)
    workspace_root = resolve_workspace_root(args.workspace, state_root=state_root)
    ensure_workspace_scaffold(workspace_root, state_root=state_root)
    ensure_discussion_exists(state_root, args.discussion_id)

    state = load_discussion_state(state_root, args.discussion_id)
    if state.get("status") != "open":
        raise SystemExit(f"Discussion {args.discussion_id} is not open: {state.get('status')}")

    participants = list(state.get("participants") or [])
    if args.sender not in participants:
        raise SystemExit(f"Sender {args.sender} is not a participant of discussion {args.discussion_id}")
    for receiver in args.to:
        if receiver not in participants:
            raise SystemExit(f"Receiver {receiver} is not a participant of discussion {args.discussion_id}")

    body = read_text_source(body=args.body, body_file=args.body_file, use_stdin=args.stdin).rstrip()
    now = utc_now()
    append_jsonl(
        discussion_file_map(state_root, args.discussion_id)["messages"],
        {
            "ts": now,
            "type": "discussion_message",
            "discussion_id": args.discussion_id,
            "sender": args.sender,
            "to": args.to,
            "kind": args.kind,
            "body": body,
        },
    )
    state["last_message_at"] = now
    persist_discussion_snapshot(state_root, args.discussion_id, state)
    append_workspace_session_note(
        workspace_root,
        f"discussion {args.discussion_id} message",
        [
            f"sender: {args.sender}",
            f"kind: {args.kind}",
            f"to: {', '.join(args.to) or 'all participants'}",
        ],
        ts=now,
    )
    print(f"Posted {args.kind} message to discussion {args.discussion_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
