# My Team 设计

## 设计概览

这个 skill 采用"team leader 编排 + member 执行 + artifact 持续落盘"的模式。

## Team Model

- `team leader` 只负责协调、分配、推进和汇报
- `member` 负责分析、设计、开发、测试等执行工作
- 默认先让一个 member 完成分析拆解，再由 team leader 继续分发实现与验证任务
- member 名称应与分配的任务类型匹配，例如 `member-analysis`、`member-design`、`member-coding`、`member-testing`，并已扩展到 `member-review`、`member-docs`、`member-release`、`member-integration`
- `member_role_name` 记录 canonical role，`owner_agent_id` 记录具体实例；因此同一个 role 可以并行多个实例，例如 `member-coding-1` 和 `member-coding-2`
- 如果工具返回了不同的系统昵称，team leader 在对外汇报、任务跟踪和交接时仍应使用任务类型匹配的角色名
- team leader 需要把任务分配给了谁、完成情况如何、还有哪些阻塞及时反馈给用户
- member 之间的直接讨论应通过 discussion artifact 进行，而不是无记录聊天；讨论必须能关联任务、参与者和最终决议
- 启动 my-team 模式后，除非收到退出指令，否则持续按该模式调度成员
- 在 VS Code Copilot 中，team leader 应使用 `runSubagent` 来调度真正的子 agent 执行 member 工作，而不是顺序地角色扮演不同成员；独立任务应并行发出多个 `runSubagent` 调用

## Workspace / Memory

- 长期 agent 需要一个用户确认过的 workspace 根目录（默认 `.my-team/`），用来保存跨任务、跨会话的长期状态
- 所有 skill 运行时文件统一放在 `.my-team/` 下，和项目自身文件隔离
- `TEAM.md` 负责长期协作契约和恢复规则
- `MEMORY.md` 负责保存事实、决策、偏好和约束
- `USER_CONTEXT.md` 负责保存 workspace、仓库、安装路径和环境约定
- `ROLES/` 负责保存 leader 和 member 的长期角色说明
- `INBOX.md` 负责保存待接收和待恢复工作
- `SESSIONS/current.md` 负责保存当前会话摘要
- `bootstrap_workspace.py` 应负责初始化 workspace skeleton
- `update_memory.py` 应负责把长期事实和决策追加到 memory 层
- `resume_readiness.py` 应负责判断 workspace 和 task 状态是否可恢复
- 临时日志继续走 `ai-chat/`、`events.jsonl` 和 task artifacts，workspace memory 只承载值得长期保留的信息

## 核心组成

- `scripts/`：CLI 脚本，实现任务初始化、状态更新、结构化文档写入、聊天归档、文档刷新与摘要渲染
- `assign_member.py`：把任务类型转换成标准 member 角色名，并可把成员分配写回任务状态；必要时可指定同 role 的具体实例 owner
- `create_subtask.py`：高层入口，用于一次性创建子任务、挂接父任务、分配 member、指定实例 owner 并初始化交接信息
- `create_discussion.py`：创建成员讨论，并记录模式、参与者、关联任务和主题
- `post_discussion_message.py`：向成员讨论追加消息流
- `resolve_discussion.py`：把讨论决议落盘，并同步回关联任务
- `render_summary.py`：用于输出 team leader 视角的状态面板，支持按 owner、任务类型、状态和阻塞态聚合，并能把同 role 的不同实例分开显示
- `bootstrap_workspace.py`：初始化长期 workspace 的 bootstrap 文件结构
- `update_memory.py`：把事实、决策、偏好和约束写入 workspace memory
- `resume_readiness.py`：在恢复前检查 workspace 和任务状态是否具备继续条件
- `references/`：给使用 skill 的 team leader 和 member 提供分析、设计与协议上下文
- `SKILL.md`：skill 入口，描述何时使用、读哪些参考文档、优先调用哪些脚本
- `README.md`：给用户看的安装说明、skill 名称与使用示例
- `install_skill.py`：把 skill 包安装到用户指定的 Codex skills 目录

## 命名与安装

- 当前包装固定使用 `my-team` 作为默认 skill 名称
- 安装路径使用 `$CODEX_HOME/skills/my-team`
- 安装后通过 `[$my-team](...)` 或名称提及来触发
- 安装副本包含 `install_skill.py` 与 `tests/`，可以自洽安装和验证
- 安装过程应优先通过安装脚本完成，而不是要求用户手工复制目录
- 工程目录保存的是源码和交付物，实际被 Codex 加载的 skill 应位于用户目录
- team leader 负责协调、管理和汇报，member 负责分析、设计、开发和测试
- team leader 可先委派一个 member 负责拆解，再把执行任务分配给其他 member
- team leader 在新的长期 workspace 中应先 bootstrap，再把 memory 更新和 resume readiness 作为恢复闭环的一部分
