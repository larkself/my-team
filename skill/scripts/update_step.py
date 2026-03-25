#!/usr/bin/env python3
from __future__ import annotations

import argparse

from orchestrator_common import (
    append_jsonl,
    append_transition_events,
    append_progress_log,
    ensure_state_root,
    ensure_task_exists,
    load_state,
    load_steps,
    persist_state_snapshot,
    save_steps,
    task_file_map,
    utc_now,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Update a task step in steps.json.")
    parser.add_argument("task_id", help="Task ID")
    parser.add_argument("action", choices=["add", "start", "complete", "block", "cancel"])
    parser.add_argument("--state-root", help="Path to orchestrator-state")
    parser.add_argument("--step-id", required=True, help="Step ID")
    parser.add_argument("--title", help="Step title, required for add")
    parser.add_argument("--description", help="Optional step description")
    parser.add_argument("--note", help="Optional progress note")
    return parser


def find_step(steps_doc: dict, step_id: str) -> dict | None:
    for step in steps_doc["steps"]:
        if step["step_id"] == step_id:
            return step
    return None


def all_steps_completed(steps_doc: dict) -> bool:
    return bool(steps_doc["steps"]) and all(step.get("status") == "completed" for step in steps_doc["steps"])


def has_open_execution(steps_doc: dict) -> bool:
    return any(step.get("status") in {"in_progress", "blocked"} for step in steps_doc["steps"])


def main() -> int:
    args = build_parser().parse_args()
    state_root = ensure_state_root(args.state_root)
    ensure_task_exists(state_root, args.task_id)

    state = load_state(state_root, args.task_id)
    previous_state = dict(state)
    steps_doc = load_steps(state_root, args.task_id)
    step = find_step(steps_doc, args.step_id)
    now = utc_now()

    if args.action == "add":
        if step is not None:
            raise SystemExit(f"Step already exists: {args.step_id}")
        if not args.title:
            raise SystemExit("--title is required when action=add")
        step = {
            "step_id": args.step_id,
            "title": args.title,
            "description": args.description or "",
            "status": "pending",
            "created_at": now,
            "updated_at": now,
        }
        steps_doc["steps"].append(step)
        event_type = "step_added"
        progress_message = args.note or f"已添加步骤 {args.step_id}：{args.title}"
    else:
        if step is None:
            raise SystemExit(f"Step not found: {args.step_id}")
        step["updated_at"] = now
        event_type = f"step_{args.action}"
        default_note = {
            "start": f"开始执行步骤 {args.step_id}：{step['title']}",
            "complete": f"已完成步骤 {args.step_id}：{step['title']}",
            "block": f"步骤 {args.step_id} 已阻塞：{step['title']}",
            "cancel": f"步骤 {args.step_id} 已取消：{step['title']}",
        }
        progress_message = args.note or default_note[args.action]

        if args.action == "start":
            step["status"] = "in_progress"
            step.setdefault("started_at", now)
            state["phase"] = "executing"
            state["status"] = "in_progress"
            state["current_step_id"] = args.step_id
        elif args.action == "complete":
            step["status"] = "completed"
            step["completed_at"] = now
            if state.get("current_step_id") == args.step_id:
                state["current_step_id"] = None
            state["status"] = "in_progress"
            if all_steps_completed(steps_doc):
                state["phase"] = "reporting"
        elif args.action == "block":
            step["status"] = "blocked"
            step["blocked_at"] = now
            state["phase"] = "executing"
            state["status"] = "blocked"
            state["current_step_id"] = args.step_id
        elif args.action == "cancel":
            step["status"] = "cancelled"
            if state.get("current_step_id") == args.step_id:
                state["current_step_id"] = None
            if not has_open_execution(steps_doc):
                state["status"] = "in_progress"

    save_steps(state_root, args.task_id, steps_doc)

    paths = task_file_map(state_root, args.task_id)
    persist_state_snapshot(state_root, args.task_id, state)
    append_transition_events(paths["events"], args.task_id, previous_state, state, ts=now)
    append_jsonl(
        paths["events"],
        {
            "ts": now,
            "type": event_type,
            "task_id": args.task_id,
            "step_id": args.step_id,
            "phase": state.get("phase"),
            "status": state.get("status"),
        },
    )
    append_progress_log(paths["progress"], progress_message, ts=now)

    print(f"Updated step {args.step_id} for {args.task_id} with action {args.action}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
