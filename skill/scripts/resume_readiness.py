#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json

from orchestrator_common import resolve_state_root, resolve_workspace_root, workspace_resume_snapshot


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Report whether the current workspace and orchestrator state are ready to resume.")
    parser.add_argument("--workspace", help="Workspace root")
    parser.add_argument("--state-root", help="Path to orchestrator-state")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    state_root = resolve_state_root(args.state_root) if args.state_root else resolve_state_root(None)
    workspace_root = resolve_workspace_root(args.workspace, state_root=state_root)
    payload = workspace_resume_snapshot(workspace_root, state_root)
    if payload.get("all_completed"):
        payload["recommendation"] = "所有任务已完成，无需恢复；如有新任务请直接创建"
    elif payload.get("incomplete_tasks"):
        ids = ", ".join(sorted(payload["incomplete_tasks"]))
        payload["recommendation"] = (
            f"以下任务归档不完整，需先修复再继续：{ids}。"
            "对每个不完整的任务执行 init_task.py <task-id> --repair ... 补齐缺失文件"
        )
    elif payload["ready"]:
        payload["recommendation"] = "可以恢复当前任务"
    elif payload.get("missing_state_files"):
        payload["recommendation"] = "先补齐 orchestrator-state 的基础文件，再恢复当前任务"
    elif not payload.get("active_task_ids"):
        payload["recommendation"] = "当前没有可恢复的活跃任务，先接收或创建一个任务再恢复"
    else:
        payload["recommendation"] = "先补齐 workspace/bootstrap 或缺失的任务 artifact，再恢复当前任务"

    if args.pretty:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(json.dumps(payload, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
