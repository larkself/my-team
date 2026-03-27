#!/usr/bin/env python3
"""Read chat logs, save extracted knowledge to MEMORY.md, and optionally clear/archive history."""
from __future__ import annotations

import argparse
import shutil
from pathlib import Path

from orchestrator_common import (
    append_workspace_memory_entries,
    append_workspace_session_note,
    ensure_workspace_scaffold,
    local_date_str,
    resolve_state_root,
    resolve_workspace_root,
    utc_now,
    write_text,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Extract knowledge from ai-chat logs into MEMORY.md, then optionally clear or archive the logs.",
    )
    parser.add_argument("--workspace", help="Workspace root (default: .my-team)")
    parser.add_argument("--state-root", help="Optional orchestrator-state path (used to infer workspace root)")

    group = parser.add_argument_group("knowledge entries")
    group.add_argument("--fact", action="append", default=[], help="Repeatable fact entry")
    group.add_argument("--decision", action="append", default=[], help="Repeatable decision entry")
    group.add_argument("--preference", action="append", default=[], help="Repeatable preference entry")
    group.add_argument("--constraint", action="append", default=[], help="Repeatable constraint entry")

    action = parser.add_argument_group("log actions")
    action.add_argument("--dump", action="store_true", help="Dump all chat logs to stdout")
    action.add_argument("--list", action="store_true", dest="list_logs", help="List chat log files and sizes")
    action.add_argument("--clear", action="store_true", help="Remove chat log files after saving knowledge")
    action.add_argument("--archive", action="store_true", help="Move logs to ai-chat/archive/ instead of deleting")
    action.add_argument("--dry-run", action="store_true", help="Show what would be cleared without acting")
    return parser


def chat_log_files(workspace: Path) -> list[Path]:
    """Return sorted list of .md files directly under ai-chat/."""
    ai_chat_dir = workspace / "ai-chat"
    if not ai_chat_dir.is_dir():
        return []
    return sorted(p for p in ai_chat_dir.iterdir() if p.suffix == ".md" and p.is_file())


def list_logs(workspace: Path) -> str:
    """Return a summary of chat log files."""
    files = chat_log_files(workspace)
    if not files:
        return "No chat logs found."
    lines = []
    total_bytes = 0
    for f in files:
        size = f.stat().st_size
        total_bytes += size
        lines.append(f"  {f.name}  ({size} bytes)")
    lines.append(f"  Total: {len(files)} file(s), {total_bytes} bytes")
    return "\n".join(lines)


def dump_logs(workspace: Path) -> str:
    """Return concatenated content of all chat logs."""
    files = chat_log_files(workspace)
    if not files:
        return ""
    parts = []
    for f in files:
        parts.append(f.read_text(encoding="utf-8"))
    return "\n".join(parts)


def archive_logs(workspace: Path, *, dry_run: bool = False) -> list[str]:
    """Move log files into ai-chat/archive/<date>/. Return list of moved paths."""
    files = chat_log_files(workspace)
    if not files:
        return []
    archive_dir = workspace / "ai-chat" / "archive" / local_date_str()
    moved: list[str] = []
    for f in files:
        dest = archive_dir / f.name
        if dry_run:
            moved.append(f"[dry-run] {f.name} -> {dest}")
        else:
            archive_dir.mkdir(parents=True, exist_ok=True)
            shutil.move(str(f), str(dest))
            moved.append(f"{f.name} -> {dest}")
    return moved


def clear_logs(workspace: Path, *, dry_run: bool = False) -> list[str]:
    """Delete log files. Return list of removed files."""
    files = chat_log_files(workspace)
    removed: list[str] = []
    for f in files:
        if dry_run:
            removed.append(f"[dry-run] would remove {f.name}")
        else:
            f.unlink()
            removed.append(f"removed {f.name}")
    return removed


def main() -> int:
    args = build_parser().parse_args()
    state_root = resolve_state_root(args.state_root) if args.state_root else None
    workspace = resolve_workspace_root(args.workspace, state_root=state_root)
    ensure_workspace_scaffold(workspace)

    # --list: show available log files
    if args.list_logs:
        print(list_logs(workspace))
        return 0

    # --dump: output all log content to stdout
    if args.dump:
        content = dump_logs(workspace)
        if content:
            print(content)
        else:
            print("No chat logs found.")
        return 0

    # Collect knowledge entries
    entries: list[tuple[str, str]] = []
    entries.extend(("fact", item) for item in args.fact)
    entries.extend(("decision", item) for item in args.decision)
    entries.extend(("preference", item) for item in args.preference)
    entries.extend(("constraint", item) for item in args.constraint)

    has_entries = bool(entries)
    has_cleanup = args.clear or args.archive

    if not has_entries and not has_cleanup:
        raise SystemExit("Provide knowledge entries (--fact/--decision/--preference/--constraint) and/or --clear/--archive. Use --list or --dump to inspect logs first.")

    # Save knowledge entries to MEMORY.md
    if has_entries:
        append_workspace_memory_entries(workspace, entries, source="extract_knowledge.py (from chat logs)")
        print(f"Saved {len(entries)} knowledge entry(ies) to {workspace / 'MEMORY.md'}")

    # Archive or clear
    actions: list[str] = []
    if args.archive:
        actions = archive_logs(workspace, dry_run=args.dry_run)
    elif args.clear:
        actions = clear_logs(workspace, dry_run=args.dry_run)

    if actions:
        for a in actions:
            print(a)
        log_count = len(chat_log_files(workspace)) if args.dry_run else 0
        cleanup_mode = "archived" if args.archive else "cleared"
        if not args.dry_run:
            append_workspace_session_note(
                workspace,
                f"chat logs {cleanup_mode}",
                [f"files: {len(actions)}", f"knowledge entries saved: {len(entries)}"],
            )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
