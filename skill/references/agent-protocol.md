# My Team Agent Protocol

## Language Split

- `task.md`、`analysis.md`、`design.md`、`plan.md`、`progress.log`、`result.md` 使用简体中文
- `internal/brief.en.md` 与 `internal/handoff.en.md` 使用英文
- `state.json`、`steps.json`、`events.jsonl` 使用结构化格式

## Task ID Naming Convention

- 主任务使用顶层编号：`T-001`、`T-002`、`T-003`...
- 子任务使用 `父任务ID-序号` 层级格式：`T-001-1`、`T-001-2`、`T-001-3`...
- 嵌套子任务继续追加层级：`T-001-1-1`、`T-001-1-2`...
- 同一父任务下的子任务按创建顺序递增
- 例如：主任务 `T-001` 有分析子任务 `T-001-1`、设计子任务 `T-001-2`、编码子任务 `T-001-3`、测试子任务 `T-001-4`

## Team Leader Loop

1. 记录用户消息到 `.my-team/ai-chat/YYYY-MM-DD.md`
2. 如果 workspace 未初始化或缺少核心文件，先用 `bootstrap_workspace.py` 建好 `.my-team/` 下的 `TEAM.md`、`MEMORY.md`、`USER_CONTEXT.md`、`ROLES/`、`INBOX.md` 和 `SESSIONS/current.md`
3. 判断 skill 级文档是否需要刷新
4. 先分析哪些信息需要用户提供或确认，并优先准备推荐值，同时把长期事实、偏好和约束写入 `MEMORY.md`
5. 读取 `ledger.json`、`SESSIONS/current.md` 和受影响任务
6. **先用 `init_task.py` 创建主任务**（含 goal、scope、acceptance-criterion），确保主任务有完整的 artifact 存档，**然后**再用 `create_subtask.py` 创建子任务；不要跳过 `init_task.py` 直接创建子任务，否则父任务会被隐式补建为空壳
7. 用 `create_subtask.py` 创建子任务后，用 `runSubagent` 调度真正的子 agent 来执行 member 工作；独立的成员任务应并行发出多个 `runSubagent` 调用
8. 只在边界清晰时把分析、设计、开发、测试等工作交给 member
9. 基于 artifact 汇总后再对用户输出，并把主 Agent 回复追加到当日聊天日志；在这个 skill 里主 Agent 充当 team leader
10. 持续向用户汇报任务进展、阻塞点和下一步协调动作
11. 及时反馈"任务分配给了谁""当前完成情况如何""哪些任务仍在进行、等待或阻塞"
12. 一旦收到启动 `my-team` skill 的指令，就持续按 my-team 模式执行，直到收到"退出 my-team 模式"的明确指令
13. 只使用合法阶段 `received`、`analysis`、`design`、`planning`、`executing`、`reporting`、`completed`、`interrupted`、`revising`，不要引入 `intake` 或其他未定义阶段
14. 每个子任务都必须在 `.my-team/orchestrator-state/tasks/<task-id>` 下有实体存档；`ledger.json` 只能记录索引，不能替代任务目录
15. 如果父任务是通过子任务关系首次被发现，也要为该父任务创建对应任务目录，保证恢复、审计和上下文续接都可用
16. task ID 遵循层级命名：主任务 `T-001`，子任务 `T-001-1`、`T-001-2`...; 不要对主任务和子任务使用平行编号如 `T-001`、`T-002`
17. 创建或引用 member 时，必须使用和任务类型匹配的角色名，例如 `member-analysis`、`member-design`、`member-coding`、`member-testing`、`member-review`、`member-docs`、`member-release`、`member-integration`；即使工具返回不同的系统昵称，对外汇报和内部交接也要沿用任务类型匹配的角色名
18. `member_role_name` 代表 canonical role；如果同一 role 需要并行多个 agent，应保持 `member_role_name` 不变，并使用不同的 `owner_agent_id`，例如 `member-coding-1`、`member-coding-2`
19. 创建子任务时优先使用 `create_subtask.py`，把父子关系、member 分配、初始 progress 和 handoff 一次性落盘
20. team leader 应优先使用 `create_subtask.py` 来一次性完成父子关系、member 分配和初始交接的落盘；汇报时继续沿用任务类型匹配的成员角色名
21. member 之间允许直接发起 `consult` 或 `sync` 讨论，但讨论必须通过 `create_discussion.py`、`post_discussion_message.py`、`resolve_discussion.py` 落盘到 `.my-team/orchestrator-state/discussions/<discussion-id>`
20. discussion artifact 至少要记录参与者、关联任务、消息流和决议；不要把关键讨论留在不可恢复的临时聊天里
21. 长期事实、偏好、决策和约束应通过 `update_memory.py` 追加到 `MEMORY.md`
22. 恢复前应先运行 `resume_readiness.py`，确认 workspace 和 task artifact 是否足够接续
23. 所有 skill 运行时文件统一放在项目根目录的 `.my-team/` 下，和项目自身文件隔离

