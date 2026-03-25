#!/usr/bin/env python3
from __future__ import annotations

import argparse

from orchestrator_common import (
    append_jsonl,
    append_transition_events,
    append_progress_log,
    default_artifact_title,
    ensure_state_root,
    ensure_task_exists,
    load_state,
    persist_state_snapshot,
    read_text_source,
    task_file_map,
    utc_now,
    write_text,
)

ARTIFACT_CHOICES = ["task", "analysis", "design", "plan", "result", "brief", "handoff"]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Write or append a task artifact markdown file.")
    parser.add_argument("task_id", help="Task ID")
    parser.add_argument("artifact", choices=ARTIFACT_CHOICES, help="Artifact name")
    parser.add_argument("--state-root", help="Path to orchestrator-state")
    parser.add_argument("--body", help="Inline body text")
    parser.add_argument("--body-file", help="Read body text from file")
    parser.add_argument("--stdin", action="store_true", help="Read body text from stdin")
    parser.add_argument("--title", help="Optional markdown title line")
    parser.add_argument("--append", action="store_true", help="Append instead of replace")
    parser.add_argument("--phase", help="Optional phase update")
    parser.add_argument("--status", help="Optional status update")
    parser.add_argument("--revision", type=int, help="Optional revision override")
    parser.add_argument("--event-type", default="artifact_written", help="Event type to append")
    parser.add_argument("--progress-note", help="Optional Chinese progress note")
    return parser


def build_content(task_id: str, artifact: str, body: str, title: str | None, append: bool, existing: str) -> str:
    payload = body.rstrip()
    if append:
        separator = "" if existing.endswith("\n") or existing == "" else "\n"
        return f"{existing}{separator}{payload}\n"
    if title:
        return f"{title.rstrip()}\n\n{payload}\n"
    if payload.lstrip().startswith("# "):
        return f"{payload}\n"
    return f"{default_artifact_title(task_id, artifact)}\n\n{payload}\n"


def main() -> int:
    args = build_parser().parse_args()
    state_root = ensure_state_root(args.state_root)
    ensure_task_exists(state_root, args.task_id)
    state = load_state(state_root, args.task_id)
    previous_state = dict(state)
    paths = task_file_map(state_root, args.task_id)
    now = utc_now()

    body = read_text_source(body=args.body, body_file=args.body_file, use_stdin=args.stdin)
    target = paths[args.artifact]
    existing = target.read_text(encoding="utf-8") if target.exists() else ""
    content = build_content(args.task_id, args.artifact, body, args.title, args.append, existing)
    write_text(target, content)

    if args.phase:
        state["phase"] = args.phase
    if args.status:
        state["status"] = args.status
    if args.revision is not None:
        state["revision"] = args.revision
    persist_state_snapshot(
        state_root,
        args.task_id,
        state,
        sync_task_doc=args.artifact != "task",
    )
    append_transition_events(paths["events"], args.task_id, previous_state, state, ts=now)

    append_jsonl(
        paths["events"],
        {
            "ts": now,
            "type": args.event_type,
            "task_id": args.task_id,
            "artifact": args.artifact,
            "phase": state.get("phase"),
            "status": state.get("status"),
            "revision": state.get("revision"),
        },
    )
    if args.progress_note:
        append_progress_log(paths["progress"], args.progress_note, ts=now)

    print(f"Wrote {args.artifact} for {args.task_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
