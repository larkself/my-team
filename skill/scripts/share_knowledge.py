#!/usr/bin/env python3
"""Allow members to share knowledge entries on a shared board that other members can read."""
from __future__ import annotations

import argparse
import json

from orchestrator_common import (
    append_jsonl,
    append_progress_log,
    append_workspace_session_note,
    ensure_state_root,
    ensure_task_exists,
    ensure_workspace_scaffold,
    knowledge_board_dir,
    resolve_workspace_root,
    task_file_map,
    utc_now,
    write_json,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Share knowledge entries on a board that other members can read.",
    )
    parser.add_argument("--state-root", help="Path to orchestrator-state")
    parser.add_argument("--workspace", help="Path to the long-lived workspace root")
    parser.add_argument("--task-id", help="Source task that produced this knowledge")
    parser.add_argument("--author", help="Member owner ID sharing the knowledge, e.g. member-analysis-1")
    parser.add_argument("--topic", help="Short topic / title for the knowledge entry")
    parser.add_argument("--content", help="Knowledge content to share")
    parser.add_argument("--tag", action="append", default=[], help="Repeatable tags for categorization")
    parser.add_argument("--target-task", action="append", default=[], help="Repeatable task IDs this knowledge is relevant to")
    parser.add_argument("--list", dest="list_entries", action="store_true", help="List existing knowledge board entries")
    parser.add_argument("--read", metavar="ENTRY_ID", help="Read a specific knowledge board entry")
    return parser


def list_entries(state_root):
    kb_dir = knowledge_board_dir(state_root)
    if not kb_dir.exists():
        print("Knowledge board is empty.")
        return 0
    entries = sorted(kb_dir.glob("*.json"))
    if not entries:
        print("Knowledge board is empty.")
        return 0
    for entry_path in entries:
        data = json.loads(entry_path.read_text(encoding="utf-8"))
        tags = ", ".join(data.get("tags", [])) or "none"
        print(f"  {data.get('entry_id', entry_path.stem)}  [{tags}]  {data.get('topic', '?')}")
    return 0


def read_entry(state_root, entry_id):
    kb_dir = knowledge_board_dir(state_root)
    entry_path = kb_dir / f"{entry_id}.json"
    if not entry_path.exists():
        raise SystemExit(f"Knowledge entry not found: {entry_path}")
    data = json.loads(entry_path.read_text(encoding="utf-8"))
    print(f"Entry: {data.get('entry_id')}")
    print(f"Topic: {data.get('topic')}")
    print(f"Author: {data.get('author')}")
    print(f"Source task: {data.get('source_task_id')}")
    print(f"Tags: {', '.join(data.get('tags', []))}")
    print(f"Target tasks: {', '.join(data.get('target_task_ids', []))}")
    print(f"Created: {data.get('created_at')}")
    print(f"\n{data.get('content', '')}")
    return 0


def next_entry_id(state_root):
    kb_dir = knowledge_board_dir(state_root)
    if not kb_dir.exists():
        return "KB-001"
    existing = sorted(kb_dir.glob("KB-*.json"))
    if not existing:
        return "KB-001"
    last_num = 0
    for p in existing:
        try:
            num = int(p.stem.split("-", 1)[1])
            if num > last_num:
                last_num = num
        except (ValueError, IndexError):
            pass
    return f"KB-{last_num + 1:03d}"


def main() -> int:
    args = build_parser().parse_args()
    state_root = ensure_state_root(args.state_root)

    if args.list_entries:
        return list_entries(state_root)
    if args.read:
        return read_entry(state_root, args.read)

    # Validate required fields for creating an entry
    missing = [name for name in ("task_id", "author", "topic", "content") if not getattr(args, name)]
    if missing:
        raise SystemExit(f"Missing required arguments for creating an entry: {', '.join('--' + m.replace('_', '-') for m in missing)}")

    workspace_root = resolve_workspace_root(args.workspace, state_root=state_root)
    ensure_workspace_scaffold(workspace_root, state_root=state_root)
    ensure_task_exists(state_root, args.task_id)

    now = utc_now()
    entry_id = next_entry_id(state_root)
    entry_data = {
        "entry_id": entry_id,
        "source_task_id": args.task_id,
        "author": args.author,
        "topic": args.topic,
        "content": args.content,
        "tags": args.tag,
        "target_task_ids": args.target_task,
        "created_at": now,
    }

    kb_dir = knowledge_board_dir(state_root)
    kb_dir.mkdir(parents=True, exist_ok=True)
    write_json(kb_dir / f"{entry_id}.json", entry_data)

    # Append event to the source task
    task_paths = task_file_map(state_root, args.task_id)
    append_jsonl(
        task_paths["events"],
        {
            "ts": now,
            "type": "knowledge_shared",
            "task_id": args.task_id,
            "entry_id": entry_id,
            "author": args.author,
            "topic": args.topic,
            "tags": args.tag,
            "target_task_ids": args.target_task,
        },
    )
    append_progress_log(
        task_paths["progress"],
        f"成员 {args.author} 分享了知识条目 {entry_id}：{args.topic}",
        ts=now,
    )

    # Notify target tasks if specified
    for target_tid in args.target_task:
        target_events = task_file_map(state_root, target_tid)["events"]
        append_jsonl(
            target_events,
            {
                "ts": now,
                "type": "knowledge_received",
                "task_id": target_tid,
                "entry_id": entry_id,
                "from_task_id": args.task_id,
                "author": args.author,
                "topic": args.topic,
            },
        )

    append_workspace_session_note(
        workspace_root,
        f"knowledge {entry_id} shared by {args.author}",
        [
            f"source_task: {args.task_id}",
            f"topic: {args.topic}",
            f"tags: {', '.join(args.tag) or 'none'}",
            f"target_tasks: {', '.join(args.target_task) or 'none'}",
        ],
        ts=now,
    )

    print(f"Knowledge entry {entry_id} shared by {args.author} from task {args.task_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