## Workspace / Memory Loop

1. 先确定用户确认过的 workspace 根目录（默认 `.my-team/`），必要时先初始化长期 workspace
2. workspace 缺少 bootstrap 文件时，优先用 `bootstrap_workspace.py` 创建 `.my-team/` 下的 `TEAM.md`、`MEMORY.md`、`USER_CONTEXT.md`、`ROLES/`、`INBOX.md`、`SESSIONS/current.md`
3. `TEAM.md` 保存 team leader 的长期契约和升级规则，`MEMORY.md` 保存长期事实、决策、偏好和约束，`USER_CONTEXT.md` 保存环境与 workspace 约定
4. `ROLES/` 保存 team leader 和各 member 的长期角色说明，`INBOX.md` 保存待接收和待恢复工作，`SESSIONS/current.md` 保存当前运行摘要
5. 在做出新的长期决策、确认新的偏好或收敛新的约束后，使用 `update_memory.py` 更新记忆层
6. 在重新接续任务或中断恢复前，使用 `resume_readiness.py` 检查 workspace 和任务状态是否具备继续条件
7. 临时执行日志继续写入 `ai-chat/`、`events.jsonl` 和 task artifacts，workspace memory 只承载长期且值得跨会话保留的信息

Team leader constraints:

- team leader only coordinates, assigns, and reports progress
- use `runSubagent` to dispatch real sub-agents for member work; do not role-play members sequentially
- independent member tasks should be dispatched in parallel via multiple `runSubagent` calls
- start with one member for `analysis and decomposition`
- hand off later `coding` and `testing` work to members instead of doing it directly
- member task types already include `review`, `docs`, `release`, and `integration` in addition to `analysis`, `design`, `coding`, and `testing`
- when naming members, keep the role name aligned with the assigned task type in reports and handoff
- keep `member_role_name` canonical and use distinct `owner_agent_id` values when the same role is running multiple parallel member instances
- use `create_subtask.py` for new child tasks so parent linkage and initial handoff stay consistent
- allow member-to-member discussion only when it is recorded as a discussion artifact under `.my-team/orchestrator-state/discussions/` with participants, linked tasks, and a final decision
- explicitly report task ownership, completion status, and blocked work back to the user
- stay in my-team mode until the user explicitly asks to exit it
- all skill runtime files (workspace state, orchestrator-state, ai-chat) live under `.my-team/` in the project root
- refresh workspace memory after confirmed decisions, durable preferences, and workspace changes
- consult resume readiness before resuming a suspended workspace session
- keep `MEMORY.md` for durable memory, `SESSIONS/current.md` for the current session, and `resume_readiness.py` for recovery checks

## Member Loop

1. 加载任务目录
2. 判断任务级文档是否需要刷新
3. 接收 team leader 分配的局部任务并补齐分析、设计、计划、执行记录和结果
4. 在执行步骤前后写入状态、步骤、事件和进度日志
5. 中断时更新 `handoff.en.md`，把可恢复信息交回 team leader；handoff 是正式交接记录，不是脚手架占位文件

## Document Refresh Loop

1. 先判断哪些文档可能过期
2. 再刷新需要更新的文档
3. 最后记录判断与更新结果，不能悄悄改文档但不留痕

## Packaging Rule

- 交付 skill 时，必须同时提供 `SKILL.md`、`references/`、`scripts/`、`tests/`
- 交付物必须明确 skill 名称固定为 `my-team`、安装位置 `$CODEX_HOME/skills/my-team` 和调用示例
- 交付物必须明确哪些配置由 Agent 推荐，哪些配置需要用户最终确认
- 交付物还必须提供可执行的安装脚本，默认把包安装到 `$CODEX_HOME/skills/my-team`
- 安装副本必须自洽，包含 `install_skill.py`、`scripts/`、`tests/` 和成员分配/子任务创建入口
- 交付物还必须明确说明：工程目录保存源码，用户目录 `$CODEX_HOME/skills/my-team` 保存实际安装后的 skill
- 交付物还必须明确说明：`orchestrator-state/tasks/<task-id>` 保存每个任务和子任务的实体存档，`ledger.json` 只做索引与关系登记
- 交付物还必须明确说明：`orchestrator-state/discussions/<discussion-id>` 保存成员讨论实体存档，包含 topic、messages、decision 和 state
- 交付物还必须明确 team leader 只负责协调、管理和汇报，member 负责分析、设计、开发和测试
- 交付物还必须明确：`create_subtask.py` 会承担高层子任务创建入口，`render_summary.py` 会承担 team leader 视角的成员状态面板
- 交付物还必须明确：`create_discussion.py`、`post_discussion_message.py`、`resolve_discussion.py` 会承担成员直接讨论和决议留痕
