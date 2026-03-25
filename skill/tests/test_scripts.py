from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
SCRIPT_DIR = ROOT_DIR / "scripts"
INSTALL_SCRIPT = ROOT_DIR / "install_skill.py"
SKILL_MIRROR_DIR = ROOT_DIR / "skills" / "my-team"


class ScriptCliTests(unittest.TestCase):
    maxDiff = None

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.workspace = Path(self.temp_dir.name) / ".my-team"
        self.workspace.mkdir(parents=True, exist_ok=True)
        self.state_root = self.workspace / "orchestrator-state"

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def run_script(
        self,
        script_name: str,
        *args: str,
        workspace: Path | None = None,
        input_text: str | None = None,
    ) -> subprocess.CompletedProcess[str]:
        command = [
            sys.executable,
            str(SCRIPT_DIR / script_name),
            *args,
            "--state-root",
            str(self.state_root),
        ]
        if workspace is not None:
            command.extend(["--workspace", str(workspace)])
        return subprocess.run(
            command,
            text=True,
            input=input_text,
            capture_output=True,
            check=True,
        )

    def run_chat_script(
        self,
        role: str,
        *args: str,
        input_text: str | None = None,
    ) -> subprocess.CompletedProcess[str]:
        command = [
            sys.executable,
            str(SCRIPT_DIR / "log_chat_turn.py"),
            role,
            "--workspace",
            str(self.workspace),
            *args,
        ]
        return subprocess.run(
            command,
            text=True,
            input=input_text,
            capture_output=True,
            check=True,
        )

    def run_install_script(self, *args: str) -> subprocess.CompletedProcess[str]:
        command = [
            sys.executable,
            str(INSTALL_SCRIPT),
            *args,
        ]
        return subprocess.run(
            command,
            text=True,
            capture_output=True,
            check=True,
        )

    def run_install_script_allow_failure(self, *args: str) -> subprocess.CompletedProcess[str]:
        command = [
            sys.executable,
            str(INSTALL_SCRIPT),
            *args,
        ]
        return subprocess.run(
            command,
            text=True,
            capture_output=True,
            check=False,
        )

    def run_script_allow_failure(
        self,
        script_name: str,
        *args: str,
        workspace: Path | None = None,
        input_text: str | None = None,
    ) -> subprocess.CompletedProcess[str]:
        command = [
            sys.executable,
            str(SCRIPT_DIR / script_name),
            *args,
            "--state-root",
            str(self.state_root),
        ]
        if workspace is not None:
            command.extend(["--workspace", str(workspace)])
        return subprocess.run(
            command,
            text=True,
            input=input_text,
            capture_output=True,
            check=False,
        )

    def task_dir(self, task_id: str) -> Path:
        return self.state_root / "tasks" / task_id

    def discussion_dir(self, discussion_id: str) -> Path:
        return self.state_root / "discussions" / discussion_id

    def read_json(self, path: Path) -> dict:
        return json.loads(path.read_text(encoding="utf-8"))

    def read_text(self, path: Path) -> str:
        return path.read_text(encoding="utf-8")

    def task_artifact_paths(self, task_id: str) -> list[Path]:
        task_dir = self.task_dir(task_id)
        return [
            task_dir / "task.md",
            task_dir / "analysis.md",
            task_dir / "design.md",
            task_dir / "plan.md",
            task_dir / "progress.log",
            task_dir / "result.md",
            task_dir / "internal" / "brief.en.md",
            task_dir / "internal" / "handoff.en.md",
            task_dir / "state.json",
            task_dir / "steps.json",
            task_dir / "events.jsonl",
        ]

    def test_init_task_creates_dual_track_artifacts(self) -> None:
        self.run_script(
            "init_task.py",
            "T-001",
            "--goal",
            "初始化测试任务",
            "--scope",
            "验证基础脚手架",
            "--acceptance-criterion",
            "生成中英文分层文件",
        )

        task_dir = self.task_dir("T-001")
        for expected_path in self.task_artifact_paths("T-001"):
            self.assertTrue(expected_path.exists(), f"Missing expected file: {expected_path}")

        state = self.read_json(task_dir / "state.json")
        self.assertEqual(state["goal"], "初始化测试任务")
        self.assertEqual(state["phase"], "received")

        ledger = self.read_json(self.state_root / "ledger.json")
        self.assertIn("T-001", ledger["tasks"])
        self.assertEqual(ledger["tasks"]["T-001"]["goal"], "初始化测试任务")
        self.assertIn("任务已创建", self.read_text(task_dir / "progress.log"))

    def test_write_artifact_prepends_default_heading_for_subheading_input(self) -> None:
        self.run_script(
            "init_task.py",
            "T-002",
            "--goal",
            "验证默认标题补齐",
        )

        self.run_script(
            "write_artifact.py",
            "T-002",
            "analysis",
            "--stdin",
            input_text="## 目标理解\n\n验证默认标题补齐。\n",
        )

        analysis_text = self.read_text(self.task_dir("T-002") / "analysis.md")
        self.assertTrue(analysis_text.startswith("# 任务 T-002 分析\n\n## 目标理解"))
        self.assertIn("验证默认标题补齐。", analysis_text)

    def test_structured_writers_and_checkpoint_flow(self) -> None:
        self.run_script(
            "init_task.py",
            "T-003",
            "--goal",
            "验证结构化脚本",
            "--scope",
            "analysis/design/plan/result/checkpoint 全链路",
        )

        self.run_script(
            "write_analysis.py",
            "T-003",
            "--goal-understanding",
            "确认结构化分析模板能生成中文文档。",
            "--constraint",
            "保持用户文档为中文",
            "--risk",
            "字段过少会限制表达",
        )
        self.run_script(
            "write_design.py",
            "T-003",
            "--solution-summary",
            "为每类文档提供独立的结构化写入脚本。",
            "--decision",
            "将 analysis/design/plan/result 拆为独立 CLI",
        )
        self.run_script(
            "write_plan.py",
            "T-003",
            "--step",
            "S-001|生成分析模板|completed",
            "--step",
            "S-002|生成设计模板|completed",
            "--step",
            "S-003|生成计划和结果模板|in_progress",
            "--current-focus",
            "同步验证 steps.json 与 plan.md。",
            "--sync-steps",
        )
        self.run_script(
            "checkpoint_task.py",
            "T-003",
            "--phase",
            "planning",
            "--bump-revision",
            "--handoff-stdin",
            "--progress-note",
            "已记录 checkpoint。",
            workspace=self.workspace,
            input_text=(
                "# Task T-003 Handoff\n\n"
                "- Current checkpoint: templates written.\n"
                "- Resume guidance: complete the result document next.\n"
            ),
        )
        self.run_script(
            "write_result.py",
            "T-003",
            "--summary",
            "结构化文档与 checkpoint 流程验证完成。",
            "--completed",
            "analysis 模板可写入",
            "--completed",
            "design 模板可写入",
            "--completed",
            "plan 模板可同步 steps",
        )

        task_dir = self.task_dir("T-003")
        self.assertIn("## 目标理解", self.read_text(task_dir / "analysis.md"))
        self.assertIn("## 关键决策", self.read_text(task_dir / "design.md"))
        self.assertIn("## 步骤列表", self.read_text(task_dir / "plan.md"))
        self.assertIn("## 完成情况", self.read_text(task_dir / "result.md"))
        self.assertIn("Resume guidance", self.read_text(task_dir / "internal" / "handoff.en.md"))

        state = self.read_json(task_dir / "state.json")
        self.assertEqual(state["status"], "completed")
        self.assertEqual(state["phase"], "completed")
        self.assertEqual(state["revision"], 2)

        steps = self.read_json(task_dir / "steps.json")
        self.assertEqual([step["step_id"] for step in steps["steps"]], ["S-001", "S-002", "S-003"])
        self.assertEqual(steps["steps"][2]["status"], "in_progress")

        summary = self.run_script("render_summary.py", "--task-id", "T-003").stdout
        self.assertIn("任务摘要 T-003", summary)
        self.assertIn("修订版本：2", summary)
        self.assertIn("Workspace / Resume", summary)
        self.assertIn("resume_owner", summary)
        self.assertIn("checkpoint_task.py updated T-003 to phase planning and status in_progress", self.read_text(self.workspace / "MEMORY.md"))
        self.assertIn("checkpoint recorded for T-003", self.read_text(self.workspace / "SESSIONS" / "current.md"))

    def test_task_md_syncs_with_state_changes_and_parent_placeholder_is_shaped(self) -> None:
        self.run_script(
            "init_task.py",
            "T-006",
            "--goal",
            "验证 task.md 同步",
            "--parent-task-id",
            "T-PARENT",
        )
        self.run_script(
            "update_state.py",
            "T-006",
            "--phase",
            "analysis",
            "--status",
            "revising",
            "--goal",
            "已更新目标",
        )

        task_text = self.read_text(self.task_dir("T-006") / "task.md")
        self.assertIn("## 当前状态", task_text)
        self.assertIn("已更新目标", task_text)
        self.assertIn("- 状态：revising", task_text)
        self.assertIn("- 阶段：analysis", task_text)

        parent_dir = self.task_dir("T-PARENT")
        self.assertTrue(parent_dir.exists())
        for expected_path in self.task_artifact_paths("T-PARENT"):
            self.assertTrue(expected_path.exists(), f"Missing expected parent file: {expected_path}")

        ledger = self.read_json(self.state_root / "ledger.json")
        parent_entry = ledger["tasks"]["T-PARENT"]
        for key in [
            "task_id",
            "parent_task_id",
            "owner_agent_id",
            "status",
            "phase",
            "revision",
            "goal",
            "scope",
            "priority",
            "artifact_path",
            "updated_at",
            "child_task_ids",
        ]:
            self.assertIn(key, parent_entry)
        self.assertIn("T-006", parent_entry["child_task_ids"])

        summary = self.run_script("render_summary.py", "--task-id", "T-006").stdout
        self.assertIn("父任务：T-PARENT", summary)

    def test_parent_task_directory_is_created_for_multiple_children(self) -> None:
        parent_task_id = "T-PARENT-2"
        self.run_script(
            "init_task.py",
            "T-011",
            "--goal",
            "第一个子任务",
            "--parent-task-id",
            parent_task_id,
        )

        parent_dir = self.task_dir(parent_task_id)
        self.assertTrue(parent_dir.exists())
        for expected_path in self.task_artifact_paths(parent_task_id):
            self.assertTrue(expected_path.exists(), f"Missing expected parent file: {expected_path}")

        self.run_script(
            "init_task.py",
            "T-012",
            "--goal",
            "第二个子任务",
            "--parent-task-id",
            parent_task_id,
        )

        for task_id in [parent_task_id, "T-011", "T-012"]:
            self.assertTrue(self.task_dir(task_id).exists(), f"Missing task directory: {task_id}")
            for expected_path in self.task_artifact_paths(task_id):
                self.assertTrue(expected_path.exists(), f"Missing expected file for {task_id}: {expected_path}")

        ledger = self.read_json(self.state_root / "ledger.json")
        parent_entry = ledger["tasks"][parent_task_id]
        self.assertEqual(parent_entry["child_task_ids"], ["T-011", "T-012"])
        self.assertEqual(ledger["tasks"]["T-011"]["parent_task_id"], parent_task_id)
        self.assertEqual(ledger["tasks"]["T-012"]["parent_task_id"], parent_task_id)

    def test_revise_task_bumps_revision_and_preserves_completed_steps(self) -> None:
        self.run_script("init_task.py", "T-007", "--goal", "验证修订流程")
        self.run_script(
            "write_plan.py",
            "T-007",
            "--step",
            "S-001|已完成旧步骤|completed",
            "--step",
            "S-002|待重排步骤|pending",
            "--current-focus",
            "先生成旧计划。",
            "--sync-steps",
        )
        self.run_script(
            "revise_task.py",
            "T-007",
            "--scope",
            "新范围",
            "--checkpoint-reason",
            "用户修改范围",
            "--progress-note",
            "已接受修订并重排计划。",
        )
        self.run_script(
            "write_plan.py",
            "T-007",
            "--step",
            "S-002|按新范围执行|pending",
            "--step",
            "S-003|补充校验|pending",
            "--current-focus",
            "按修订后的范围重排。",
            "--sync-steps",
        )

        state = self.read_json(self.task_dir("T-007") / "state.json")
        self.assertEqual(state["revision"], 2)
        self.assertEqual(state["phase"], "planning")

        steps = self.read_json(self.task_dir("T-007") / "steps.json")
        self.assertEqual([step["step_id"] for step in steps["steps"]], ["S-002", "S-003", "S-001"])
        self.assertEqual(steps["steps"][-1]["status"], "completed")

        events = [
            json.loads(line)
            for line in self.read_text(self.task_dir("T-007") / "events.jsonl").splitlines()
            if line.strip()
        ]
        event_types = [event["type"] for event in events]
        self.assertIn("checkpoint", event_types)
        self.assertIn("revision_accepted", event_types)

    def test_task_mode_doc_suggestions_can_use_artifact_state(self) -> None:
        self.run_script("init_task.py", "T-008", "--goal", "验证 artifact-aware refresh")
        self.run_script("update_state.py", "T-008", "--phase", "design")

        result = self.run_script(
            "suggest_doc_updates.py",
            "--mode",
            "task",
            "--task-id",
            "T-008",
            "--message",
            "继续执行",
        )
        payload = json.loads(result.stdout)
        self.assertEqual(payload["task_id"], "T-008")
        self.assertTrue(payload["doc_flags"]["task"])
        self.assertTrue(payload["doc_flags"]["analysis"])
        self.assertTrue(payload["doc_flags"]["design"])
        self.assertTrue(payload["doc_flags"]["brief"])
        self.assertTrue(payload["doc_flags"]["handoff"])

    def test_update_step_flow_updates_summary_and_reporting_phase(self) -> None:
        self.run_script(
            "init_task.py",
            "T-004",
            "--goal",
            "验证步骤流",
        )

        self.run_script("update_step.py", "T-004", "add", "--step-id", "S-001", "--title", "执行验证")
        self.run_script("update_step.py", "T-004", "start", "--step-id", "S-001")
        self.run_script(
            "append_event.py",
            "T-004",
            "interruption",
            "--reason",
            "用户调整优先级",
            "--progress-note",
            "收到中断，准备重排。",
        )
        self.run_script(
            "update_state.py",
            "T-004",
            "--revision",
            "2",
            "--phase",
            "planning",
            "--event-type",
            "revision_accepted",
        )
        self.run_script("update_step.py", "T-004", "complete", "--step-id", "S-001")

        state = self.read_json(self.task_dir("T-004") / "state.json")
        self.assertEqual(state["phase"], "reporting")
        self.assertEqual(state["revision"], 2)

        summary = self.run_script("render_summary.py", "--task-id", "T-004").stdout
        self.assertIn("[x] S-001 执行验证", summary)
        self.assertIn("revision_accepted", summary)
        self.assertIn("step_complete", summary)

    def test_log_chat_turn_appends_to_daily_ai_chat_markdown(self) -> None:
        self.run_chat_script(
            "user",
            "--date",
            "2026-03-23",
            "--time-label",
            "09:30:00",
            "--message",
            "请帮我整理今天的任务。",
        )
        self.run_chat_script(
            "main-agent",
            "--date",
            "2026-03-23",
            "--time-label",
            "09:30:12",
            "--message",
            "我先汇总当前任务，再给你一个执行顺序。",
        )

        log_path = self.workspace / "ai-chat" / "2026-03-23.md"
        content = self.read_text(log_path)
        self.assertTrue(log_path.exists())
        self.assertTrue(content.startswith("# 2026-03-23 聊天记录\n"))
        self.assertIn("## 09:30:00 用户", content)
        self.assertIn("请帮我整理今天的任务。", content)
        self.assertIn("## 09:30:12 主Agent", content)
        self.assertIn("我先汇总当前任务，再给你一个执行顺序。", content)
        self.assertEqual(content.count("# 2026-03-23 聊天记录"), 1)
        self.assertTrue((self.workspace / "TEAM.md").exists())
        self.assertTrue((self.workspace / "SESSIONS" / "current.md").exists())
        self.assertIn("main-agent chat turn logged", self.read_text(self.workspace / "SESSIONS" / "current.md"))

    def test_bootstrap_workspace_creates_long_lived_artifacts(self) -> None:
        self.run_script("bootstrap_workspace.py", workspace=self.workspace)

        self.assertTrue((self.workspace / "TEAM.md").exists())
        self.assertTrue((self.workspace / "MEMORY.md").exists())
        self.assertTrue((self.workspace / "USER_CONTEXT.md").exists())
        self.assertTrue((self.workspace / "INBOX.md").exists())
        self.assertTrue((self.workspace / "SESSIONS" / "current.md").exists())
        self.assertTrue((self.workspace / "ROLES" / "leader.md").exists())
        self.assertTrue((self.workspace / "ROLES" / "member-analysis.md").exists())
        self.assertTrue((self.workspace / "ROLES" / "member-testing.md").exists())

        user_context = self.read_text(self.workspace / "USER_CONTEXT.md")
        self.assertIn("skill_name: my-team", user_context)
        self.assertIn(str(self.state_root), user_context)

    def test_update_memory_appends_structured_entries(self) -> None:
        self.run_script("bootstrap_workspace.py", workspace=self.workspace)
        self.run_script(
            "update_memory.py",
            "--fact",
            "用户偏好中文汇报",
            "--decision",
            "默认先分配 member-analysis",
            "--preference",
            "及时反馈分配和完成情况",
            "--constraint",
            "team leader 不亲自写代码",
            workspace=self.workspace,
        )

        memory_text = self.read_text(self.workspace / "MEMORY.md")
        self.assertIn("source: update_memory.py", memory_text)
        self.assertIn("fact: 用户偏好中文汇报", memory_text)
        self.assertIn("decision: 默认先分配 member-analysis", memory_text)
        self.assertIn("preference: 及时反馈分配和完成情况", memory_text)
        self.assertIn("constraint: team leader 不亲自写代码", memory_text)
        session_text = self.read_text(self.workspace / "SESSIONS" / "current.md")
        self.assertIn("memory updated", session_text)

    def test_resume_readiness_reports_missing_and_ready_states(self) -> None:
        self.run_script("bootstrap_workspace.py", workspace=self.workspace)

        missing_result = self.run_script("resume_readiness.py", workspace=self.workspace)
        missing_payload = json.loads(missing_result.stdout)
        self.assertFalse(missing_payload["ready"])
        self.assertIn("ledger.json", missing_payload["missing_state_files"])
        self.assertEqual(missing_payload["resume_owner"], "team leader")
        self.assertEqual(missing_payload["current_task_id"], None)

        self.run_script("init_task.py", "T-090", "--goal", "验证恢复准备", "--scope", "workspace resume")
        ready_result = self.run_script("resume_readiness.py", workspace=self.workspace)
        ready_payload = json.loads(ready_result.stdout)
        self.assertTrue(ready_payload["ready"])
        self.assertEqual(ready_payload["current_task_id"], "T-090")
        self.assertEqual(ready_payload["resume_owner"], "team leader")
        self.assertEqual(ready_payload["missing_task_artifacts"], {})

    def test_suggest_doc_updates_returns_expected_flags(self) -> None:
        result = self.run_script(
            "suggest_doc_updates.py",
            "--mode",
            "skill",
            "--message",
            "请更新分析、设计、skill 文档，并补充测试和聊天记录规则。",
        )
        payload = json.loads(result.stdout)
        self.assertTrue(payload["doc_flags"]["analysis"])
        self.assertTrue(payload["doc_flags"]["design"])
        self.assertTrue(payload["doc_flags"]["skill"])
        self.assertTrue(payload["doc_flags"]["protocol"])
        self.assertTrue(payload["doc_flags"]["tests"])
        self.assertIn("analysis", payload["suggested_docs"])

    def test_suggest_doc_updates_task_mode_returns_task_level_flags(self) -> None:
        result = self.run_script(
            "suggest_doc_updates.py",
            "--mode",
            "task",
            "--message",
            "主agent要求你重做分析、设计、计划，并更新handoff和步骤状态。",
        )
        payload = json.loads(result.stdout)
        self.assertEqual(payload["mode"], "task")
        self.assertTrue(payload["doc_flags"]["analysis"])
        self.assertTrue(payload["doc_flags"]["design"])
        self.assertTrue(payload["doc_flags"]["plan"])
        self.assertTrue(payload["doc_flags"]["handoff"])
        self.assertTrue(payload["doc_flags"]["steps"])

    def test_record_doc_refresh_appends_jsonl_entry(self) -> None:
        self.run_script(
            "record_doc_refresh.py",
            "--message-summary",
            "收到一条需要刷新分析和设计的指令",
            "--considered-doc",
            "analysis",
            "--considered-doc",
            "design",
            "--updated-doc",
            "analysis",
            "--updated-doc",
            "design",
            "--status",
            "updated",
            "--note",
            "已同步分析与设计文档。",
        )

        log_path = self.state_root / "doc-refresh.jsonl"
        self.assertTrue(log_path.exists())
        lines = [line for line in self.read_text(log_path).splitlines() if line.strip()]
        self.assertEqual(len(lines), 1)
        payload = json.loads(lines[0])
        self.assertEqual(payload["status"], "updated")
        self.assertEqual(payload["considered_docs"], ["analysis", "design"])
        self.assertEqual(payload["updated_docs"], ["analysis", "design"])

    def test_record_doc_refresh_task_scope_appends_global_and_task_logs(self) -> None:
        self.run_script("init_task.py", "T-005", "--goal", "验证任务级文档刷新记录")
        self.run_script(
            "record_doc_refresh.py",
            "--scope",
            "task",
            "--task-id",
            "T-005",
            "--message-summary",
            "主agent要求补充分析与计划",
            "--considered-doc",
            "analysis",
            "--considered-doc",
            "plan",
            "--updated-doc",
            "analysis",
            "--status",
            "updated",
            "--progress-note",
            "已记录任务级文档刷新判断。",
        )

        global_log = [line for line in self.read_text(self.state_root / "doc-refresh.jsonl").splitlines() if line.strip()]
        self.assertEqual(len(global_log), 1)
        global_payload = json.loads(global_log[0])
        self.assertEqual(global_payload["scope"], "task")
        self.assertEqual(global_payload["task_id"], "T-005")

        event_lines = [
            line
            for line in self.read_text(self.task_dir("T-005") / "events.jsonl").splitlines()
            if line.strip()
        ]
        task_event = json.loads(event_lines[-1])
        self.assertEqual(task_event["type"], "task_doc_refresh")
        self.assertEqual(task_event["updated_docs"], ["analysis"])
        self.assertIn("任务级文档刷新判断", self.read_text(self.task_dir("T-005") / "progress.log"))

    def test_invalid_phase_intake_is_rejected(self) -> None:
        self.run_script("init_task.py", "T-009", "--goal", "验证非法阶段")
        result = self.run_script_allow_failure(
            "update_state.py",
            "T-009",
            "--phase",
            "intake",
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Invalid phase 'intake'", result.stderr)

    def test_assign_member_generates_canonical_role_and_updates_state(self) -> None:
        self.run_script("init_task.py", "T-013", "--goal", "验证成员分配")

        preview = self.run_script("assign_member.py", "--task-type", "analysis")
        self.assertEqual(preview.stdout.strip(), "member-analysis")

        result = self.run_script("assign_member.py", "T-013", "--task-type", "analysis")
        self.assertIn("member-analysis", result.stdout)

        state = self.read_json(self.task_dir("T-013") / "state.json")
        self.assertEqual(state["task_type"], "analysis")
        self.assertEqual(state["member_role_name"], "member-analysis")
        self.assertEqual(state["owner_agent_id"], "member-analysis")

        task_text = self.read_text(self.task_dir("T-013") / "task.md")
        self.assertIn("- 任务类型：analysis", task_text)
        self.assertIn("- 成员角色：member-analysis", task_text)
        self.assertIn("- 负责人：member-analysis", task_text)

    def test_assign_member_supports_same_role_multiple_instances(self) -> None:
        self.run_script("init_task.py", "T-013A", "--goal", "验证同角色多实例成员分配")

        preview = self.run_script(
            "assign_member.py",
            "--task-type",
            "coding",
            "--owner-agent-id",
            "member-coding-2",
        )
        self.assertEqual(preview.stdout.strip(), "member-coding-2")

        result = self.run_script(
            "assign_member.py",
            "T-013A",
            "--task-type",
            "coding",
            "--owner-agent-id",
            "member-coding-2",
        )
        self.assertIn("member-coding-2", result.stdout)

        state = self.read_json(self.task_dir("T-013A") / "state.json")
        self.assertEqual(state["task_type"], "coding")
        self.assertEqual(state["member_role_name"], "member-coding")
        self.assertEqual(state["owner_agent_id"], "member-coding-2")

        task_text = self.read_text(self.task_dir("T-013A") / "task.md")
        self.assertIn("- 任务类型：coding", task_text)
        self.assertIn("- 成员角色：member-coding", task_text)
        self.assertIn("- 负责人：member-coding-2", task_text)

    def test_create_subtask_initializes_parent_link_member_and_handoff(self) -> None:
        self.run_script("init_task.py", "T-018", "--goal", "验证子任务创建入口")

        result = self.run_script(
            "create_subtask.py",
            "T-019",
            "--parent-task-id",
            "T-018",
            "--task-type",
            "review",
            "--goal",
            "完成 review 子任务的初始化",
            "--scope",
            "覆盖父子关联、成员分配、初始交接与进展日志",
            "--priority",
            "high",
            "--status",
            "blocked",
            "--phase",
            "executing",
            "--acceptance-criterion",
            "子任务写入实体存档",
            "--dependency",
            "T-018",
            "--progress-note",
            "review 子任务已创建，等待 team leader 继续派发。",
            workspace=self.workspace,
        )

        self.assertIn("Created subtask T-019 under T-018 as member-review", result.stdout)

        state = self.read_json(self.task_dir("T-019") / "state.json")
        self.assertEqual(state["parent_task_id"], "T-018")
        self.assertEqual(state["task_type"], "review")
        self.assertEqual(state["member_role_name"], "member-review")
        self.assertEqual(state["owner_agent_id"], "member-review")
        self.assertEqual(state["status"], "blocked")
        self.assertEqual(state["phase"], "executing")
        self.assertEqual(state["priority"], "high")

        task_text = self.read_text(self.task_dir("T-019") / "task.md")
        self.assertIn("- 负责人：member-review", task_text)
        self.assertIn("- 任务类型：review", task_text)
        self.assertIn("- 成员角色：member-review", task_text)

        handoff_text = self.read_text(self.task_dir("T-019") / "internal" / "handoff.en.md")
        self.assertIn("Current checkpoint: subtask created for member-review", handoff_text)
        self.assertIn("continue the review work for parent T-018", handoff_text)

        progress_text = self.read_text(self.task_dir("T-019") / "progress.log")
        self.assertIn("review 子任务已创建", progress_text)
        self.assertIn("subtask T-019 created", self.read_text(self.workspace / "SESSIONS" / "current.md"))
        self.assertIn("create_subtask.py assigned T-019 to member-review", self.read_text(self.workspace / "MEMORY.md"))

        events_text = self.read_text(self.task_dir("T-019") / "events.jsonl")
        self.assertIn('"type": "subtask_created"', events_text)

        ledger = self.read_json(self.state_root / "ledger.json")
        self.assertIn("T-019", ledger["tasks"]["T-018"]["child_task_ids"])

        summary = self.run_script("render_summary.py", "--task-id", "T-019").stdout
        self.assertIn("父任务：T-018", summary)
        self.assertIn("成员角色：member-review", summary)

    def test_create_subtask_supports_same_role_multiple_instances(self) -> None:
        self.run_script("init_task.py", "T-018A", "--goal", "验证同角色多实例子任务")

        result = self.run_script(
            "create_subtask.py",
            "T-019A",
            "--parent-task-id",
            "T-018A",
            "--task-type",
            "coding",
            "--owner-agent-id",
            "member-coding-2",
            "--goal",
            "完成 coding 子任务的多实例初始化",
            workspace=self.workspace,
        )

        self.assertIn("Created subtask T-019A under T-018A as member-coding-2 (role member-coding)", result.stdout)

        state = self.read_json(self.task_dir("T-019A") / "state.json")
        self.assertEqual(state["parent_task_id"], "T-018A")
        self.assertEqual(state["task_type"], "coding")
        self.assertEqual(state["member_role_name"], "member-coding")
        self.assertEqual(state["owner_agent_id"], "member-coding-2")

        task_text = self.read_text(self.task_dir("T-019A") / "task.md")
        self.assertIn("- 负责人：member-coding-2", task_text)
        self.assertIn("- 成员角色：member-coding", task_text)

        handoff_text = self.read_text(self.task_dir("T-019A") / "internal" / "handoff.en.md")
        self.assertIn("Current checkpoint: subtask created for member-coding-2 (role member-coding)", handoff_text)

        memory_text = self.read_text(self.workspace / "MEMORY.md")
        self.assertIn("create_subtask.py assigned T-019A to member-coding-2 (role member-coding)", memory_text)

    def test_member_discussion_flow_creates_artifacts_and_resolution(self) -> None:
        self.run_script("init_task.py", "T-020", "--goal", "验证成员讨论归档")

        result = self.run_script(
            "create_discussion.py",
            "D-001",
            "--mode",
            "consult",
            "--title",
            "对齐 API 契约",
            "--context",
            "coding 与 testing 需要对齐返回结构",
            "--initiator",
            "member-coding-1",
            "--participant",
            "member-testing-1",
            "--task-id",
            "T-020",
            workspace=self.workspace,
        )
        self.assertIn("Created discussion D-001", result.stdout)

        discussion_dir = self.discussion_dir("D-001")
        self.assertTrue((discussion_dir / "topic.md").exists())
        self.assertTrue((discussion_dir / "decision.md").exists())
        self.assertTrue((discussion_dir / "state.json").exists())
        self.assertTrue((discussion_dir / "messages.jsonl").exists())

        discussion_state = self.read_json(discussion_dir / "state.json")
        self.assertEqual(discussion_state["status"], "open")
        self.assertEqual(discussion_state["mode"], "consult")
        self.assertEqual(discussion_state["initiator"], "member-coding-1")
        self.assertEqual(discussion_state["participants"], ["member-coding-1", "member-testing-1"])
        self.assertEqual(discussion_state["linked_task_ids"], ["T-020"])

        self.run_script(
            "post_discussion_message.py",
            "D-001",
            "--sender",
            "member-testing-1",
            "--to",
            "member-coding-1",
            "--kind",
            "answer",
            "--body",
            "统一返回 code、message、data 三段结构。",
            workspace=self.workspace,
        )
        self.run_script(
            "resolve_discussion.py",
            "D-001",
            "--resolver",
            "member-coding-1",
            "--summary",
            "双方确认统一返回 code/message/data",
            workspace=self.workspace,
        )

        discussion_state = self.read_json(discussion_dir / "state.json")
        self.assertEqual(discussion_state["status"], "resolved")
        self.assertEqual(discussion_state["resolution_summary"], "双方确认统一返回 code/message/data")

        decision_text = self.read_text(discussion_dir / "decision.md")
        self.assertIn("双方确认统一返回 code/message/data", decision_text)

        messages_text = self.read_text(discussion_dir / "messages.jsonl")
        self.assertIn('"type": "discussion_started"', messages_text)
        self.assertIn('"type": "discussion_message"', messages_text)
        self.assertIn('"type": "discussion_resolved"', messages_text)

        task_events = self.read_text(self.task_dir("T-020") / "events.jsonl")
        self.assertIn('"type": "discussion_started"', task_events)
        self.assertIn('"type": "discussion_resolved"', task_events)

        progress_text = self.read_text(self.task_dir("T-020") / "progress.log")
        self.assertIn("成员讨论 D-001 已启动", progress_text)
        self.assertIn("成员讨论 D-001 已收敛", progress_text)

        memory_text = self.read_text(self.workspace / "MEMORY.md")
        self.assertIn("discussion D-001 resolved: 双方确认统一返回 code/message/data", memory_text)
        session_text = self.read_text(self.workspace / "SESSIONS" / "current.md")
        self.assertIn("discussion D-001 opened", session_text)
        self.assertIn("discussion D-001 resolved", session_text)

        discussion_summary = self.run_script("render_summary.py", "--discussion-id", "D-001", workspace=self.workspace).stdout
        self.assertIn("讨论摘要 D-001", discussion_summary)
        self.assertIn("对齐 API 契约", discussion_summary)
        self.assertIn("member-coding-1", discussion_summary)
        self.assertIn("member-testing-1", discussion_summary)

        task_summary = self.run_script("render_summary.py", "--task-id", "T-020", workspace=self.workspace).stdout
        self.assertIn("成员讨论", task_summary)
        self.assertIn("D-001", task_summary)

    def test_member_role_mismatch_is_rejected(self) -> None:
        self.run_script("init_task.py", "T-014", "--goal", "验证成员角色校验")
        result = self.run_script_allow_failure(
            "update_state.py",
            "T-014",
            "--task-type",
            "analysis",
            "--owner-agent-id",
            "member-design",
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("owner_agent_id 'member-design' does not match task_type 'analysis'", result.stderr)

    def test_skill_package_docs_include_name_install_and_usage(self) -> None:
        skill_path = ROOT_DIR / "SKILL.md"
        readme_path = ROOT_DIR / "README.md"
        analysis_ref = ROOT_DIR / "references" / "analysis.md"
        design_ref = ROOT_DIR / "references" / "design.md"
        protocol_ref = ROOT_DIR / "references" / "agent-protocol.md"

        self.assertTrue(skill_path.exists())
        self.assertTrue(readme_path.exists())
        self.assertTrue(INSTALL_SCRIPT.exists())
        self.assertTrue(analysis_ref.exists())
        self.assertTrue(design_ref.exists())
        self.assertTrue(protocol_ref.exists())

        skill_text = self.read_text(skill_path)
        readme_text = self.read_text(readme_path)

        self.assertIn("name: my-team", skill_text)
        self.assertIn("安装后的 skill 名称：`my-team`", readme_text)
        self.assertIn("$CODEX_HOME/skills/my-team", readme_text)
        self.assertIn("Use [$my-team]", readme_text)
        self.assertIn("该名称固定，不提供重命名功能", readme_text)
        self.assertIn("Recommended Defaults / Need User Confirmation", readme_text)
        self.assertIn("Source vs Installed Package", readme_text)
        self.assertIn("install_skill.py", readme_text)
        self.assertIn("assign_member.py", readme_text)
        self.assertIn("create_discussion.py", readme_text)
        self.assertIn("post_discussion_message.py", readme_text)
        self.assertIn("resolve_discussion.py", readme_text)
        self.assertIn("bootstrap_workspace.py", readme_text)
        self.assertIn("update_memory.py", readme_text)
        self.assertIn("resume_readiness.py", readme_text)
        self.assertNotIn("--skill-name", readme_text)
        self.assertIn("仓库根目录是源码权威来源；Codex 实际使用的 skill 副本应位于用户目录", readme_text)
        self.assertIn("For any task, first analyze which information the user must provide or confirm", skill_text)
        self.assertIn("judge which skill-level or task-level documents may be stale", skill_text)
        self.assertIn("record what was considered, what was updated", skill_text)
        self.assertIn("append the main-agent reply to `.my-team/ai-chat/YYYY-MM-DD.md`", skill_text)
        self.assertIn("team leader", skill_text)
        self.assertIn("member", skill_text)
        self.assertIn("member-analysis", skill_text)
        self.assertIn("member-testing", skill_text)
        self.assertIn("member-review", skill_text)
        self.assertIn("member-docs", skill_text)
        self.assertIn("member-release", skill_text)
        self.assertIn("member-integration", skill_text)
        self.assertIn("create_subtask.py", skill_text)
        self.assertIn("create_discussion.py", skill_text)
        self.assertIn("post_discussion_message.py", skill_text)
        self.assertIn("resolve_discussion.py", skill_text)
        self.assertIn("render_summary.py", skill_text)
        self.assertIn("bootstrap_workspace.py", skill_text)
        self.assertIn("update_memory.py", skill_text)
        self.assertIn("resume_readiness.py", skill_text)
        self.assertIn("Document Refresh Loop", protocol_ref.read_text(encoding="utf-8"))
        self.assertIn("基于 artifact 汇总后再对用户输出，并把主 Agent 回复追加到当日聊天日志", protocol_ref.read_text(encoding="utf-8"))
        self.assertIn("当前任务中哪些信息必须由用户提供或确认", self.read_text(analysis_ref))
        self.assertIn("推荐值：", self.read_text(analysis_ref))
        self.assertIn("待确认项：", self.read_text(analysis_ref))
        self.assertIn("team leader", self.read_text(analysis_ref))
        self.assertIn("member-first", self.read_text(analysis_ref))
        self.assertIn("member-analysis", self.read_text(analysis_ref))
        self.assertIn("member-design", self.read_text(analysis_ref))
        self.assertIn("member-review", self.read_text(analysis_ref))
        self.assertIn("member-docs", self.read_text(analysis_ref))
        self.assertIn("member-release", self.read_text(analysis_ref))
        self.assertIn("member-integration", self.read_text(analysis_ref))
        self.assertIn("team leader", self.read_text(design_ref))
        self.assertIn("member-design", self.read_text(design_ref))
        self.assertIn("create_subtask.py", self.read_text(design_ref))
        self.assertIn("create_discussion.py", self.read_text(design_ref))
        self.assertIn("resolve_discussion.py", self.read_text(design_ref))
        self.assertIn("render_summary.py", self.read_text(design_ref))
        self.assertIn("assign_member.py", self.read_text(design_ref))
        self.assertIn("python3 install_skill.py", readme_text)
        self.assertIn("What The Agent Should Analyze First", readme_text)
        self.assertFalse(SKILL_MIRROR_DIR.exists(), f"Stale mirror should not exist: {SKILL_MIRROR_DIR}")
        self.assertIn("team leader", readme_text)
        self.assertIn("member", readme_text)
        self.assertIn("task-type matched member names", readme_text)
        self.assertIn("member-analysis", readme_text)
        self.assertIn("member-review", readme_text)
        self.assertIn("member-docs", readme_text)
        self.assertIn("member-release", readme_text)
        self.assertIn("member-integration", readme_text)
        self.assertIn("create_subtask.py", readme_text)
        self.assertIn("create_discussion.py", readme_text)
        self.assertIn("post_discussion_message.py", readme_text)
        self.assertIn("resolve_discussion.py", readme_text)
        self.assertIn("render_summary.py", readme_text)
        self.assertIn("bootstrap_workspace.py", readme_text)
        self.assertIn("update_memory.py", readme_text)
        self.assertIn("resume_readiness.py", readme_text)
        self.assertIn("assignment and completion feedback", readme_text)
        self.assertIn("persistent my-team mode", readme_text)
        self.assertIn("fixed skill name", readme_text)

    def test_team_leader_member_model_is_documented(self) -> None:
        skill_text = self.read_text(ROOT_DIR / "SKILL.md")
        readme_text = self.read_text(ROOT_DIR / "README.md")
        analysis_text = self.read_text(ROOT_DIR / "references" / "analysis.md")
        design_text = self.read_text(ROOT_DIR / "references" / "design.md")
        protocol_text = self.read_text(ROOT_DIR / "references" / "agent-protocol.md")

        self.assertIn("team leader", skill_text)
        self.assertIn("member", skill_text)
        self.assertIn("member-analysis", skill_text)
        self.assertIn("member-testing", skill_text)
        self.assertIn("member-review", skill_text)
        self.assertIn("member-docs", skill_text)
        self.assertIn("member-release", skill_text)
        self.assertIn("member-integration", skill_text)
        self.assertIn("assign_member.py", skill_text)
        self.assertIn("create_subtask.py", skill_text)
        self.assertIn("create_discussion.py", skill_text)
        self.assertIn("post_discussion_message.py", skill_text)
        self.assertIn("resolve_discussion.py", skill_text)
        self.assertIn("render_summary.py", skill_text)
        self.assertIn("bootstrap_workspace.py", skill_text)
        self.assertIn("update_memory.py", skill_text)
        self.assertIn("resume_readiness.py", skill_text)
        self.assertIn("main agent as team leader", readme_text)
        self.assertIn("member-first analysis", readme_text)
        self.assertIn("members handling analysis, design, coding, and testing", readme_text)
        self.assertIn("review/docs/release/integration", readme_text)
        self.assertIn("task-type matched member names", readme_text)
        self.assertIn("team leader coordinating and reporting progress", readme_text)
        self.assertIn("team leader", analysis_text)
        self.assertIn("member-first", analysis_text)
        self.assertIn("member-analysis", analysis_text)
        self.assertIn("member-review", analysis_text)
        self.assertIn("team leader", design_text)
        self.assertIn("member", design_text)
        self.assertIn("member-design", design_text)
        self.assertIn("create_subtask.py", design_text)
        self.assertIn("create_discussion.py", design_text)
        self.assertIn("resolve_discussion.py", design_text)
        self.assertIn("render_summary.py", design_text)
        self.assertIn("bootstrap_workspace.py", design_text)
        self.assertIn("update_memory.py", design_text)
        self.assertIn("resume_readiness.py", design_text)
        self.assertIn("team leader", protocol_text)
        self.assertIn("analysis and decomposition", protocol_text)
        self.assertIn("coding", protocol_text)
        self.assertIn("testing", protocol_text)
        self.assertIn("member-analysis", protocol_text)
        self.assertIn("member-review", protocol_text)
        self.assertIn("discussion", protocol_text)
        self.assertIn("assignment and completion", readme_text)
        self.assertIn("my-team mode", readme_text)
        self.assertIn("task ownership", protocol_text)
        self.assertIn("stay in my-team mode", protocol_text)
        self.assertIn("fixed skill name", readme_text)
        self.assertIn("bootstrap_workspace.py", protocol_text)
        self.assertIn("update_memory.py", protocol_text)
        self.assertIn("resume_readiness.py", protocol_text)

    def test_task_handoff_placeholder_is_marked_as_incomplete(self) -> None:
        self.run_script("init_task.py", "T-010", "--goal", "验证 handoff 刷新")

        result = self.run_script(
            "suggest_doc_updates.py",
            "--mode",
            "task",
            "--task-id",
            "T-010",
            "--message",
            "继续执行当前任务。",
        )
        payload = json.loads(result.stdout)

        self.assertTrue(payload["doc_flags"]["handoff"])
        self.assertIn("handoff information is incomplete", payload["reasons"]["handoff"])
        self.assertNotIn("scaffold", " ".join(payload["reasons"]["handoff"]).lower())

    def test_install_skill_script_rejects_skill_name_override(self) -> None:
        codex_home = Path(self.temp_dir.name) / "codex-home"

        result = self.run_install_script_allow_failure(
            "--codex-home",
            str(codex_home),
            "--skill-name",
            "custom-task-flow-skill",
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("unrecognized arguments: --skill-name", result.stderr)

    def test_install_skill_script_installs_fixed_my_team_package(self) -> None:
        codex_home = Path(self.temp_dir.name) / "default-codex-home"

        result = self.run_install_script("--codex-home", str(codex_home))

        install_dir = codex_home / "skills" / "my-team"
        self.assertTrue((install_dir / "SKILL.md").exists())
        self.assertTrue((install_dir / "README.md").exists())
        self.assertTrue((install_dir / "install_skill.py").exists())
        self.assertTrue((install_dir / "references" / "agent-protocol.md").exists())
        self.assertTrue((install_dir / "scripts" / "bootstrap_workspace.py").exists())
        self.assertTrue((install_dir / "scripts" / "assign_member.py").exists())
        self.assertTrue((install_dir / "scripts" / "create_subtask.py").exists())
        self.assertTrue((install_dir / "scripts" / "create_discussion.py").exists())
        self.assertTrue((install_dir / "scripts" / "post_discussion_message.py").exists())
        self.assertTrue((install_dir / "scripts" / "resolve_discussion.py").exists())
        self.assertTrue((install_dir / "scripts" / "update_memory.py").exists())
        self.assertTrue((install_dir / "scripts" / "resume_readiness.py").exists())
        self.assertTrue((install_dir / "scripts" / "render_summary.py").exists())
        self.assertTrue((install_dir / "tests" / "test_scripts.py").exists())

        installed_skill = self.read_text(install_dir / "SKILL.md")
        installed_readme = self.read_text(install_dir / "README.md")
        installed_protocol = self.read_text(install_dir / "references" / "agent-protocol.md")

        self.assertIn("name: my-team", installed_skill)
        self.assertIn("my-team", installed_readme)
        self.assertIn("my-team", installed_protocol)
        self.assertIn("member-analysis", installed_skill)
        self.assertIn("member-review", installed_skill)
        self.assertIn("member-docs", installed_skill)
        self.assertIn("member-release", installed_skill)
        self.assertIn("member-integration", installed_skill)
        self.assertIn("assign_member.py", installed_readme)
        self.assertIn("create_subtask.py", installed_readme)
        self.assertIn("create_discussion.py", installed_readme)
        self.assertIn("post_discussion_message.py", installed_readme)
        self.assertIn("resolve_discussion.py", installed_readme)
        self.assertIn("render_summary.py", installed_readme)
        self.assertIn("bootstrap_workspace.py", installed_readme)
        self.assertIn("update_memory.py", installed_readme)
        self.assertIn("resume_readiness.py", installed_readme)
        self.assertIn("task-type matched member names", installed_readme)
        self.assertIn("member-testing", installed_protocol)
        self.assertIn(f"Installed skill to user directory: {install_dir}", result.stdout)
        self.assertIn("Recommended invocation: Use [$my-team]", result.stdout)
        self.assertIn(
            "Installed package contents: README.md, SKILL.md, install_skill.py, references/, scripts/, tests/",
            result.stdout,
        )

    def test_render_summary_team_leader_view_groups_and_filters_blocked_tasks(self) -> None:
        self.run_script("init_task.py", "T-030", "--goal", "团队汇总父任务")
        self.run_script(
            "create_subtask.py",
            "T-031",
            "--parent-task-id",
            "T-030",
            "--task-type",
            "review",
            "--goal",
            "review 子任务",
            "--status",
            "blocked",
            "--phase",
            "executing",
        )
        self.run_script(
            "create_subtask.py",
            "T-032",
            "--parent-task-id",
            "T-030",
            "--task-type",
            "coding",
            "--owner-agent-id",
            "member-coding-1",
            "--goal",
            "coding 子任务",
            "--status",
            "in_progress",
            "--phase",
            "executing",
        )
        self.run_script(
            "create_subtask.py",
            "T-034",
            "--parent-task-id",
            "T-030",
            "--task-type",
            "coding",
            "--owner-agent-id",
            "member-coding-2",
            "--goal",
            "第二个 coding 子任务",
            "--status",
            "in_progress",
            "--phase",
            "executing",
        )
        self.run_script(
            "create_subtask.py",
            "T-033",
            "--parent-task-id",
            "T-030",
            "--task-type",
            "docs",
            "--goal",
            "docs 子任务",
            "--status",
            "completed",
            "--phase",
            "reporting",
        )

        owner_summary = self.run_script("render_summary.py", "--group-by", "owner").stdout
        self.assertIn("Team Leader 总览", owner_summary)
        self.assertIn("## owner：member-review", owner_summary)
        self.assertIn("## owner：member-coding-1", owner_summary)
        self.assertIn("## owner：member-coding-2", owner_summary)
        self.assertIn("## owner：member-docs", owner_summary)

        type_summary = self.run_script("render_summary.py", "--group-by", "task-type").stdout
        self.assertIn("## task-type：review", type_summary)
        self.assertIn("## task-type：coding", type_summary)
        self.assertIn("## task-type：docs", type_summary)

        status_summary = self.run_script("render_summary.py", "--group-by", "status").stdout
        self.assertIn("## status：blocked", status_summary)
        self.assertIn("## status：in_progress", status_summary)
        self.assertIn("## status：completed", status_summary)

        blocked_only = self.run_script("render_summary.py", "--blocked-only").stdout
        self.assertIn("Team Leader 总览", blocked_only)
        self.assertIn("T-031", blocked_only)
        self.assertNotIn("T-032", blocked_only)
        self.assertNotIn("T-034", blocked_only)
        self.assertNotIn("T-033", blocked_only)

    def test_installed_package_tests_run_successfully(self) -> None:
        if os.environ.get("ONE_TEAM_RUNTIME_PACKAGE") == "1":
            self.skipTest("Skip recursive install verification inside the runtime package.")

        codex_home = Path(self.temp_dir.name) / "runtime-codex-home"
        self.run_install_script("--codex-home", str(codex_home))

        install_dir = codex_home / "skills" / "my-team"
        env = os.environ.copy()
        env["ONE_TEAM_RUNTIME_PACKAGE"] = "1"
        result = subprocess.run(
            [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"],
            cwd=install_dir,
            text=True,
            capture_output=True,
            env=env,
            check=False,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        combined_output = result.stdout + result.stderr
        self.assertIn("OK", combined_output)


if __name__ == "__main__":
    unittest.main()
