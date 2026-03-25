---
name: my-team
description: Coordinate artifact-first multi-agent work with durable task directories, chat logs, refresh tracking, checkpoints, and recovery-friendly Chinese/English split artifacts.
---

# My Team

## Overview

Use this skill when you need one team leader to stay user-facing, coordinate a team of members, and continuously write structured artifacts to disk while the members execute bounded sub-tasks.

The team leader should first be able to delegate analysis and task breakdown to one member, then assign the resulting work to other members for implementation, testing, and verification.

Once the main agent is asked to start the `my-team` skill, it should keep operating in my-team mode until the user explicitly asks to exit my-team mode.

## References

Read [references/agent-protocol.md](references/agent-protocol.md) for the operating protocol and checkpoint rules.

Read [references/analysis.md](references/analysis.md) and [references/design.md](references/design.md) for the product rationale and design boundaries.

## Scripts

Prefer the local scripts in `scripts/` over handwritten edits to machine-readable files:

- `init_task.py`
- `create_subtask.py`
- `update_state.py`
- `append_event.py`
- `update_step.py`
- `sync_task_doc.py`
- `assign_member.py`
- `create_discussion.py`
- `post_discussion_message.py`
- `resolve_discussion.py`
- `bootstrap_workspace.py`
- `write_artifact.py`
- `checkpoint_task.py`
- `revise_task.py`
- `update_memory.py`
- `write_analysis.py`
- `write_design.py`
- `write_plan.py`
- `write_result.py`
- `log_chat_turn.py`
- `resume_readiness.py`
- `suggest_doc_updates.py`
- `record_doc_refresh.py`
- `render_summary.py`

## Team View Helpers

- `create_subtask.py` for one-shot child task setup, including parent linkage, canonical member assignment, optional instance-level owner assignment, and initial handoff/progress
- `create_discussion.py` to open a member-to-member consult/sync thread with participants and linked tasks
- `post_discussion_message.py` to append one auditable member message to a discussion
- `resolve_discussion.py` to record the decision, resolve the discussion, and sync the outcome back to linked tasks
- `render_summary.py` as the team leader's status panel, with grouped owner/task-type/status views, blocked-task filtering, and owner-level separation for same-role parallel instances
- `bootstrap_workspace.py` to initialize TEAM/MEMORY/USER_CONTEXT/ROLES/INBOX/SESSIONS/current.md
- `update_memory.py` to append structured facts, decisions, preferences, and constraints
- `resume_readiness.py` to inspect workspace + orchestrator-state before resuming work

## Workspace Layer

All skill runtime files live under `.my-team/` in the project root, keeping them separate from the project's own source files. The workspace root is `.my-team/` and the orchestrator state root is `.my-team/orchestrator-state/`.

The workspace should bootstrap into a small set of long-lived files:

```text
.my-team/
  TEAM.md
  MEMORY.md
  USER_CONTEXT.md
  ROLES/
    leader.md
    member-analysis.md
    member-design.md
    member-coding.md
    member-testing.md
    member-review.md
    member-docs.md
    member-release.md
    member-integration.md
  INBOX.md
  SESSIONS/
    current.md
```

- `TEAM.md` records the long-running operating contract, escalation rules, and workspace assumptions
- `MEMORY.md` stores durable facts, confirmed decisions, user preferences, and constraints that should survive task boundaries
- `USER_CONTEXT.md` stores the confirmed user environment, workspace root, and other setup facts
- `ROLES/` stores standing orders for the team leader and each member role
- `INBOX.md` stores pending work, interrupts, and items that should be resumed later
- `SESSIONS/current.md` stores the current live session summary so the team leader can recover quickly after interruption

For this layer, prefer three helper scripts:

- `bootstrap_workspace.py` to create the workspace skeleton
- `update_memory.py` to append durable facts, decisions, preferences, and constraints
- `resume_readiness.py` to check whether the current workspace and task state are safe to resume

The team leader should bootstrap the workspace before the first long-lived session, refresh memory after confirmed decisions or repeated facts, and check resume readiness before continuing after interruption.

