#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

STATE_ROOT_NAME = "orchestrator-state"
SKILL_DIR_NAME = ".my-team"
VALID_PHASES = {
    "received",
    "analysis",
    "design",
    "planning",
    "executing",
    "reporting",
    "completed",
    "interrupted",
    "revising",
}
VALID_STATUSES = {
    "pending",
    "in_progress",
    "blocked",
    "interrupted",
    "revising",
    "completed",
    "cancelled",
}
VALID_DISCUSSION_MODES = {"consult", "sync"}
VALID_DISCUSSION_STATUSES = {"open", "resolved", "closed"}
STANDARD_MEMBER_TASK_TYPES = {"analysis", "design", "coding", "testing"}
STANDARD_MEMBER_TASK_TYPES.update({"review", "docs", "release", "integration"})
STANDARD_MEMBER_ROLE_PREFIX = "member-"
STANDARD_MEMBER_ROLE_NAMES = {
    task_type: f"{STANDARD_MEMBER_ROLE_PREFIX}{task_type}"
    for task_type in STANDARD_MEMBER_TASK_TYPES
}
STANDARD_MEMBER_TASK_TYPE_CHOICES = tuple(sorted(STANDARD_MEMBER_TASK_TYPES))
STANDARD_WORKSPACE_ROLE_NAMES = ("leader", *tuple(sorted(STANDARD_MEMBER_ROLE_NAMES.values())))


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def local_now() -> datetime:
    return datetime.now().astimezone()


def local_date_str() -> str:
    return local_now().date().isoformat()


def local_time_str() -> str:
    return local_now().strftime("%H:%M:%S")


def resolve_state_root(raw_path: str | None) -> Path:
    if raw_path:
        return Path(raw_path).expanduser().resolve()
    return (Path.cwd() / SKILL_DIR_NAME / STATE_ROOT_NAME).resolve()


def resolve_workspace_root(raw_path: str | None, *, state_root: Path | None = None) -> Path:
    if raw_path:
        return Path(raw_path).expanduser().resolve()
    if state_root is not None:
        return state_root.parent.resolve()
    return (Path.cwd() / SKILL_DIR_NAME).resolve()


def default_ledger() -> dict[str, Any]:
    return {
        "schema_version": 1,
        "updated_at": utc_now(),
        "tasks": {},
        "discussions": {},
    }


def default_ledger_task_entry(state_root: Path, task_id: str) -> dict[str, Any]:
    return {
        "task_id": task_id,
        "parent_task_id": None,
        "owner_agent_id": "unassigned",
        "task_type": None,
        "member_role_name": None,
        "status": "pending",
        "phase": "received",
        "revision": 0,
        "goal": "待补充",
        "scope": "待补充",
        "priority": "medium",
        "artifact_path": str(task_dir(state_root, task_id)),
        "updated_at": utc_now(),
        "child_task_ids": [],
    }


def default_task_state(task_id: str, *, parent_task_id: str | None = None) -> dict[str, Any]:
    now = utc_now()
    return {
        "task_id": task_id,
        "parent_task_id": parent_task_id,
        "owner_agent_id": "unassigned",
        "task_type": None,
        "member_role_name": None,
        "status": "pending",
        "phase": "received",
        "revision": 0,
        "goal": "待补充",
        "scope": "待补充",
        "priority": "medium",
        "dependencies": [],
        "acceptance_criteria": [],
        "current_step_id": None,
        "created_at": now,
        "updated_at": now,
    }


def task_state_from_ledger_entry(task_id: str, entry: dict[str, Any] | None = None) -> dict[str, Any]:
    state = default_task_state(task_id, parent_task_id=(entry or {}).get("parent_task_id"))
    if not entry:
        return state

    for key in [
        "owner_agent_id",
        "task_type",
        "member_role_name",
        "status",
        "phase",
        "revision",
        "goal",
        "scope",
        "priority",
        "current_step_id",
    ]:
        if key in entry:
            state[key] = entry[key]

    if entry.get("dependencies") is not None:
        state["dependencies"] = list(entry.get("dependencies") or [])
    if entry.get("acceptance_criteria") is not None:
        state["acceptance_criteria"] = list(entry.get("acceptance_criteria") or [])
    if entry.get("created_at"):
        state["created_at"] = entry["created_at"]
    if entry.get("updated_at"):
        state["updated_at"] = entry["updated_at"]
    return state


def ensure_state_root(raw_path: str | None) -> Path:
    state_root = resolve_state_root(raw_path)
    (state_root / "tasks").mkdir(parents=True, exist_ok=True)
    (state_root / "discussions").mkdir(parents=True, exist_ok=True)
    ledger_path = state_root / "ledger.json"
    if not ledger_path.exists():
        write_json(ledger_path, default_ledger())
    return state_root


def load_json(path: Path, default: Any | None = None) -> Any:
    if not path.exists():
        if default is None:
            raise FileNotFoundError(f"JSON file not found: {path}")
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def append_jsonl(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False) + "\n")


