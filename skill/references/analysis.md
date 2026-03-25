# My Team 分析

## 目标

这个 skill 面向需要长期推进、可被打断、需要 team leader 统一协调多个 member 协作的复杂任务，并要求在 my-team 模式下持续保持稳定的团队分工。

## 要解决的问题

- 只依赖上下文记忆时，长任务在中断后难恢复
- 多子任务并行时，缺少统一 artifact 会让状态难追踪
- 任务分析、设计、计划、执行和结果如果不落盘，就很难解释"为什么这样做"
- 如果没有长期 workspace 和 memory，team leader 只能记住当前任务，无法稳定延续用户偏好、确认过的 workspace 和恢复线索
- 如果 skill 产生的文件和项目自身文件混在一起，会污染项目目录结构

## 关键要求

- team leader 是唯一对外入口
- team leader 不亲自承担分析、设计、开发和测试工作
- member 只执行边界清晰的局部任务
- 中文用户文档与英文内部文档分层保存
- 聊天日志、状态文件、事件流和文档刷新记录都可追踪
- team leader 需要及时反馈任务分配对象、当前完成情况和阻塞项
- 启动 my-team 后，除非用户明确退出，否则后续都应保持同一协作模式

## Team Leader / Member Model

- `team leader` 负责统一接收用户任务、管理成员分工并汇报整体进展
- `member-first` 是默认工作流：先让一个 member 做分析与拆解，再继续派发后续执行任务
- 分析、设计、开发、测试等执行性工作都属于 member，而不是 team leader
- member 名称应与分配的任务类型匹配，例如 `member-analysis`、`member-design`、`member-coding`、`member-testing`，标准集合也已经扩展到 `member-review`、`member-docs`、`member-release`、`member-integration`
- `member_role_name` 应保持 canonical role；如果同一 role 需要并行多个实例，应通过不同的 `owner_agent_id` 区分，例如 `member-coding-1`、`member-coding-2`
- 如果工具返回了不同的系统昵称，team leader 在对外汇报和内部交接时仍应使用任务类型匹配的角色名
- team leader 还需要持续向用户说明"谁在做什么""完成到了哪一步"
- 真实团队里 member 之间还会围绕接口、依赖和验证口径直接讨论，因此 skill 需要可审计的 member-to-member discussion，而不是把所有讨论都强制经过 team leader 转发
- 创建子任务、分配 member、初始化 handoff 和 progress 的动作应尽量收敛到单一入口，减少手工拼装状态的风险
- 长期 agent 还需要 workspace bootstrap、persistent memory 和 resume readiness 这三层能力，把"长期在线"和"可恢复"变成正式契约
- 在 VS Code Copilot 中，team leader 应使用 `runSubagent` 调度真正的子 agent 来执行 member 工作，实现真正的并行执行

## Workspace / Memory

- 所有 skill 运行时文件统一放在项目根目录的 `.my-team/` 下，和项目自身文件隔离

- `TEAM.md` 记录长期协作契约，包含 team leader 的边界、恢复规则和升级规则
- `MEMORY.md` 记录跨任务保留的事实、决策、偏好和约束
- `USER_CONTEXT.md` 记录确认过的 workspace、仓库位置、安装路径和用户环境
- `ROLES/` 记录 leader 和各 member 的长期角色说明，避免每次重新解释
- `INBOX.md` 记录长期待办、插单和恢复后续工作
- `SESSIONS/current.md` 记录当前会话摘要，帮助团队在中断后快速恢复
- `bootstrap_workspace.py` 应负责初始化上述结构
- `update_memory.py` 应负责把长期事实和决策写回记忆层
- `resume_readiness.py` 应负责判断 workspace 和任务状态是否可继续

## 技能交付要求

- 当前包装固定使用 `my-team` 作为 skill 名称
- 交付物需要包含可安装的 `SKILL.md`
- 交付物需要包含安装说明和使用说明，帮助用户把 skill 放到 `$CODEX_HOME/skills/my-team`
- Agent 需要先分析当前任务中哪些信息必须由用户提供或确认，并把推荐值与待确认项区分开
  - 推荐值：skill 名称、内部语言等固定项
  - 待确认项：workspace 根目录、安装路径等因用户环境而异的配置
- 交付物需要包含可执行安装脚本，减少用户手工复制目录的负担
- 交付物需要包含稳定的 member 分配入口，例如 `assign_member.py`
- 交付物需要包含高层子任务入口，例如 `create_subtask.py`
- 交付物需要包含成员讨论入口，例如 `create_discussion.py`、`post_discussion_message.py`、`resolve_discussion.py`
- 交付物需要包含 team leader 视角的状态面板能力，让 `render_summary.py` 能按 owner、任务类型、状态和阻塞态聚合展示
- 交付物需要说明 team leader 如何先让一个 member 分析拆解，再把执行工作分配给其他 member
- 交付物需要包含 workspace bootstrap、memory update 和 resume readiness 的长期 agent 入口，形成持续工作区和恢复能力
