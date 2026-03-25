#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

from orchestrator_common import (
    discussion_file_map,
    ensure_state_root,
    linked_discussions_for_task,
    load_ledger,
    load_json,
    read_jsonl_tail,
    resolve_workspace_root,
    task_file_map,
    workspace_resume_snapshot,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Render a Chinese markdown summary from orchestrator artifacts.")
    parser.add_argument("--state-root", help="Path to orchestrator-state")
    parser.add_argument("--task-id", help="Optional task ID for a detailed task summary")
    parser.add_argument("--discussion-id", help="Optional discussion ID for a detailed discussion summary")
    parser.add_argument("--max-events", type=int, default=5, help="How many recent events to include")
    parser.add_argument("--group-by", choices=["owner", "task-type", "status"], help="Group team overview by the selected dimension")
    parser.add_argument("--blocked-only", action="store_true", help="Only include blocked tasks in the overview")
    parser.add_argument("--workspace", help="Optional workspace root for recovery-aware summary")
    parser.add_argument("--output", help="Optional output markdown path")
    return parser


def format_list(items: list[str], fallback: str) -> str:
    if not items:
        return fallback
    return "\n".join(f"- {item}" for item in items)


def summarize_workspace(workspace_root: Path, state_root: Path, *, task_ids: set[str] | None = None) -> str:
    snapshot = workspace_resume_snapshot(workspace_root, state_root, task_ids=task_ids)
    missing_workspace = snapshot.get("missing_workspace_files", [])
    missing_roles = snapshot.get("missing_workspace_roles", [])
    missing_state_files = snapshot.get("missing_state_files", [])
    missing_task_artifacts = snapshot.get("missing_task_artifacts", {})
    current_task_id = snapshot.get("current_task_id") or "无"
    if task_ids is not None and current_task_id != "无" and current_task_id not in task_ids:
        current_task_id = "无"
    return (
        "## Workspace / Resume\n\n"
        f"- workspace_root：{snapshot.get('workspace_root')}\n"
        f"- state_root：{snapshot.get('state_root')}\n"
        f"- workspace_ready：{snapshot.get('workspace_ready')}\n"
        f"- state_ready：{snapshot.get('state_ready')}\n"
        f"- ready：{snapshot.get('ready')}\n"
        f"- resume_owner：{snapshot.get('resume_owner')}\n"
        f"- current_task_id：{current_task_id}\n"
        f"- missing_workspace_files：{', '.join(missing_workspace) or '无'}\n"
        f"- missing_workspace_roles：{', '.join(missing_roles) or '无'}\n"
        f"- missing_state_files：{', '.join(missing_state_files) or '无'}\n"
        f"- missing_task_artifacts：{json.dumps(missing_task_artifacts, ensure_ascii=False) if missing_task_artifacts else '无'}\n"
    )


def summarize_task(state_root: Path, task_id: str, max_events: int, workspace_root: Path | None = None) -> str:
    paths = task_file_map(state_root, task_id)
    state = load_json(paths["state"])
    ledger = load_ledger(state_root)
    task_entry = ledger.get("tasks", {}).get(task_id, {})
    steps_doc = load_json(paths["steps"], {"task_id": task_id, "steps": []})
    events = read_jsonl_tail(paths["events"], max_events)
    workspace_section = ""
    if workspace_root is not None:
        workspace_section = summarize_workspace(workspace_root, state_root) + "\n"

    acceptance = format_list(state.get("acceptance_criteria") or [], "- 无")
    dependencies = format_list(state.get("dependencies") or [], "- 无")
    step_lines = []
    for step in steps_doc.get("steps", []):
        icon = {
            "completed": "[x]",
            "in_progress": "[>]",
            "blocked": "[!]",
            "cancelled": "[-]",
            "pending": "[ ]",
        }.get(step.get("status"), "[ ]")
        step_lines.append(f"- {icon} {step['step_id']} {step['title']}")
    event_lines = []
    for event in events:
        message = event.get("message") or event.get("reason") or ""
        suffix = f" {message}" if message else ""
        event_lines.append(f"- {event.get('ts')} {event.get('type')}{suffix}")
    linked_discussions = linked_discussions_for_task(state_root, task_id)
    discussion_lines = [format_discussion_line(discussion) for discussion in linked_discussions]

    return (
        f"# 任务摘要 {task_id}\n\n"
        f"{workspace_section}"
        f"- 目标：{state.get('goal') or '无'}\n"
        f"- 范围：{state.get('scope') or '无'}\n"
        f"- 状态：{state.get('status') or '未知'}\n"
        f"- 阶段：{state.get('phase') or '未知'}\n"
        f"- 修订版本：{state.get('revision')}\n"
        f"- 负责人：{state.get('owner_agent_id') or '无'}\n"
        f"- 任务类型：{state.get('task_type') or '无'}\n"
        f"- 成员角色：{state.get('member_role_name') or '无'}\n"
        f"- 父任务：{state.get('parent_task_id') or '无'}\n"
        f"- 子任务：{', '.join(task_entry.get('child_task_ids') or []) or '无'}\n"
        f"- 当前步骤：{state.get('current_step_id') or '无'}\n"
        f"- Artifact 路径：{paths['state'].parent}\n\n"
        "## 验收标准\n\n"
        f"{acceptance}\n\n"
        "## 依赖\n\n"
        f"{dependencies}\n\n"
        "## 步骤概览\n\n"
        f"{chr(10).join(step_lines) if step_lines else '- 暂无步骤'}\n\n"
        "## 最近事件\n\n"
        f"{chr(10).join(event_lines) if event_lines else '- 暂无事件'}\n\n"
        "## 成员讨论\n\n"
        f"{chr(10).join(discussion_lines) if discussion_lines else '- 暂无关联讨论'}\n"
    )


def format_discussion_line(discussion: dict[str, Any]) -> str:
    participants = ",".join(discussion.get("participants") or []) or "无"
    linked_tasks = ",".join(discussion.get("linked_task_ids") or []) or "无"
    resolution = discussion.get("resolution_summary") or "无"
    return (
        f"- {discussion.get('discussion_id')} | {discussion.get('mode') or '未知'} | "
        f"{discussion.get('status') or '未知'} | initiator={discussion.get('initiator') or '无'} | "
        f"participants={participants} | tasks={linked_tasks} | topic={discussion.get('title') or '无'} | "
        f"resolution={resolution}"
    )


def summarize_discussion(state_root: Path, discussion_id: str, max_events: int, workspace_root: Path | None = None) -> str:
    paths = discussion_file_map(state_root, discussion_id)
    state = load_json(paths["state"])
    messages = read_jsonl_tail(paths["messages"], max_events)
    workspace_section = ""
    if workspace_root is not None:
        workspace_section = summarize_workspace(workspace_root, state_root, task_ids=set(state.get("linked_task_ids") or [])) + "\n"

    message_lines = []
    for message in messages:
        sender = message.get("sender") or "未知"
        receivers = ",".join(message.get("to") or []) or "all"
        body = (message.get("body") or "").replace("\n", " ").strip()
        kind = message.get("kind") or message.get("type") or "note"
        message_lines.append(f"- {message.get('ts')} {sender} -> {receivers} [{kind}] {body}")

    decision_text = paths["decision"].read_text(encoding="utf-8").strip() if paths["decision"].exists() else "无"
    return (
        f"# 讨论摘要 {discussion_id}\n\n"
        f"{workspace_section}"
        f"- 主题：{state.get('title') or '无'}\n"
        f"- 模式：{state.get('mode') or '未知'}\n"
        f"- 状态：{state.get('status') or '未知'}\n"
        f"- 发起人：{state.get('initiator') or '无'}\n"
        f"- 参与者：{', '.join(state.get('participants') or []) or '无'}\n"
        f"- 关联任务：{', '.join(state.get('linked_task_ids') or []) or '无'}\n"
        f"- 结论摘要：{state.get('resolution_summary') or '无'}\n\n"
        "## 最近消息\n\n"
        f"{chr(10).join(message_lines) if message_lines else '- 暂无消息'}\n\n"
        "## 决议记录\n\n"
        f"{decision_text}\n"
    )


def format_team_task_line(task: dict[str, str]) -> str:
    return (
        f"- {task.get('task_id')} | owner={task.get('owner_agent_id') or '无'} | "
        f"type={task.get('task_type') or '无'} | member={task.get('member_role_name') or '无'} | "
        f"status={task.get('status') or '未知'} | phase={task.get('phase') or '未知'} | "
        f"goal={task.get('goal') or '无'}"
    )


def summarize_all(
    state_root: Path,
    *,
    group_by: str | None = None,
    blocked_only: bool = False,
    workspace_root: Path | None = None,
) -> str:
    ledger = load_ledger(state_root)
    tasks = list(ledger.get("tasks", {}).values())
    discussions = list(ledger.get("discussions", {}).values())
    tasks.sort(key=lambda item: item.get("updated_at", ""), reverse=True)
    discussions.sort(key=lambda item: item.get("updated_at", ""), reverse=True)
    if blocked_only:
        tasks = [task for task in tasks if task.get("status") == "blocked"]
        task_ids = {task.get("task_id") for task in tasks if task.get("task_id")}
        discussions = [
            discussion
            for discussion in discussions
            if any(task_id in task_ids for task_id in (discussion.get("linked_task_ids") or []))
        ]

    status_counts: dict[str, int] = {}
    for task in tasks:
        status = task.get("status", "unknown")
        status_counts[status] = status_counts.get(status, 0) + 1
    discussion_counts: dict[str, int] = {}
    for discussion in discussions:
        status = discussion.get("status", "unknown")
        discussion_counts[status] = discussion_counts.get(status, 0) + 1

    header = [
        "# Team Leader 总览" if group_by or blocked_only else "# Orchestrator 总览",
        "",
        f"- 任务总数：{len(tasks)}",
        f"- 阻塞任务：{sum(1 for task in tasks if task.get('status') == 'blocked')}",
        f"- 状态分布：{', '.join(f'{key}={value}' for key, value in sorted(status_counts.items())) or '无'}",
        f"- 讨论总数：{len(discussions)}",
        f"- 讨论分布：{', '.join(f'{key}={value}' for key, value in sorted(discussion_counts.items())) or '无'}",
        "",
    ]
    if workspace_root is not None:
        task_ids = {task.get("task_id") for task in tasks if task.get("task_id")}
        header.append(summarize_workspace(workspace_root, state_root, task_ids=task_ids if blocked_only else None))

    if group_by is None:
        rows = [
            (
                f"- {task.get('task_id')} | parent={task.get('parent_task_id') or '无'} | "
                f"children={','.join(task.get('child_task_ids') or []) or '无'} | "
                f"{task.get('phase') or '未知'} | {task.get('status') or '未知'} | {task.get('goal') or '无'}"
            )
            for task in tasks
        ]
        discussion_rows = [format_discussion_line(discussion) for discussion in discussions]
        return "\n".join(
            header
            + ["## 任务列表", ""]
            + (rows or ["- 暂无任务"])
            + ["", "## 成员讨论", ""]
            + (discussion_rows or ["- 暂无成员讨论"])
        ) + "\n"

    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for task in tasks:
        if group_by == "owner":
            key = task.get("owner_agent_id") or task.get("member_role_name") or "无"
        elif group_by == "task-type":
            key = task.get("task_type") or "无"
        else:
            key = task.get("status") or "未知"
        grouped[key].append(task)

    sections = []
    for group_key in sorted(grouped):
        section_tasks = sorted(grouped[group_key], key=lambda item: item.get("updated_at", ""), reverse=True)
        blocked_count = sum(1 for task in section_tasks if task.get("status") == "blocked")
        sections.append(f"## {group_by}：{group_key} ({len(section_tasks)} 项，阻塞 {blocked_count} 项)")
        sections.append("")
        sections.extend(format_team_task_line(task) for task in section_tasks)
        sections.append("")

    if not sections:
        sections = ["- 暂无任务"]
    discussion_section = ["## 成员讨论", ""]
    discussion_section.extend(format_discussion_line(discussion) for discussion in discussions)
    if not discussions:
        discussion_section.append("- 暂无成员讨论")
    discussion_section.append("")

    return "\n".join(header + sections + discussion_section).rstrip() + "\n"


def main() -> int:
    args = build_parser().parse_args()
    state_root = ensure_state_root(args.state_root)
    workspace_root = resolve_workspace_root(args.workspace, state_root=state_root)
    if args.task_id and args.discussion_id:
        raise SystemExit("Use either --task-id or --discussion-id, not both")
    summary = (
        summarize_task(state_root, args.task_id, args.max_events, workspace_root=workspace_root)
        if args.task_id
        else (
            summarize_discussion(state_root, args.discussion_id, args.max_events, workspace_root=workspace_root)
            if args.discussion_id
            else summarize_all(state_root, group_by=args.group_by, blocked_only=args.blocked_only, workspace_root=workspace_root)
        )
    )

    if args.output:
        output_path = Path(args.output).expanduser().resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(summary, encoding="utf-8")

    print(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
