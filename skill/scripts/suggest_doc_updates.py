#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

from orchestrator_common import ensure_task_exists, load_json, read_text_source, resolve_state_root, task_file_map

MODE_DOC_KEYWORDS = {
    "skill": {
        "analysis": [
            "分析",
            "需求",
            "目标",
            "范围",
            "约束",
            "假设",
            "风险",
            "problem",
            "scope",
            "assumption",
            "risk",
        ],
        "design": [
            "设计",
            "架构",
            "结构",
            "状态",
            "artifact",
            "接口",
            "schema",
            "协议",
            "流程",
            "lifecycle",
        ],
        "skill": [
            "skill",
            "技能",
            "SKILL.md",
            "用法",
            "规则",
            "主agent",
            "子agent",
            "prompt",
        ],
        "protocol": [
            "protocol",
            "agent-protocol",
            "协议",
            "中断",
            "恢复",
            "checkpoint",
            "聊天记录",
            "ai-chat",
            "流程",
        ],
        "tests": [
            "测试",
            "test",
            "unittest",
            "回归",
            "验证",
            "coverage",
        ],
    },
    "task": {
        "task": [
            "任务",
            "goal",
            "scope",
            "范围",
            "优先级",
            "验收",
            "acceptance",
            "owner",
        ],
        "analysis": [
            "分析",
            "需求",
            "约束",
            "假设",
            "风险",
            "unknown",
            "problem",
            "scope",
        ],
        "design": [
            "设计",
            "架构",
            "接口",
            "边界",
            "artifact",
            "schema",
            "流程",
            "方案",
        ],
        "plan": [
            "计划",
            "步骤",
            "step",
            "milestone",
            "排期",
            "当前重点",
            "next",
        ],
        "result": [
            "结果",
            "汇报",
            "总结",
            "report",
            "output",
            "完成情况",
        ],
        "brief": [
            "brief",
            "internal",
            "context",
            "摘要",
            "内部说明",
        ],
        "handoff": [
            "handoff",
            "接力",
            "resume",
            "恢复",
            "交接",
            "checkpoint",
            "中断",
        ],
        "steps": [
            "steps",
            "step",
            "步骤",
            "task list",
            "执行项",
            "todo",
        ],
    },
}

TASK_PHASE_REQUIRED_DOCS = {
    "received": {"task", "brief", "handoff"},
    "analysis": {"task", "analysis", "brief", "handoff"},
    "design": {"task", "analysis", "design", "brief", "handoff"},
    "planning": {"task", "analysis", "design", "plan", "steps", "brief", "handoff"},
    "executing": {"task", "analysis", "design", "plan", "steps", "brief", "handoff"},
    "reporting": {"task", "analysis", "design", "plan", "result", "steps", "brief", "handoff"},
    "completed": {"task", "analysis", "design", "plan", "result", "steps", "brief", "handoff"},
    "interrupted": {"task", "analysis", "design", "plan", "steps", "brief", "handoff"},
    "revising": {"task", "analysis", "design", "plan", "steps", "brief", "handoff"},
}
TASK_PLACEHOLDERS = {
    "task": ["待补充"],
    "analysis": ["待补充。"],
    "design": ["待补充。"],
    "plan": ["待补充执行步骤。", "1. 待补充。", "待补充。"],
    "result": ["待补充。"],
    "brief": ["TBD", "待补充"],
    "handoff": ["pending completion detail", "record the latest milestone, next owner, and verification status before resuming"],
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Suggest which skill documents may need refreshing after a new chat instruction.",
    )
    parser.add_argument("--state-root", help="Path to orchestrator-state for task-aware suggestions")
    parser.add_argument("--mode", choices=sorted(MODE_DOC_KEYWORDS.keys()), default="skill", help="Document suggestion mode")
    parser.add_argument("--task-id", help="Task ID for task-aware suggestions")
    parser.add_argument("--message", help="Inline message")
    parser.add_argument("--message-file", help="Read message from file")
    parser.add_argument("--stdin", action="store_true", help="Read message from stdin")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output")
    return parser


def task_doc_staleness(state_root: Path, task_id: str) -> dict[str, list[str]]:
    ensure_task_exists(state_root, task_id)
    paths = task_file_map(state_root, task_id)
    state = load_json(paths["state"])
    required_docs = TASK_PHASE_REQUIRED_DOCS.get(state.get("phase"), {"task"})
    reasons: dict[str, list[str]] = defaultdict(list)

    for doc_name in MODE_DOC_KEYWORDS["task"]:
        if doc_name == "steps":
            if doc_name not in required_docs:
                continue
            if not paths["steps"].exists():
                reasons[doc_name].append("artifact missing")
                continue
            steps_doc = load_json(paths["steps"], {"task_id": task_id, "steps": []})
            if not steps_doc.get("steps"):
                reasons[doc_name].append("steps list is empty for current phase")
            continue

        path = paths[doc_name]
        if not path.exists():
            reasons[doc_name].append("artifact missing")
            continue
        text = path.read_text(encoding="utf-8")
        if doc_name == "task" and "## 当前状态" not in text:
            reasons[doc_name].append("task document missing current state section")
        if doc_name in required_docs:
            placeholders = TASK_PLACEHOLDERS.get(doc_name, [])
            if any(marker in text for marker in placeholders):
                if doc_name == "handoff":
                    reasons[doc_name].append("handoff information is incomplete")
                else:
                    reasons[doc_name].append("artifact still contains placeholder content")
    return reasons


def detect_doc_impacts(message: str, *, mode: str, state_root: Path | None = None, task_id: str | None = None) -> dict:
    lowered = message.lower()
    reasons: dict[str, list[str]] = defaultdict(list)
    suggested_docs: list[str] = []
    doc_keywords = MODE_DOC_KEYWORDS[mode]

    for doc_name, keywords in doc_keywords.items():
        for keyword in keywords:
            if keyword.lower() in lowered:
                reasons[doc_name].append(f"matched keyword: {keyword}")
        if reasons[doc_name]:
            suggested_docs.append(doc_name)

    if "文档" in message or "docs" in lowered or "documentation" in lowered:
        generic_targets = ["skill", "protocol"] if mode == "skill" else ["analysis", "design", "plan", "result"]
        for doc_name in generic_targets:
            if doc_name in doc_keywords and doc_name not in suggested_docs:
                suggested_docs.append(doc_name)
                reasons[doc_name].append("generic documentation mention")

    if mode == "task" and state_root and task_id:
        stale_reasons = task_doc_staleness(state_root, task_id)
        for doc_name, doc_reasons in stale_reasons.items():
            reasons[doc_name].extend(doc_reasons)
            if doc_name not in suggested_docs:
                suggested_docs.append(doc_name)

    payload = {
        "mode": mode,
        "message": message,
        "suggested_docs": suggested_docs,
        "doc_flags": {doc_name: doc_name in suggested_docs for doc_name in doc_keywords},
        "reasons": {doc_name: reasons.get(doc_name, []) for doc_name in doc_keywords},
    }
    if task_id:
        payload["task_id"] = task_id
    return payload


def main() -> int:
    args = build_parser().parse_args()
    message = read_text_source(body=args.message, body_file=args.message_file, use_stdin=args.stdin).strip()
    state_root = resolve_state_root(args.state_root) if args.mode == "task" and args.task_id else None
    payload = detect_doc_impacts(message, mode=args.mode, state_root=state_root, task_id=args.task_id)
    if args.pretty:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(json.dumps(payload, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