def append_progress_log(path: Path, message: str, *, ts: str | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    timestamp = ts or utc_now()
    with path.open("a", encoding="utf-8") as handle:
        handle.write(f"[{timestamp}] {message}\n")


def task_dir(state_root: Path, task_id: str) -> Path:
    return state_root / "tasks" / task_id


def doc_refresh_log_path(state_root: Path) -> Path:
    return state_root / "doc-refresh.jsonl"


def discussions_dir(state_root: Path) -> Path:
    return state_root / "discussions"


def workspace_paths(workspace_root: Path) -> dict[str, Path]:
    return {
        "root": workspace_root,
        "team": workspace_root / "TEAM.md",
        "memory": workspace_root / "MEMORY.md",
        "user_context": workspace_root / "USER_CONTEXT.md",
        "roles_dir": workspace_root / "ROLES",
        "inbox": workspace_root / "INBOX.md",
        "sessions_dir": workspace_root / "SESSIONS",
        "current_session": workspace_root / "SESSIONS" / "current.md",
        "ai_chat_dir": workspace_root / "ai-chat",
    }


def workspace_role_path(workspace_root: Path, role_name: str) -> Path:
    return workspace_paths(workspace_root)["roles_dir"] / f"{role_name}.md"


def workspace_role_descriptions() -> dict[str, str]:
    descriptions = {
        "leader": "负责接单、协调、分配、汇报和恢复。",
    }
    for role_name in STANDARD_MEMBER_ROLE_NAMES.values():
        task_type = member_task_type_from_role_name(role_name) or "member"
        descriptions[role_name] = f"负责 {task_type} 相关的局部执行工作，并向 team leader 汇报进展。"
    return descriptions


def default_workspace_markdown(workspace_root: Path, *, state_root: Path | None = None) -> dict[str, str]:
    state_root_text = str(state_root) if state_root else "待确认"
    files = {
        "TEAM.md": (
            "# My Team Workspace\n\n"
            "## Team Contract\n\n"
            "- team leader 负责协调、分配、汇报和恢复\n"
            "- member 负责分析、设计、开发、测试与专项执行\n"
            "- long-lived workspace 用来保存跨会话可恢复信息\n\n"
            "## Recovery Rules\n\n"
            "- 先检查 MEMORY.md、SESSIONS/current.md 和 orchestrator-state\n"
            "- 关键事实、偏好和约束写入 MEMORY.md\n"
            "- 当前进展和下一步写入 SESSIONS/current.md\n"
        ),
        "MEMORY.md": (
            "# Memory\n\n"
            "## Facts\n\n"
            "- 待补充\n\n"
            "## Decisions\n\n"
            "- 待补充\n\n"
            "## Preferences\n\n"
            "- 待补充\n\n"
            "## Constraints\n\n"
            "- 待补充\n"
        ),
        "USER_CONTEXT.md": (
            "# User Context\n\n"
            f"- workspace_root: {workspace_root}\n"
            f"- state_root: {state_root_text}\n"
            f"- skill_name: my-team\n"
            "- update this file when the user confirms new defaults, paths, or recovery constraints\n"
        ),
        "INBOX.md": (
            "# Inbox\n\n"
            "## Active Items\n\n"
            "- 待补充\n\n"
            "## Recovery Notes\n\n"
            "- 待补充\n"
        ),
        "SESSIONS/current.md": (
            "# Current Session\n\n"
            "## Snapshot\n\n"
            "- status: bootstrap\n"
            "- next_action: initialize workspace, read memory, then resume orchestrator state\n\n"
            "## Recent Updates\n\n"
            "- 待补充\n"
        ),
        "ROLES/leader.md": (
            "# Role: leader\n\n"
            "## Standing Orders\n\n"
            "- 负责接单、协调、分配、汇报和恢复\n"
            "- 不亲自承担分析、设计、开发和测试工作\n"
            "- 先让 member 做分析拆解，再把后续工作分给其他 member\n"
            "- 把任务分配、完成情况和阻塞状态及时反馈给用户\n"
        ),
    }

    for role_name, description in workspace_role_descriptions().items():
        if role_name == "leader":
            continue
        files[f"ROLES/{role_name}.md"] = (
            f"# Role: {role_name}\n\n"
            "## Standing Orders\n\n"
            f"- {description}\n"
            "- 遇到阻塞时要及时回报 team leader\n"
            "- 交付时保留可恢复的 artifact 和 handoff 信息\n"
        )

    return files


def ensure_workspace_scaffold(
    workspace_root: Path,
    *,
    state_root: Path | None = None,
    overwrite: bool = False,
) -> dict[str, Path]:
    paths = workspace_paths(workspace_root)
    paths["root"].mkdir(parents=True, exist_ok=True)
    paths["roles_dir"].mkdir(parents=True, exist_ok=True)
    paths["sessions_dir"].mkdir(parents=True, exist_ok=True)
    paths["ai_chat_dir"].mkdir(parents=True, exist_ok=True)

    defaults = default_workspace_markdown(workspace_root, state_root=state_root)
    for relative_name, content in defaults.items():
        path = workspace_root / relative_name
        if overwrite or not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")

    for role_name in STANDARD_WORKSPACE_ROLE_NAMES:
        role_path = workspace_role_path(workspace_root, role_name)
        if overwrite or not role_path.exists():
            role_path.parent.mkdir(parents=True, exist_ok=True)
            if role_name == "leader":
                role_content = (
                    "# Role: leader\n\n"
                    "## Standing Orders\n\n"
                    "- 负责接单、协调、分配、汇报和恢复\n"
                    "- 不亲自承担分析、设计、开发和测试工作\n"
                    "- 先让 member 做分析拆解，再把后续工作分给其他 member\n"
                    "- 把任务分配、完成情况和阻塞状态及时反馈给用户\n"
                )
            else:
                task_type = member_task_type_from_role_name(role_name) or "member"
                role_content = (
                    f"# Role: {role_name}\n\n"
                    "## Standing Orders\n\n"
                    f"- 负责 {task_type} 相关的局部执行工作，并向 team leader 汇报进展\n"
                    "- 遇到阻塞时要及时回报 team leader\n"
                    "- 交付时保留可恢复的 artifact 和 handoff 信息\n"
                )
            role_path.write_text(role_content, encoding="utf-8")

    return paths


def append_workspace_memory_entries(
    workspace_root: Path,
    entries: list[tuple[str, str]],
    *,
    source: str | None = None,
    ts: str | None = None,
) -> None:
    if not entries:
        return
    ensure_workspace_scaffold(workspace_root)
    timestamp = ts or utc_now()
    memory_path = workspace_paths(workspace_root)["memory"]
    block_lines = [f"## {timestamp}"]
    if source:
        block_lines.append(f"- source: {source}")
    for entry_type, text in entries:
        block_lines.append(f"- {entry_type}: {text}")
    block_lines.append("")
    with memory_path.open("a", encoding="utf-8") as handle:
        handle.write("\n".join(block_lines) + "\n")


def append_workspace_session_note(
    workspace_root: Path,
    title: str,
    lines: list[str] | None = None,
    *,
    ts: str | None = None,
) -> None:
    ensure_workspace_scaffold(workspace_root)
    timestamp = ts or utc_now()
    session_path = workspace_paths(workspace_root)["current_session"]
    block_lines = [f"## {timestamp}", f"- {title}"]
    for line in lines or []:
        block_lines.append(f"- {line}")
    block_lines.append("")
    with session_path.open("a", encoding="utf-8") as handle:
        handle.write("\n".join(block_lines) + "\n")


def workspace_file_status(workspace_root: Path) -> dict[str, Any]:
    paths = workspace_paths(workspace_root)
    return {
        "workspace_root": str(workspace_root),
        "missing_files": [
            key
            for key in ["team", "memory", "user_context", "inbox", "current_session"]
            if not paths[key].exists()
        ],
        "roles_missing": [
            role_name
            for role_name in STANDARD_WORKSPACE_ROLE_NAMES
            if not workspace_role_path(workspace_root, role_name).exists()
        ],
    }


def discussion_dir(state_root: Path, discussion_id: str) -> Path:
    return discussions_dir(state_root) / discussion_id


def discussion_file_map(state_root: Path, discussion_id: str) -> dict[str, Path]:
    base_dir = discussion_dir(state_root, discussion_id)
    return {
        "topic": base_dir / "topic.md",
        "decision": base_dir / "decision.md",
        "state": base_dir / "state.json",
        "messages": base_dir / "messages.jsonl",
    }


def workspace_resume_snapshot(
    workspace_root: Path,
    state_root: Path,
    *,
    task_ids: set[str] | None = None,
) -> dict[str, Any]:
    workspace_status = workspace_file_status(workspace_root)
    ledger_path = state_root / "ledger.json"
    ledger_exists = ledger_path.exists()
    ledger = load_ledger(state_root) if ledger_exists else default_ledger()
    active_tasks = [
        task
        for task in ledger.get("tasks", {}).values()
        if task.get("status") not in {"completed", "cancelled"}
    ]
    if task_ids is not None:
        active_tasks = [task for task in active_tasks if task.get("task_id") in task_ids]
    active_tasks.sort(key=lambda item: item.get("updated_at", ""), reverse=True)
    current_task = active_tasks[0] if active_tasks else None
    missing_task_artifacts: dict[str, list[str]] = {}
    for task in active_tasks:
        task_id = task.get("task_id")
        if not task_id:
            continue
        paths = task_file_map(state_root, task_id)
        required = ["task", "progress", "state", "handoff", "events"]
        if task.get("phase") in {"analysis", "design", "planning", "executing", "reporting", "revising"}:
            required.extend(["analysis", "design", "plan"])
        if task.get("phase") in {"reporting", "completed"}:
            required.append("result")
        missing = [name for name in required if not paths[name].exists()]
        if missing:
            missing_task_artifacts[task_id] = missing

    # Check ALL ledger tasks for incomplete scaffolds (directory exists
    # but core files missing, or directory absent entirely).
    incomplete_tasks: dict[str, list[str]] = {}
    for task in ledger.get("tasks", {}).values():
        tid = task.get("task_id")
        if not tid:
            continue
        missing_core = verify_task_integrity(state_root, tid)
        if missing_core:
            incomplete_tasks[tid] = missing_core

    resume_owner = None
    resume_task_id = None
    if current_task:
        resume_task_id = current_task.get("task_id")
        owner = current_task.get("owner_agent_id") or current_task.get("member_role_name") or "main"
        resume_owner = "team leader" if owner in {"main", "unassigned"} else owner

    all_tasks = list(ledger.get("tasks", {}).values())
    all_completed = all_tasks and all(
        task.get("status") in {"completed", "cancelled"} for task in all_tasks
    )

    if all_completed:
        ready = (
            ledger_exists
            and not workspace_status["missing_files"]
            and not workspace_status["roles_missing"]
        )
    else:
        ready = (
            ledger_exists
            and bool(active_tasks)
            and not workspace_status["missing_files"]
            and not workspace_status["roles_missing"]
            and not missing_task_artifacts
            and not incomplete_tasks
        )
    return {
        "workspace_root": str(workspace_root),
        "state_root": str(state_root),
        "workspace_ready": not workspace_status["missing_files"] and not workspace_status["roles_missing"],
        "state_ready": ledger_exists,
        "ready": ready,
        "all_completed": all_completed,
        "current_task_id": resume_task_id,
        "resume_owner": resume_owner or "team leader",
        "missing_workspace_files": workspace_status["missing_files"],
        "missing_workspace_roles": workspace_status["roles_missing"],
        "missing_state_files": [] if ledger_exists else ["ledger.json"],
        "missing_task_artifacts": missing_task_artifacts,
        "incomplete_tasks": incomplete_tasks,
        "active_task_ids": [task.get("task_id") for task in active_tasks if task.get("task_id")],
    }


def internal_dir(state_root: Path, task_id: str) -> Path:
    return task_dir(state_root, task_id) / "internal"


def task_file_map(state_root: Path, task_id: str) -> dict[str, Path]:
    base_dir = task_dir(state_root, task_id)
    return {
        "task": base_dir / "task.md",
        "analysis": base_dir / "analysis.md",
        "design": base_dir / "design.md",
        "plan": base_dir / "plan.md",
        "progress": base_dir / "progress.log",
        "result": base_dir / "result.md",
        "brief": base_dir / "internal" / "brief.en.md",
        "handoff": base_dir / "internal" / "handoff.en.md",
        "state": base_dir / "state.json",
        "steps": base_dir / "steps.json",
        "events": base_dir / "events.jsonl",
    }


def validate_phase(phase: str | None) -> None:
    if phase is None:
        return
    if phase not in VALID_PHASES:
        raise ValueError(f"Invalid phase '{phase}'. Allowed values: {', '.join(sorted(VALID_PHASES))}")


def validate_status(status: str | None) -> None:
    if status is None:
        return
    if status not in VALID_STATUSES:
        raise ValueError(f"Invalid status '{status}'. Allowed values: {', '.join(sorted(VALID_STATUSES))}")


def validate_discussion_mode(mode: str | None) -> None:
    if mode is None:
        return
    if mode not in VALID_DISCUSSION_MODES:
        raise ValueError(f"Invalid discussion mode '{mode}'. Allowed values: {', '.join(sorted(VALID_DISCUSSION_MODES))}")


def validate_discussion_status(status: str | None) -> None:
    if status is None:
        return
    if status not in VALID_DISCUSSION_STATUSES:
        raise ValueError(
            f"Invalid discussion status '{status}'. Allowed values: {', '.join(sorted(VALID_DISCUSSION_STATUSES))}"
        )


def canonical_member_role_name(task_type: str | None) -> str | None:
    if task_type is None:
        return None
    if task_type not in STANDARD_MEMBER_TASK_TYPES:
        raise ValueError(
            f"Invalid task_type '{task_type}'. Allowed values: {', '.join(sorted(STANDARD_MEMBER_TASK_TYPES))}"
        )
    return STANDARD_MEMBER_ROLE_NAMES[task_type]


def member_task_type_from_role_name(role_name: str | None) -> str | None:
    if role_name is None:
        return None
    if role_name in {"main", "unassigned"}:
        return None
    if role_name.startswith(STANDARD_MEMBER_ROLE_PREFIX):
        candidate = role_name.removeprefix(STANDARD_MEMBER_ROLE_PREFIX)
        if candidate in STANDARD_MEMBER_TASK_TYPES:
            return candidate
    return None


def member_role_name_from_owner_agent_id(owner_agent_id: str | None) -> str | None:
    if owner_agent_id is None:
        return None
    if owner_agent_id in {"", "main", "unassigned"}:
        return None
    for role_name in sorted(STANDARD_MEMBER_ROLE_NAMES.values(), key=len, reverse=True):
        if owner_agent_id == role_name or owner_agent_id.startswith(f"{role_name}-"):
            return role_name
    return None


def member_task_type_from_owner_agent_id(owner_agent_id: str | None) -> str | None:
    role_name = member_role_name_from_owner_agent_id(owner_agent_id)
    return member_task_type_from_role_name(role_name)


def validate_member_owner_identifier(owner_agent_id: str, *, field_name: str) -> None:
    if member_role_name_from_owner_agent_id(owner_agent_id) is None:
        raise ValueError(
            f"{field_name} '{owner_agent_id}' must be a canonical member role name or a role-matched member instance"
        )


def normalize_member_identity(state: dict[str, Any]) -> None:
    task_type = state.get("task_type")
    member_role_name = state.get("member_role_name")
    owner_agent_id = state.get("owner_agent_id")

    if task_type is not None:
        canonical_member_role_name(task_type)

    if member_role_name not in {None, "", "unassigned"}:
        inferred_task_type = member_task_type_from_role_name(member_role_name)
        if inferred_task_type is None:
            raise ValueError(
                f"member_role_name '{member_role_name}' must be one of: "
                f"{', '.join(sorted(STANDARD_MEMBER_ROLE_NAMES.values()))}"
            )
        if task_type is None:
            task_type = inferred_task_type
            state["task_type"] = task_type
        elif task_type != inferred_task_type:
            raise ValueError(
                f"member_role_name '{member_role_name}' does not match task_type '{task_type}'"
            )

    if owner_agent_id not in {None, "", "unassigned", "main"}:
        inferred_task_type = member_task_type_from_owner_agent_id(owner_agent_id)
        if inferred_task_type is None:
            raise ValueError(
                f"owner_agent_id '{owner_agent_id}' must be 'main', 'unassigned', a canonical member role name, "
                "or a role-matched member instance like 'member-coding-2'"
            )
        if task_type is None:
            task_type = inferred_task_type
            state["task_type"] = task_type
        elif task_type != inferred_task_type:
            raise ValueError(
                f"owner_agent_id '{owner_agent_id}' does not match task_type '{task_type}'"
            )

    if task_type is not None:
        canonical_role = canonical_member_role_name(task_type)
        if member_role_name in {None, "", "unassigned"}:
            state["member_role_name"] = canonical_role
        elif member_role_name != canonical_role:
            raise ValueError(
                f"member_role_name '{member_role_name}' does not match task_type '{task_type}'"
            )
        if owner_agent_id in {None, "", "unassigned", "main"}:
            state["owner_agent_id"] = canonical_role
        elif member_role_name_from_owner_agent_id(owner_agent_id) != canonical_role:
            raise ValueError(
                f"owner_agent_id '{owner_agent_id}' does not match task_type '{task_type}'"
            )
    elif member_role_name not in {None, "", "unassigned"}:
        raise ValueError("member_role_name requires a supported task_type")


def validate_state_payload(state: dict[str, Any]) -> None:
    normalize_member_identity(state)
    validate_phase(state.get("phase"))
    validate_status(state.get("status"))


def default_discussion_state(discussion_id: str) -> dict[str, Any]:
    now = utc_now()
    return {
        "discussion_id": discussion_id,
        "mode": "consult",
        "status": "open",
        "title": "待补充",
        "context": "",
        "initiator": "待补充",
        "participants": [],
        "linked_task_ids": [],
        "resolution_summary": "",
        "created_at": now,
        "updated_at": now,
        "last_message_at": None,
        "resolved_at": None,
    }


def normalize_discussion_state(state: dict[str, Any]) -> None:
    validate_discussion_mode(state.get("mode"))
    validate_discussion_status(state.get("status"))
    initiator = state.get("initiator")
    if not initiator:
        raise ValueError("discussion initiator is required")
    validate_member_owner_identifier(initiator, field_name="initiator")

    participants = list(state.get("participants") or [])
    if initiator not in participants:
        participants.insert(0, initiator)
    deduped: list[str] = []
    for participant in participants:
        validate_member_owner_identifier(participant, field_name="participant")
        if participant not in deduped:
            deduped.append(participant)
    if len(deduped) < 2:
        raise ValueError("discussion participants must contain at least two member agents")
    state["participants"] = deduped
    state["linked_task_ids"] = list(dict.fromkeys(state.get("linked_task_ids") or []))


def validate_discussion_payload(state: dict[str, Any]) -> None:
    normalize_discussion_state(state)


def ensure_discussion_exists(state_root: Path, discussion_id: str) -> None:
    if not discussion_dir(state_root, discussion_id).exists():
        raise FileNotFoundError(f"Discussion directory not found: {discussion_dir(state_root, discussion_id)}")


def ensure_task_exists(state_root: Path, task_id: str) -> None:
    if not task_dir(state_root, task_id).exists():
        raise FileNotFoundError(f"Task directory not found: {task_dir(state_root, task_id)}")


def load_ledger(state_root: Path) -> dict[str, Any]:
    ledger = load_json(state_root / "ledger.json", default_ledger())
    if "tasks" not in ledger:
        ledger["tasks"] = {}
    if "discussions" not in ledger:
        ledger["discussions"] = {}
    return ledger


def save_ledger(state_root: Path, ledger: dict[str, Any]) -> None:
    ledger.setdefault("tasks", {})
    ledger.setdefault("discussions", {})
    ledger["updated_at"] = utc_now()
    write_json(state_root / "ledger.json", ledger)


def load_state(state_root: Path, task_id: str) -> dict[str, Any]:
    ensure_task_exists(state_root, task_id)
    return load_json(task_file_map(state_root, task_id)["state"])


def load_discussion_state(state_root: Path, discussion_id: str) -> dict[str, Any]:
    ensure_discussion_exists(state_root, discussion_id)
    return load_json(discussion_file_map(state_root, discussion_id)["state"])


def save_state(state_root: Path, task_id: str, state: dict[str, Any]) -> None:
    state["updated_at"] = utc_now()
    write_json(task_file_map(state_root, task_id)["state"], state)


def save_discussion_state(state_root: Path, discussion_id: str, state: dict[str, Any]) -> None:
    state["updated_at"] = utc_now()
    write_json(discussion_file_map(state_root, discussion_id)["state"], state)


def load_steps(state_root: Path, task_id: str) -> dict[str, Any]:
    ensure_task_exists(state_root, task_id)
    default = {"task_id": task_id, "updated_at": utc_now(), "steps": []}
    return load_json(task_file_map(state_root, task_id)["steps"], default)


def save_steps(state_root: Path, task_id: str, steps_doc: dict[str, Any]) -> None:
    steps_doc["task_id"] = task_id
    steps_doc["updated_at"] = utc_now()
    write_json(task_file_map(state_root, task_id)["steps"], steps_doc)


def sync_task_to_ledger(
    state_root: Path,
    state: dict[str, Any],
    *,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    ledger = load_ledger(state_root)
    task_id = state["task_id"]
    entry = ledger["tasks"].get(task_id, default_ledger_task_entry(state_root, task_id))
    entry["child_task_ids"] = entry.get("child_task_ids", [])
    entry.update(
        {
            "task_id": task_id,
            "parent_task_id": state.get("parent_task_id"),
            "owner_agent_id": state.get("owner_agent_id"),
            "task_type": state.get("task_type"),
            "member_role_name": state.get("member_role_name"),
            "status": state.get("status"),
            "phase": state.get("phase"),
            "revision": state.get("revision"),
            "goal": state.get("goal"),
            "scope": state.get("scope"),
            "priority": state.get("priority"),
            "artifact_path": str(task_dir(state_root, task_id)),
            "updated_at": state.get("updated_at", utc_now()),
        }
    )
    if extra:
        entry.update(extra)
    ledger["tasks"][task_id] = entry

    parent_task_id = state.get("parent_task_id")
    if parent_task_id:
        parent_paths = task_file_map(state_root, parent_task_id)
        if not parent_paths["state"].exists():
            parent_entry = ledger["tasks"].get(parent_task_id)
            ensure_task_scaffold_if_missing(state_root, task_state_from_ledger_entry(parent_task_id, parent_entry))
        parent_entry = ledger["tasks"].get(parent_task_id, default_ledger_task_entry(state_root, parent_task_id))
        parent_entry["child_task_ids"] = parent_entry.get("child_task_ids", [])
        if task_id not in parent_entry["child_task_ids"]:
            parent_entry["child_task_ids"].append(task_id)
        parent_entry["task_id"] = parent_task_id
        ledger["tasks"][parent_task_id] = parent_entry

    save_ledger(state_root, ledger)
    return ledger


def default_ledger_discussion_entry(state_root: Path, discussion_id: str) -> dict[str, Any]:
    return {
        "discussion_id": discussion_id,
        "mode": "consult",
        "status": "open",
        "title": "待补充",
        "initiator": "待补充",
        "participants": [],
        "linked_task_ids": [],
        "resolution_summary": "",
        "artifact_path": str(discussion_dir(state_root, discussion_id)),
        "updated_at": utc_now(),
    }


def sync_discussion_to_ledger(
    state_root: Path,
    state: dict[str, Any],
    *,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    ledger = load_ledger(state_root)
    discussion_id = state["discussion_id"]
    entry = ledger["discussions"].get(discussion_id, default_ledger_discussion_entry(state_root, discussion_id))
    entry.update(
        {
            "discussion_id": discussion_id,
            "mode": state.get("mode"),
            "status": state.get("status"),
            "title": state.get("title"),
            "initiator": state.get("initiator"),
            "participants": list(state.get("participants") or []),
            "linked_task_ids": list(state.get("linked_task_ids") or []),
            "resolution_summary": state.get("resolution_summary") or "",
            "artifact_path": str(discussion_dir(state_root, discussion_id)),
            "updated_at": state.get("updated_at", utc_now()),
        }
    )
    if extra:
        entry.update(extra)
    ledger["discussions"][discussion_id] = entry
    save_ledger(state_root, ledger)
    return ledger


def ensure_task_scaffold(state_root: Path, state: dict[str, Any]) -> dict[str, Path]:
    task_id = state["task_id"]
    task_paths = task_file_map(state_root, task_id)
    task_dir(state_root, task_id).mkdir(parents=True, exist_ok=True)
    internal_dir(state_root, task_id).mkdir(parents=True, exist_ok=True)

    dependencies = state.get("dependencies") or []
    acceptance = state.get("acceptance_criteria") or []
    dependency_lines = "\n".join(f"- {item}" for item in dependencies) or "- 无"
    acceptance_lines = "\n".join(f"- {item}" for item in acceptance) or "- 待补充"

    default_files = {
        "task": task_md_from_state(state),
        "analysis": (
            f"# 任务 {task_id} 分析\n\n"
            "## 目标理解\n\n"
            "待补充。\n\n"
            "## 约束与假设\n\n"
            "待补充。\n\n"
            "## 风险与未知项\n\n"
            "待补充。\n"
        ),
        "design": (
            f"# 任务 {task_id} 设计\n\n"
            "## 方案概述\n\n"
            "待补充。\n\n"
            "## 关键取舍\n\n"
            "待补充。\n\n"
            "## 边界与依赖\n\n"
            "待补充。\n"
        ),
        "plan": (
            f"# 任务 {task_id} 计划\n\n"
            "## 步骤列表\n\n"
            "1. 待补充。\n\n"
            "## 当前重点\n\n"
            "待补充。\n"
        ),
        "progress": "",
        "result": (
            f"# 任务 {task_id} 结果\n\n"
            "## 完成情况\n\n"
            "待补充。\n\n"
            "## 产出物\n\n"
            "待补充。\n\n"
            "## 后续建议\n\n"
            "待补充。\n"
        ),
        "brief": (
            f"# Task {task_id} Brief\n\n"
            f"- Goal: {state.get('goal') or 'TBD'}\n"
            f"- Scope: {state.get('scope') or 'TBD'}\n"
            f"- Phase: {state.get('phase') or 'received'}\n"
            f"- Priority: {state.get('priority') or 'medium'}\n"
        ),
        "handoff": (
            f"# Task {task_id} Handoff\n\n"
            "- Current checkpoint: pending completion detail\n"
            "- Resume guidance: record the latest milestone, next owner, and verification status before resuming\n"
        ),
    }

    for name, content in default_files.items():
        path = task_paths[name]
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")

    if not task_paths["state"].exists():
        write_json(task_paths["state"], state)
    if not task_paths["steps"].exists():
        write_json(task_paths["steps"], {"task_id": task_id, "updated_at": utc_now(), "steps": []})
    if not task_paths["events"].exists():
        task_paths["events"].touch()

    return task_paths


def ensure_discussion_scaffold(state_root: Path, state: dict[str, Any]) -> dict[str, Path]:
    discussion_id = state["discussion_id"]
    paths = discussion_file_map(state_root, discussion_id)
    discussion_dir(state_root, discussion_id).mkdir(parents=True, exist_ok=True)

    participants = ", ".join(state.get("participants") or []) or "TBD"
    linked_tasks = ", ".join(state.get("linked_task_ids") or []) or "none"
    default_files = {
        "topic": (
            f"# Discussion {discussion_id} Topic\n\n"
            f"- Mode: {state.get('mode') or 'consult'}\n"
            f"- Initiator: {state.get('initiator') or 'TBD'}\n"
            f"- Participants: {participants}\n"
            f"- Linked tasks: {linked_tasks}\n"
            f"- Topic: {state.get('title') or 'TBD'}\n\n"
            "## Context\n\n"
            f"{state.get('context') or 'TBD'}\n"
        ),
        "decision": (
            f"# Discussion {discussion_id} Decision\n\n"
            "Pending resolution.\n"
        ),
    }
    for name, content in default_files.items():
        path = paths[name]
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")

    if not paths["state"].exists():
        write_json(paths["state"], state)
    if not paths["messages"].exists():
        paths["messages"].touch()
    return paths


def verify_task_integrity(state_root: Path, task_id: str) -> list[str]:
    """Return names of files that should exist for *task_id* but are missing."""
    paths = task_file_map(state_root, task_id)
    core = ["task", "state", "progress", "handoff", "brief", "events", "steps"]
    return [name for name in core if not paths[name].exists()]


def ensure_task_scaffold_if_missing(state_root: Path, state: dict[str, Any]) -> dict[str, Path]:
    task_paths = task_file_map(state_root, state["task_id"])
    if task_paths["state"].exists():
        return task_paths
    return ensure_task_scaffold(state_root, state)


def linked_discussions_for_task(state_root: Path, task_id: str) -> list[dict[str, Any]]:
    ledger = load_ledger(state_root)
    discussions = [
        discussion
        for discussion in ledger.get("discussions", {}).values()
        if task_id in (discussion.get("linked_task_ids") or [])
    ]
    discussions.sort(key=lambda item: item.get("updated_at", ""), reverse=True)
    return discussions


def parse_key_value_pairs(pairs: list[str] | None) -> dict[str, Any]:
    parsed: dict[str, Any] = {}
    if not pairs:
        return parsed
    for pair in pairs:
        if "=" not in pair:
            raise ValueError(f"Expected key=value, got: {pair}")
        key, raw_value = pair.split("=", 1)
        parsed[key] = parse_scalar(raw_value)
    return parsed


def parse_scalar(raw_value: str) -> Any:
    stripped = raw_value.strip()
    if stripped == "":
        return ""
    try:
        return json.loads(stripped)
    except json.JSONDecodeError:
        return raw_value


def read_jsonl_tail(path: Path, limit: int) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        rows.append(json.loads(line))
    if limit <= 0:
        return rows
    return rows[-limit:]


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def read_text_source(
    *,
    body: str | None = None,
    body_file: str | None = None,
    use_stdin: bool = False,
) -> str:
    provided = sum(bool(item) for item in [body is not None, body_file is not None, use_stdin])
    if provided == 0:
        raise ValueError("Provide one of --body, --body-file, or --stdin")
    if provided > 1:
        raise ValueError("Use only one of --body, --body-file, or --stdin")
    if body is not None:
        return body
    if body_file is not None:
        return Path(body_file).expanduser().resolve().read_text(encoding="utf-8")
    return sys.stdin.read()


def render_bullet_list(items: list[str], fallback: str) -> str:
    if not items:
        return fallback
    return "\n".join(f"- {item}" for item in items)


def task_md_from_state(state: dict[str, Any], *, extra_notes: str | None = None) -> str:
    dependencies = render_bullet_list(state.get("dependencies") or [], "- 无")
    acceptance = render_bullet_list(state.get("acceptance_criteria") or [], "- 待补充")
    lines = [
        f"# 任务 {state['task_id']}",
        "",
        "## 目标",
        "",
        state.get("goal") or "待补充",
        "",
        "## 范围",
        "",
        state.get("scope") or "待补充",
        "",
        "## 当前状态",
        "",
        f"- 状态：{state.get('status') or '未知'}",
        f"- 阶段：{state.get('phase') or '未知'}",
        f"- 修订版本：{state.get('revision') or 1}",
        f"- 当前步骤：{state.get('current_step_id') or '无'}",
        f"- 负责人：{state.get('owner_agent_id') or '未知'}",
        f"- 任务类型：{state.get('task_type') or '无'}",
        f"- 成员角色：{state.get('member_role_name') or '无'}",
        f"- 优先级：{state.get('priority') or '未知'}",
        "",
        "## 依赖",
        "",
        dependencies,
        "",
        "## 验收标准",
        "",
        acceptance,
    ]
    if extra_notes:
        lines.extend(["", "## 备注", "", extra_notes.strip()])
    return "\n".join(lines).rstrip() + "\n"


def sync_task_doc_with_state(state_root: Path, task_id: str, state: dict[str, Any], *, extra_notes: str | None = None) -> None:
    write_text(task_file_map(state_root, task_id)["task"], task_md_from_state(state, extra_notes=extra_notes))


def persist_state_snapshot(
    state_root: Path,
    task_id: str,
    state: dict[str, Any],
    *,
    sync_task_doc: bool = True,
    task_notes: str | None = None,
) -> None:
    validate_state_payload(state)
    save_state(state_root, task_id, state)
    if sync_task_doc:
        sync_task_doc_with_state(state_root, task_id, state, extra_notes=task_notes)
    sync_task_to_ledger(state_root, state)


def persist_discussion_snapshot(state_root: Path, discussion_id: str, state: dict[str, Any]) -> None:
    validate_discussion_payload(state)
    save_discussion_state(state_root, discussion_id, state)
    sync_discussion_to_ledger(state_root, state)


def default_artifact_title(task_id: str, artifact: str) -> str:
    titles = {
        "task": f"# 任务 {task_id}",
        "analysis": f"# 任务 {task_id} 分析",
        "design": f"# 任务 {task_id} 设计",
        "plan": f"# 任务 {task_id} 计划",
        "result": f"# 任务 {task_id} 结果",
        "brief": f"# Task {task_id} Brief",
        "handoff": f"# Task {task_id} Handoff",
    }
    return titles[artifact]


def render_bullet_block(items: list[str], *, fallback: str) -> str:
    if not items:
        return fallback
    return "\n".join(f"- {item}" for item in items)


def render_numbered_block(items: list[str], *, fallback: str) -> str:
    if not items:
        return fallback
    return "\n".join(f"{index}. {item}" for index, item in enumerate(items, start=1))


def transition_events(
    task_id: str,
    previous_state: dict[str, Any],
    next_state: dict[str, Any],
    *,
    ts: str,
) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    if previous_state.get("phase") != next_state.get("phase"):
        events.append(
            {
                "ts": ts,
                "type": "phase_changed",
                "task_id": task_id,
                "from_phase": previous_state.get("phase"),
                "to_phase": next_state.get("phase"),
                "status": next_state.get("status"),
                "revision": next_state.get("revision"),
            }
        )
    if previous_state.get("status") != next_state.get("status"):
        events.append(
            {
                "ts": ts,
                "type": "status_changed",
                "task_id": task_id,
                "from_status": previous_state.get("status"),
                "to_status": next_state.get("status"),
                "phase": next_state.get("phase"),
                "revision": next_state.get("revision"),
            }
        )
    if previous_state.get("revision") != next_state.get("revision"):
        events.append(
            {
                "ts": ts,
                "type": "revision_changed",
                "task_id": task_id,
                "from_revision": previous_state.get("revision"),
                "to_revision": next_state.get("revision"),
                "phase": next_state.get("phase"),
                "status": next_state.get("status"),
            }
        )
    return events


def append_transition_events(
    events_path: Path,
    task_id: str,
    previous_state: dict[str, Any],
    next_state: dict[str, Any],
    *,
    ts: str,
) -> None:
    for payload in transition_events(task_id, previous_state, next_state, ts=ts):
        append_jsonl(events_path, payload)


def persist_artifact_update(
    state_root: Path,
    task_id: str,
    *,
    state: dict[str, Any],
    artifact: str,
    content: str,
    event_type: str,
    progress_note: str | None = None,
) -> None:
    paths = task_file_map(state_root, task_id)
    now = utc_now()
    previous_state = load_state(state_root, task_id)
    write_text(paths[artifact], content)
    persist_state_snapshot(
        state_root,
        task_id,
        state,
        sync_task_doc=artifact != "task",
    )
    append_transition_events(paths["events"], task_id, previous_state, state, ts=now)
    append_jsonl(
        paths["events"],
        {
            "ts": now,
            "type": event_type,
            "task_id": task_id,
            "artifact": artifact,
            "phase": state.get("phase"),
            "status": state.get("status"),
            "revision": state.get("revision"),
        },
    )
    if progress_note:
        append_progress_log(paths["progress"], progress_note, ts=now)