## Document Refresh Workflow

1. Use `suggest_doc_updates.py` to judge which skill-level or task-level documents may be stale.
2. Refresh the affected documents.
3. Use `record_doc_refresh.py` to record what was considered, what was updated, and whether the decision was `updated`, `checked`, or `not_needed`.
4. After artifact-based summarization, append the main-agent reply to `.my-team/ai-chat/YYYY-MM-DD.md` with `log_chat_turn.py`; in this skill the main agent acts as the team leader.

## Sub-Agent Dispatch

In VS Code Copilot, the team leader must use `runSubagent` to dispatch real sub-agents for member work instead of role-playing different members sequentially. This enables true parallel execution.

### Dispatch Rules

- Before dispatching, use `create_subtask.py` to create the task directory and record member assignment
- Use `runSubagent` to invoke a new agent for each member task; include the task context, role instructions, script paths, and expected deliverables in the prompt
- Independent member tasks (e.g., two different coding subtasks) should be dispatched in **parallel** by calling `runSubagent` multiple times simultaneously
- Dependent tasks (e.g., testing depends on coding completion) should be dispatched **sequentially** after the predecessor completes
- The sub-agent prompt must tell the member which scripts to use, where the state-root and workspace are, and what artifacts to produce
- When the sub-agent returns, the team leader should read the updated task artifacts and summary, then report progress to the user

### Dispatch Prompt Template

When calling `runSubagent`, construct the prompt like this:

```
You are {member_role_name}, a team member in a my-team skill workspace.

Task: {task_id}
Goal: {goal}
Scope: {scope}
Parent task: {parent_task_id}

Workspace root: {workspace_root}  (under .my-team/)
State root: {state_root}  (under .my-team/orchestrator-state/)
Scripts directory: {scripts_dir}

Your job:
1. Read the task directory at {state_root}/tasks/{task_id}/
2. Perform the {task_type} work described in the goal
3. Write your analysis/design/code/test results using the scripts:
   - write_analysis.py / write_design.py / write_plan.py / write_result.py
   - update_state.py to advance phase
   - update_step.py to track progress
   - checkpoint_task.py when reaching milestones
4. Update handoff.en.md with recovery info when done

Return a brief summary of what was accomplished, what remains, and any blockers.
```

### Example

```python
# Team leader creates the main task FIRST with init_task.py
run_in_terminal("python3 scripts/init_task.py T-001 --goal '实现贪吃蛇游戏' --scope '浏览器单页游戏' --acceptance-criterion '可运行' --workspace .my-team")

# Then creates subtasks with hierarchical IDs
run_in_terminal("python3 scripts/create_subtask.py T-001-1 --parent-task-id T-001 --task-type analysis --goal '分析用户需求' --workspace .my-team")

# Then dispatches real sub-agent
runSubagent(
    prompt="You are member-analysis... (full context)",
    description="analysis for T-001-1"
)

# For parallel coding tasks (hierarchical IDs under same parent)
runSubagent(prompt="You are member-coding (T-001-3)...", description="coding T-001-3")  # parallel
runSubagent(prompt="You are member-coding (T-001-4)...", description="coding T-001-4")  # parallel
```

## Operating Rules

