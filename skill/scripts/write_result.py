#!/usr/bin/env python3
from __future__ import annotations

import argparse

from orchestrator_common import (
    ensure_state_root,
    ensure_task_exists,
    load_state,
    persist_artifact_update,
    render_bullet_block,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Write a structured Chinese result.md document.")
    parser.add_argument("task_id", help="Task ID")
    parser.add_argument("--state-root", help="Path to orchestrator-state")
    parser.add_argument("--summary", required=True, help="Chinese completion summary")
    parser.add_argument("--completed", action="append", default=[], help="Repeatable completed item")
    parser.add_argument("--output", action="append", default=[], help="Repeatable output item")
    parser.add_argument("--issue", action="append", default=[], help="Repeatable open issue")
    parser.add_argument("--next-action", action="append", default=[], help="Repeatable next action")
    parser.add_argument("--phase", default="completed", help="Phase to store in state.json")
    parser.add_argument("--status", default="completed", help="Status to store in state.json")
    parser.add_argument("--revision", type=int, help="Optional revision override")
    parser.add_argument("--progress-note", default="已更新结果文档。", help="Chinese progress log note")
    parser.add_argument("--event-type", default="result_structured_written", help="Event type")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    state_root = ensure_state_root(args.state_root)
    ensure_task_exists(state_root, args.task_id)
    state = load_state(state_root, args.task_id)
    state["phase"] = args.phase
    if args.status:
        state["status"] = args.status
    if args.revision is not None:
        state["revision"] = args.revision

    content = (
        f"# 任务 {args.task_id} 结果\n\n"
        "## 完成情况\n\n"
        f"{args.summary.strip()}\n\n"
        "## 已完成内容\n\n"
        f"{render_bullet_block(args.completed, fallback='- 待补充。')}\n\n"
        "## 产出物\n\n"
        f"{render_bullet_block(args.output, fallback='- 暂无额外产出物。')}\n\n"
        "## 遗留问题\n\n"
        f"{render_bullet_block(args.issue, fallback='- 无遗留问题。')}\n\n"
        "## 后续建议\n\n"
        f"{render_bullet_block(args.next_action, fallback='- 无后续建议。')}\n"
    )

    persist_artifact_update(
        state_root,
        args.task_id,
        state=state,
        artifact="result",
        content=content,
        event_type=args.event_type,
        progress_note=args.progress_note,
    )
    print(f"Wrote structured result for {args.task_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
