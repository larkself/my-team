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
    parser = argparse.ArgumentParser(description="Write a structured Chinese design.md document.")
    parser.add_argument("task_id", help="Task ID")
    parser.add_argument("--state-root", help="Path to orchestrator-state")
    parser.add_argument("--solution-summary", required=True, help="Chinese solution summary")
    parser.add_argument("--decision", action="append", default=[], help="Repeatable key decision")
    parser.add_argument("--alternative", action="append", default=[], help="Repeatable alternative approach")
    parser.add_argument("--boundary", action="append", default=[], help="Repeatable boundary or interface note")
    parser.add_argument("--dependency", action="append", default=[], help="Repeatable dependency")
    parser.add_argument("--risk", action="append", default=[], help="Repeatable design risk or tradeoff")
    parser.add_argument("--phase", default="design", help="Phase to store in state.json")
    parser.add_argument("--status", help="Optional status override")
    parser.add_argument("--revision", type=int, help="Optional revision override")
    parser.add_argument("--progress-note", default="已更新设计文档。", help="Chinese progress log note")
    parser.add_argument("--event-type", default="design_structured_written", help="Event type")
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
        f"# 任务 {args.task_id} 设计\n\n"
        "## 方案概述\n\n"
        f"{args.solution_summary.strip()}\n\n"
        "## 关键决策\n\n"
        f"{render_bullet_block(args.decision, fallback='- 待补充关键决策。')}\n\n"
        "## 备选方案\n\n"
        f"{render_bullet_block(args.alternative, fallback='- 暂无额外备选方案。')}\n\n"
        "## 边界与接口\n\n"
        f"{render_bullet_block(args.boundary, fallback='- 待补充边界说明。')}\n\n"
        "## 依赖\n\n"
        f"{render_bullet_block(args.dependency, fallback='- 无额外依赖。')}\n\n"
        "## 风险与权衡\n\n"
        f"{render_bullet_block(args.risk, fallback='- 暂无显式风险与权衡。')}\n"
    )

    persist_artifact_update(
        state_root,
        args.task_id,
        state=state,
        artifact="design",
        content=content,
        event_type=args.event_type,
        progress_note=args.progress_note,
    )
    print(f"Wrote structured design for {args.task_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