- All skill runtime files (workspace, orchestrator-state, ai-chat, etc.) live under the `.my-team/` directory in the project root, keeping them separate from the project's own files
- **Always create the main task first** with `init_task.py` (including goal, scope, acceptance criteria) before using `create_subtask.py` to add child tasks; never skip `init_task.py` — otherwise the parent task gets implicitly created as an empty shell with missing goal and scope
- **Task ID naming**: main tasks use top-level numbers (`T-001`, `T-002`); subtasks use hierarchical `parent-seq` format (`T-001-1`, `T-001-2`); do not use flat sequential numbers for both main and sub tasks
- Keep user-facing documents in Simplified Chinese
- Keep internal agent notes in English under `internal/`
- Keep state in JSON or JSONL
- Log every user and team leader turn to `.my-team/ai-chat/YYYY-MM-DD.md`
- Checkpoint after receiving work, after analysis, after design, after planning, before execution, after execution, when blocked, when interrupted, and before final reporting
- For any task, first analyze which information the user must provide or confirm
- Prefer proposing recommended defaults before asking the user to confirm them
- The team leader should not personally write code, perform analysis or design, or run testing work; those activities should be dispatched to team members via `runSubagent`
- The team leader should focus on planning, delegation, coordination, conflict resolution, and timely progress reporting
- For each task, the team leader should consider one member for initial decomposition first, then fan out work to other members after the breakdown is returned
- When creating or referring to a member, use a task-type-matched role name such as `member-analysis`, `member-design`, `member-coding`, `member-testing`, `member-review`, `member-docs`, `member-release`, or `member-integration`
- If a tool returns a different system nickname, keep using the task-type-matched role name in user-facing reports and `handoff.en.md`
- Keep `member_role_name` as the canonical role identity; if the same role needs parallel workers, use distinct `owner_agent_id` values such as `member-coding-1` and `member-coding-2`
- The team leader should explicitly report which member owns which task, what the current completion status is, and what remains blocked or in progress
- The team leader should prefer `create_subtask.py` when creating a new child task so parent linkage, member assignment, and initial handoff stay consistent
- Members may open direct consult/sync discussions with other members, but the discussion must be recorded under `.my-team/orchestrator-state/discussions/<discussion-id>` instead of becoming free-form chat
- Use `create_discussion.py`, `post_discussion_message.py`, and `resolve_discussion.py` for member-to-member discussion so participants, messages, linked tasks, and decisions remain auditable
- The team leader should keep a confirmed workspace root for long-lived state, bootstrap it when missing, and update workspace memory after durable decisions
- The team leader should use `bootstrap_workspace.py`, `update_memory.py`, and `resume_readiness.py` to manage persistent workspace state and recoverability
- After my-team mode is activated, the main agent should keep following this team leader / member model until the user explicitly says to exit my-team mode
- The installed skill name is fixed to `my-team`; do not treat it as a user-configurable rename target inside this skill
- The only valid task phases are `received`, `analysis`, `design`, `planning`, `executing`, `reporting`, `completed`, `interrupted`, and `revising`; do not invent `intake` or other phase names
- `handoff.en.md` is a formal internal transition record for team members, not a scaffold placeholder; describe remaining work, blockers, next actions, and ownership without exposing internal template language to the user
- Member task types are standardized across analysis, design, coding, testing, review, docs, release, and integration
- Every child task must have a real archive under `.my-team/orchestrator-state/tasks/<task-id>`; ledger entries alone are not enough for recovery or audit
- If a parent task is first discovered through child-task linkage, create its corresponding task directory as well so the parent can be recovered and audited like any other task

## Expected Layout

```text
.my-team/
  TEAM.md
  MEMORY.md
  USER_CONTEXT.md
  ROLES/
  INBOX.md
  SESSIONS/
    current.md
  ai-chat/
    2026-03-23.md
  orchestrator-state/
    doc-refresh.jsonl
    ledger.json
    discussions/
      D-001/
        ...
    tasks/
      T-001/
        ...
      T-002/
        ...
```

## Validation

Run the regression tests with:

```bash
python3 -m unittest discover -s tests -v
```

## Installation

### Codex CLI

Use the package-level installer before invoking the skill in a new Codex setup:

```bash
python3 install_skill.py --codex-home "$CODEX_HOME"
```

The installed skill that Codex actually loads should live under the user directory `$CODEX_HOME/skills/my-team`.

### GitHub Copilot (VS Code)

Personal install (available in all projects):

```bash
python3 install_copilot.py
```

Project-level install (scoped to one project, can be committed to git):

```bash
python3 install_copilot.py --project /path/to/project
```

The installed skill lives under `~/.copilot/skills/my-team` (personal) or `<project>/.github/skills/my-team` (project-level).

### Source of Truth

The repository root is the source of truth. Re-run the corresponding installer after modifying source files.
