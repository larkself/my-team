#!/usr/bin/env python3
from __future__ import annotations

import argparse

from orchestrator_common import (
    ensure_state_root,
    ensure_task_exists,
    load_state,
    load_steps,
    persist_artifact_update,
    render_bullet_block,
    render_numbered_block,
    save_steps,
    utc_now,
)

VALID_STEP_STATUSES = {"pending", "in_progress", "completed", "blocked", "cancelled"}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Write a structured Chinese plan.md document.")
    parser.add_argument("task_id", help="Task ID")
    parser.add_argument("--state-root", help="Path to orchestrator-state")
    parser.add_argument(
        "--step",
        action="append",
        default=[],
        help="Repeatable step spec: STEP_ID|Title|status where status defaults to pending",
    )
    parser.add_argument("--current-focus", required=True, help="Chinese current focus summary")
    parser.add_argument("--milestone", action="append", default=[], help="Repeatable milestone item")
    parser.add_argument("--dependency", action="append", default=[], help="Repeatable dependency item")
    parser.add_argument("--risk", action="append", default=[], help="Repeatable risk item")
    parser.add_argument("--phase", default="planning", help="Phase to store in state.json")
    parser.add_argument("--status", help="Optional status override")
    parser.add_argument("--revision", type=int, help="Optional revision override")
    parser.add_argument("--sync-steps", action="store_true", help="Also rewrite steps.json from --step values")
    parser.add_argument(
        "--replace-steps",
        action="store_true",
        help="When syncing steps, drop omitted historical steps instead of preserving them.",
    )
    parser.add_argument("--progress-note", default="已更新计划文档。", help="Chinese progress log note")
    parser.add_argument("--event-type", default="plan_structured_written", help="Event type")
    return parser


def parse_step_specs(raw_steps: list[str]) -> list[dict[str, str]]:
    parsed = []
    for raw_step in raw_steps:
        parts = [part.strip() for part in raw_step.split("|")]
        if len(parts) not in {2, 3}:
            raise SystemExit(f"Invalid --step value: {raw_step}")
        step_id, title = parts[0], parts[1]
        status = parts[2] if len(parts) == 3 else "pending"
        if status not in VALID_STEP_STATUSES:
            raise SystemExit(f"Invalid step status '{status}' in {raw_step}")
        parsed.append({"step_id": step_id, "title": title, "status": status})
    return parsed


def step_display_text(step: dict[str, str]) -> str:
    return f"[{step['status']}] {step['step_id']} {step['title']}"


def sync_steps_doc(state_root, task_id: str, parsed_steps: list[dict[str, str]], *, replace_steps: bool = False) -> None:
    existing = load_steps(state_root, task_id)
    existing_by_id = {item["step_id"]: item for item in existing.get("steps", [])}
    parsed_ids = {step["step_id"] for step in parsed_steps}
    now = utc_now()
    next_steps = []
    for step in parsed_steps:
        record = existing_by_id.get(step["step_id"], {})
        record.update(
            {
                "step_id": step["step_id"],
                "title": step["title"],
                "status": step["status"],
                "updated_at": now,
            }
        )
        record.setdefault("created_at", now)
        if step["status"] == "in_progress":
            record.setdefault("started_at", now)
        if step["status"] == "completed":
            record.setdefault("completed_at", now)
        if step["status"] == "blocked":
            record.setdefault("blocked_at", now)
        next_steps.append(record)
    if not replace_steps:
        for record in existing.get("steps", []):
            if record["step_id"] in parsed_ids:
                continue
            if record.get("status") in {"completed", "in_progress", "blocked", "cancelled"}:
                record["updated_at"] = now
                next_steps.append(record)
    save_steps(state_root, task_id, {"task_id": task_id, "steps": next_steps})


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

    parsed_steps = parse_step_specs(args.step)
    content = (
        f"# 任务 {args.task_id} 计划\n\n"
        "## 步骤列表\n\n"
        f"{render_numbered_block([step_display_text(step) for step in parsed_steps], fallback='待补充执行步骤。')}\n\n"
        "## 当前重点\n\n"
        f"{args.current_focus.strip()}\n\n"
        "## 里程碑\n\n"
        f"{render_bullet_block(args.milestone, fallback='- 暂无额外里程碑。')}\n\n"
        "## 依赖\n\n"
        f"{render_bullet_block(args.dependency, fallback='- 无额外依赖。')}\n\n"
        "## 风险与注意事项\n\n"
        f"{render_bullet_block(args.risk, fallback='- 暂无额外风险与注意事项。')}\n"
    )

    persist_artifact_update(
        state_root,
        args.task_id,
        state=state,
        artifact="plan",
        content=content,
        event_type=args.event_type,
        progress_note=args.progress_note,
    )
    if args.sync_steps:
        sync_steps_doc(state_root, args.task_id, parsed_steps, replace_steps=args.replace_steps)
    print(f"Wrote structured plan for {args.task_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
