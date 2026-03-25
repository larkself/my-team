#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from orchestrator_common import (
    append_workspace_session_note,
    ensure_workspace_scaffold,
    local_date_str,
    local_time_str,
    read_text_source,
    resolve_workspace_root,
    write_text,
)

ROLE_LABELS = {
    "user": "用户",
    "assistant": "主Agent",
    "main-agent": "主Agent",
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Append one main-agent chat turn to ai-chat/YYYY-MM-DD.md in the workspace.",
    )
    parser.add_argument("role", choices=sorted(ROLE_LABELS.keys()), help="Chat role")
    parser.add_argument("--workspace", help="Workspace root. Defaults to current working directory")
    parser.add_argument("--message", help="Inline message")
    parser.add_argument("--message-file", help="Read message from file")
    parser.add_argument("--stdin", action="store_true", help="Read message from stdin")
    parser.add_argument("--date", help="Override the filename date as YYYY-MM-DD")
    parser.add_argument("--time-label", help="Override the entry time label")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    workspace = resolve_workspace_root(args.workspace)
    ensure_workspace_scaffold(workspace)
    ai_chat_dir = workspace / "ai-chat"

    date_str = args.date or local_date_str()
    time_label = args.time_label or local_time_str()
    message = read_text_source(body=args.message, body_file=args.message_file, use_stdin=args.stdin).rstrip()

    log_path = ai_chat_dir / f"{date_str}.md"
    heading = f"# {date_str} 聊天记录\n"
    entry = f"\n## {time_label} {ROLE_LABELS[args.role]}\n\n{message}\n"

    if log_path.exists():
        existing = log_path.read_text(encoding="utf-8").rstrip()
        content = f"{existing}{entry}\n"
    else:
        content = f"{heading}{entry}\n"

    write_text(log_path, content)
    append_workspace_session_note(
        workspace,
        f"{args.role} chat turn logged",
        [
            f"ai-chat entry: {log_path.name}",
            f"excerpt: {message[:160].replace(chr(10), ' ')}",
        ],
    )
    print(f"Logged {args.role} chat turn to {log_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
