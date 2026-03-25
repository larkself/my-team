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
    parser = argparse.ArgumentParser(description="Write a structured Chinese analysis.md document.")
    parser.add_argument("task_id", help="Task ID")
    parser.add_argument("--state-root", help="Path to orchestrator-state")
    parser.add_argument("--goal-understanding", required=True, help="Chinese summary of the goal understanding")
    parser.add_argument("--constraint", action="append", default=[], help="Repeatable constraint item")
    parser.add_argument("--assumption", action="append", default=[], help="Repeatable assumption item")
    parser.add_argument("--risk", action="append", default=[], help="Repeatable risk item")
    parser.add_argument("--unknown", action="append", default=[], help="Repeatable open question or unknown item")
    parser.add_argument("--phase", default="analysis", help="Phase to store in state.json")
    parser.add_argument("--status", help="Optional status override")
    parser.add_argument("--revision", type=int, help="Optional revision override")
    parser.add_argument("--progress-note", default="已更新分析文档。", help="Chinese progress log note")
    parser.add_argument("--event-type", default="analysis_structured_written", help="Event type")
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
        f"# 任务 {args.task_id} 分析\n\n"
        "## 目标理解\n\n"
        f"{args.goal_understanding.strip()}\n\n"
        "## 约束\n\n"
        f"{render_bullet_block(args.constraint, fallback='- 无明确约束。')}\n\n"
        "## 假设\n\n"
        f"{render_bullet_block(args.assumption, fallback='- 暂无额外假设。')}\n\n"
        "## 风险\n\n"
        f"{render_bullet_block(args.risk, fallback='- 暂无显式风险。')}\n\n"
        "## 待确认事项\n\n"
        f"{render_bullet_block(args.unknown, fallback='- 暂无待确认事项。')}\n"
    )

    persist_artifact_update(
        state_root,
        args.task_id,
        state=state,
        artifact="analysis",
        content=content,
        event_type=args.event_type,
        progress_note=args.progress_note,
    )
    print(f"Wrote structured analysis for {args.task_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
