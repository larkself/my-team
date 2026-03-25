# AI 团队协作系统需求简报：让 AI Agent 像一个团队一样工作

## 1. 项目名称

- 项目名称：AI 团队协作系统
- 英文代号：My Team

## 2. 背景与目标

### 2.1 项目背景

本项目的核心理念是：**让 AI Agent 像一个真实的团队一样工作**。

在真实团队中：

- 有一个 Team Leader 负责对外沟通、接收任务、汇报进展
- 有多个团队成员，各自承担不同角色（如架构师、开发者、测试、文档等）
- 成员主动从任务列表中领取任务，并负责细化和分工
- 成员之间可以相互讨论、协商、评审
- 每个角色按需可以有多个人，根据工作负载弹性分配
- 团队通过共享的任务看板和文档来保持信息同步

当前的 AI Agent 使用模式存在以下问题：

- 单个 Agent 难以处理大型复杂任务，上下文容易溢出
- 缺乏团队协作机制，Agent 之间无法有效分工和交流
- 没有持久化的任务状态，中断后难以恢复
- 缺少角色分工，所有事情都由同一个 Agent 混在一起处理
- 成员之间不能讨论和相互审查，质量难以保证

因此，需要构建一个 **AI 团队协作系统**，让多个 Agent 以团队的方式协作，明确区分：

- **Team Leader**：唯一对外接口，接收任务、分配工作、汇报状态
- **团队成员**：按角色分工，主动领取和细化任务，相互讨论协作
- **任务看板**：共享的任务列表，所有成员可见并可领取
- **讨论区**：成员之间的异步交流通道
- **Artifact 仓库**：所有产出物的持久化存储

### 2.2 核心目标

- 目标1：构建一个 "Team Leader 对外交互、团队成员按角色分工协作" 的 AI 团队系统
- 目标2：让团队成员能自主从任务列表中领取任务，细化和拆分子任务
- 目标3：支持成员之间的相互讨论、协商和评审机制
- 目标4：支持多角色定义，每个角色可按需配置多个实例
- 目标5：支持中断、恢复、交接，通过 artifact 落盘保持团队状态连续性
- 目标6：建立共享任务看板与 artifact 仓库，使团队工作可追踪、可恢复

## 3. 产品定位与使用场景

### 3.1 产品定位

这是一个让 AI Agent 以团队方式工作的协作系统。它的定位是：

- 作为 AI 团队的组织与协作框架
- 作为任务分发、领取、细化的共享看板
- 作为团队成员之间讨论与评审的交流平台
- 作为团队所有产出物的 artifact 持久化仓库
- 作为中断恢复和人员交接的基础设施

### 3.2 典型使用场景

- 用户向 Team Leader 提出一个复杂开发任务，Team Leader 分解后将子任务放入看板，团队成员按角色领取
- 架构师成员领取设计类任务，完成后发起讨论请开发者评审
- 多个开发者成员并行领取不同模块的实现任务
- 测试成员在开发完成后领取测试任务，发现问题后在讨论区与开发者沟通
- 用户在执行中途改变需求，Team Leader 更新任务看板，受影响的成员调整工作
- 某个成员因上下文中断，新的成员可以通过 artifact 和 handoff 文档接替工作
- Team Leader 汇总各成员工作成果，向用户报告整体进展

## 4. 核心角色与职责

### 4.1 Team Leader（团队负责人）

Team Leader 是团队唯一对外的接口，负责：

- 接收用户需求，理解并转化为团队可执行的任务
- 判断任务类型（新任务、修订、暂停、取消、汇总请求）
- 将任务拆分并发布到共享任务看板
- 分配优先级，标注任务间的依赖关系
- 监控团队整体进展，协调资源分配
- 汇总各成员的工作成果并对用户汇报
- 维护全局任务总账（ledger）
- 处理冲突、阻塞和升级事项
- 归档与用户的聊天记录
- 判断并触发团队级文档刷新
- **不亲自执行具体工作**：Team Leader 不应亲自编写代码、执行分析设计或运行测试，这些工作必须委派给成员
- **先分析后分发**：收到新任务后，应先委派一个成员负责分析和任务拆解，再根据拆解结果将执行工作分配给其他成员

### 4.2 团队成员（Team Members）

团队成员不直接面向用户，按角色分工协作。所有成员共享以下基本职责：

- **任务领取**：从共享看板中主动领取自己角色匹配的任务
- **任务细化**：将领取的任务进一步细化为可执行步骤
- **任务分工**：如果任务过大，可以拆分子任务并放回看板供其他成员领取
- **讨论协作**：通过讨论区与其他成员交流，发起评审请求或技术讨论
- **Artifact 维护**：维护自己负责的任务目录下的所有产出物
- **状态更新**：在关键节点更新任务状态、进度和事件日志
- **Handoff 支持**：在中断或交接时维护 handoff 文档，确保其他成员可以接手

### 4.3 角色定义

团队支持以下预定义角色（可按项目需求扩展）：

| 角色 | 英文标识 | 标准成员名 | 职责范围 | 可多实例 |
|------|---------|-----------|---------|---------|
| 分析师 | `analysis` | `member-analysis` | 需求分析、任务拆解、信息收集 | 是 |
| 架构师 | `design` | `member-design` | 系统分析、技术方案设计、架构评审 | 是 |
| 开发者 | `coding` | `member-coding` | 代码实现、单元测试、代码评审 | 是 |
| 测试员 | `testing` | `member-testing` | 测试计划、测试执行、缺陷报告 | 是 |
| 审查员 | `review` | `member-review` | 质量审查、方案评审、一致性检查 | 是 |
| 文档员 | `docs` | `member-docs` | 用户文档、API 文档、使用说明 | 是 |
| 发布员 | `release` | `member-release` | 构建打包、发布流程、版本管理 | 是 |
| 集成员 | `integration` | `member-integration` | 系统集成、接口联调、端到端验证 | 是 |

每个角色的关键特性：

- **按需多实例**：同一角色可以有多个成员同时工作（例如 3 个 developer 并行开发不同模块）
- **角色能力边界**：每个角色有明确的能力范围和可操作的 artifact 类型
- **角色切换**：在特殊情况下，一个成员可以临时承担其他角色的任务（需 Team Leader 授权）
- **标准命名**：创建或引用成员时，必须使用与任务类型匹配的标准角色名（如 `member-coding`），即使工具返回了不同的系统昵称，对外汇报和内部交接也应沿用标准角色名
- **`member_role_name` 与 `owner_agent_id` 分离**：`member_role_name` 代表角色的 canonical 标识，`owner_agent_id` 代表具体实例；同一角色的多个并行实例应保持 `member_role_name` 不变，通过不同的 `owner_agent_id` 区分，例如 `member-coding-1` 和 `member-coding-2`

### 4.4 用户

用户只与 Team Leader 交互，不直接管理团队成员。用户可以：

- 提出新任务
- 修改目标或范围
- 调整优先级
- 要求查看进度或输出结果
- 中断当前流程并要求重新规划

## 5. 核心工作流要求

### 5.1 标准任务生命周期

每个任务至少要支持以下阶段：

1. `received` — Team Leader 接收到用户需求
2. `published` — 任务已拆分并发布到看板
3. `claimed` — 某成员已领取该任务
4. `analysis` — 成员进行分析
5. `design` — 成员进行设计
6. `planning` — 成员制定执行计划
7. `executing` — 成员执行中
8. `reviewing` — 提交评审，其他成员讨论和审查
9. `reporting` — 汇总结果
10. `completed` — 完毕

同时要支持以下中断相关状态：

1. `interrupted` — 被中断
2. `revising` — 修订中
3. `blocked` — 被阻塞（等待其他任务或讨论结论）
4. `handoff` — 交接中（成员切换）

### 5.2 Team Leader 每轮必做动作

每次收到用户消息后，Team Leader 至少要执行：

1. 将用户消息归档到 `ai-chat/YYYY-MM-DD.md`
2. 如果 workspace 未初始化或缺少核心文件，先执行 workspace bootstrap（创建 `TEAM.md`、`MEMORY.md`、`USER_CONTEXT.md`、`ROLES/`、`INBOX.md`、`SESSIONS/current.md`）
3. 判断团队级文档是否过期，必要时刷新
4. 读取全局 `ledger.json`、`SESSIONS/current.md` 与任务看板状态
5. 先分析哪些信息需要用户提供或确认，并优先准备推荐值，同时把长期事实、偏好和约束写入 `MEMORY.md`
6. 判断用户意图（新任务 / 修订 / 查询进度 / 暂停 / 取消）
7. 如果是新任务：**先委派一个成员做分析与拆解**，再根据拆解结果将执行工作分配给其他成员
8. 如果是修订：checkpoint 当前状态，更新受影响任务
9. 检查看板上各任务的进展，收集成员的工作成果
10. 检查讨论区是否有需要裁决的问题
11. 同步更新 `ledger.json`
12. 基于 artifact 汇总结果后向用户输出，明确反馈"任务分配给了谁""当前完成情况""哪些任务仍在进行、等待或阻塞"
13. 将 Team Leader 回复追加到当天聊天日志
14. 一旦进入团队协作模式，持续按该模式执行，直到用户明确要求退出

### 5.3 团队成员每轮必做动作

每次团队成员开始工作时，至少要执行：

1. 查看共享任务看板，寻找匹配自己角色的可领取任务
2. 领取任务并更新看板状态为 `claimed`
3. 创建或加载所属任务目录
4. 判断任务级文档是否过期，必要时刷新
5. 细化任务：补充分析、设计、计划文档
6. 如果任务较大，拆分子任务并发布回看板
7. 在执行步骤前后更新状态、事件和进度日志
8. 需要其他成员协助时，在讨论区发起讨论
9. 完成后发起评审请求
10. 在中断或交接时更新 handoff 文档

### 5.4 成员间讨论机制

团队成员之间可以通过讨论区进行异步交流：

- **讨论模式**：支持 `consult`（咨询，向其他成员请教意见）和 `sync`（同步，多方对齐信息）两种模式
- **发起讨论**：任何成员可以针对某个任务或技术问题发起讨论
- **参与讨论**：相关角色的成员可以回复讨论，提供意见或建议
- **评审请求**：成员完成工作后可以请求其他成员评审
- **问题升级**：如果讨论无法达成一致，可以升级给 Team Leader 裁决
- **讨论归档**：所有讨论内容持久化存储，可追溯

讨论记录集中保存在 `team-state/discussions/` 目录下（与任务目录同级），每个讨论一个独立目录，包含 topic、messages、decision 和 state 等结构化文件。讨论可关联多个任务，便于跨任务协调。

## 6. Artifact 与目录结构要求

### 6.1 工程级目录

```text
# ── Workspace 持久化层（跨任务、跨会话的长期状态）──
TEAM.md                      # 长期协作契约、升级规则和 workspace 假设
MEMORY.md                    # 跨任务持久事实、决策、偏好和约束
USER_CONTEXT.md              # 已确认的用户环境、workspace 根目录和安装路径
ROLES/                       # 长期角色说明
  leader.md
  member-analysis.md
  member-design.md
  member-coding.md
  member-testing.md
  member-review.md
  member-docs.md
  member-release.md
  member-integration.md
INBOX.md                     # 待办、插单和恢复后续工作
SESSIONS/
  current.md                 # 当前会话摘要，帮助中断后快速恢复

# ── 聊天归档 ──
ai-chat/
  2026-03-25.md

# ── 编排状态层 ──
team-state/
  ledger.json                # 全局任务索引
  board.json                 # 共享任务看板
  roster.json                # 团队花名册（角色与成员实例）
  doc-refresh.jsonl          # 文档刷新记录
  discussions/               # 成员间讨论集中存储
    D-001/
      discussion.json        # 讨论元数据、参与者、关联任务
      messages.jsonl         # 讨论消息流
      decision.md            # 讨论决议
  tasks/
    T-001/
      task.md                # 任务目标、范围、依赖、验收标准
      analysis.md            # 中文分析文档
      design.md              # 中文设计文档
      plan.md                # 中文计划文档
      progress.log           # 追加式执行日志
      result.md              # 中文结果文档
      internal/
        brief.en.md          # 给 Agent 的英文执行摘要
        handoff.en.md        # 给 Agent 的英文交接说明（正式交接记录，非占位文件）
      state.json             # 任务当前快照
      steps.json             # 任务步骤状态
      events.jsonl           # 任务级事件流
```

### 6.2 文件职责

**Workspace 持久化层：**

- `TEAM.md`：长期协作契约，包含 Team Leader 的边界、恢复规则和升级规则
- `MEMORY.md`：跨任务持久化的事实、决策、偏好和约束（通过 `update_memory` 追加）
- `USER_CONTEXT.md`：已确认的用户环境、workspace 根目录和安装路径
- `ROLES/`：Team Leader 和各成员角色的长期说明，避免每次重新解释
- `INBOX.md`：待接收、插单和恢复后续工作
- `SESSIONS/current.md`：当前会话摘要，帮助团队在中断后快速恢复

**聊天与编排层：**

- `ai-chat/YYYY-MM-DD.md`：Team Leader 与用户的聊天归档
- `team-state/ledger.json`：全局任务索引、父子关系、状态摘要
- `team-state/board.json`：共享任务看板，包含所有待领取、进行中、已完成的任务卡片
- `team-state/roster.json`：团队花名册，记录当前活跃的角色实例及其状态
- `team-state/doc-refresh.jsonl`：文档刷新判断记录
- `team-state/discussions/D-xxx/`：成员间讨论集中存储，包含讨论元数据、消息流和决议

**任务级文件：**

- `task.md`：任务目标、范围、依赖、验收标准、当前状态、领取人
- `analysis.md`：中文分析文档
- `design.md`：中文设计文档
- `plan.md`：中文计划文档
- `progress.log`：追加式中文执行日志
- `result.md`：中文阶段性或最终结果
- `internal/brief.en.md`：给 Agent 的英文执行摘要
- `internal/handoff.en.md`：给 Agent 的英文交接说明（正式交接记录，必须描述剩余工作、阻塞点、下一步动作和所有权，不是脚手架占位文件）
- `state.json`：任务当前快照
- `steps.json`：任务步骤状态
- `events.jsonl`：任务级追加式事件流

### 6.3 语言分层要求

- 所有给用户看的文档必须使用简体中文
- 所有给 Agent 的内部文档默认使用英文
- 讨论记录使用简体中文（面向团队内部协作，但需用户可读）
- 状态文件必须使用 JSON / JSONL
- 不允许把 Agent 内部说明直接混入用户文档

## 7. 最小数据结构要求

### 7.1 `ledger.json`

必须至少支持：

- `schema_version`
- `updated_at`
- `tasks`

每个任务摘要至少包含：

- `task_id`
- `parent_task_id`
- `claimed_by` — 领取该任务的成员标识（角色+实例编号）
- `status`
- `phase`
- `revision`
- `goal`
- `scope`
- `priority`
- `required_role` — 该任务需要的角色类型
- `artifact_path`
- `updated_at`
- `child_task_ids`

### 7.2 `board.json`（任务看板）

任务看板是团队协作的核心，必须至少支持：

- `schema_version`
- `updated_at`
- `columns` — 看板列（如 `backlog`、`todo`、`in_progress`、`in_review`、`done`）

每个任务卡片至少包含：

- `task_id`
- `title`
- `required_role`
- `priority`
- `status`
- `claimed_by`
- `depends_on` — 依赖的其他任务 ID 列表
- `blocked_by` — 被阻塞的原因或任务 ID
- `created_at`
- `updated_at`

### 7.3 `roster.json`（团队花名册）

必须至少支持：

- `schema_version`
- `updated_at`
- `roles` — 角色定义列表

每个角色定义至少包含：

- `role_id` — 角色标识（如 `developer`）
- `display_name` — 显示名称
- `description` — 角色职责描述
- `max_instances` — 最大实例数（0 表示不限）
- `active_instances` — 当前活跃实例列表

每个实例至少包含：

- `instance_id` — 实例唯一标识（如 `developer-1`）
- `status` — 状态（`idle`、`working`、`interrupted`）
- `current_task_id` — 当前处理的任务
- `capabilities` — 能力列表

### 7.4 `state.json`

每个任务必须至少包含：

- `task_id`
- `parent_task_id`
- `claimed_by`
- `status`
- `phase`
- `revision`
- `goal`
- `scope`
- `priority`
- `required_role`
- `dependencies`
- `acceptance_criteria`
- `current_step_id`
- `discussions` — 关联的讨论 ID 列表
- `updated_at`

### 7.5 `steps.json`

必须至少包含：

- `task_id`
- `updated_at`
- `steps`

每个步骤项至少包含：

- `step_id`
- `title`
- `status`
- `assigned_to` — 执行该步骤的成员

### 7.6 `events.jsonl`

事件流必须支持追加写入，并至少能记录：

- 任务创建
- 任务发布到看板
- 任务被领取
- 阶段变更
- 步骤新增/开始/完成
- 讨论发起/回复/结论
- 评审请求/通过/打回
- 中断
- 交接
- 修订接受
- 文档刷新
- checkpoint
- artifact 更新

### 7.7 讨论记录 `team-state/discussions/D-xxx/`

讨论采用集中式存储，每个讨论一个独立目录，包含以下文件：

**`discussion.json`（讨论元数据）：**

- `discussion_id`
- `mode` — 讨论模式（`consult` 咨询 / `sync` 同步）
- `title` — 讨论主题
- `context` — 可选的背景说明
- `initiator` — 发起人（角色+实例）
- `participants` — 参与者列表
- `linked_task_ids` — 关联的任务 ID 列表（支持跨任务讨论）
- `status` — 当前状态（`open` / `resolved` / `escalated`）
- `created_at`
- `updated_at`

**`messages.jsonl`（讨论消息流，追加式）：**

- `sender` — 发言人
- `content` — 消息内容
- `timestamp`

**`decision.md`（讨论决议）：**

- 最终结论
- 决议依据
- 受影响的任务和后续动作

## 8. 关键业务规则

### 8.1 任务领取规则

- 成员只能领取与自己角色匹配的任务
- 同一任务同一时间只能被一个成员领取
- 成员领取任务时必须更新看板状态
- 如果成员发现任务超出能力范围，应放回看板并标注说明
- Team Leader 可以指定任务给特定成员（跳过自主领取）

### 8.2 讨论规则

- 讨论必须关联到具体任务
- 所有讨论内容必须持久化
- 讨论结论必须被记录并可追溯
- 超过一定轮次仍无共识的讨论应升级给 Team Leader
- 评审类讨论必须有明确的"通过"或"需修改"结论

### 8.3 必须落盘的时机

以下时刻必须写入磁盘：

- 任务发布到看板后
- 成员领取任务后
- 完成分析后
- 完成设计后
- 完成计划后
- 步骤开始前
- 步骤完成后
- 发起或回复讨论后
- 评审完成后
- 发现阻塞时
- 接收到中断时
- 接受修订后
- 最终汇报前
- 交接发生时

### 8.4 中断与修订规则

- 用户修改范围时，Team Leader 必须先 checkpoint，再修订任务
- 修订后必须更新 `revision`，并通知受影响的成员
- 不能把旧计划硬套到新需求上
- 已完成步骤应尽量保留，不应因轻微修订被无故丢弃
- 中断原因必须进入 `events.jsonl` 和 `progress.log`
- 成员中断时必须更新 handoff 文档，确保新成员可以接手
- 每个子任务都必须在 `team-state/tasks/<task-id>` 下有实体存档，`ledger.json` 只做索引，不能替代任务目录
- 如果父任务是通过子任务关系首次被发现（如子任务先于父任务创建），也必须为该父任务创建对应任务目录，保证恢复和审计可用

### 8.5 角色与并行度规则

- 每个角色的活跃实例数不超过 `roster.json` 中定义的 `max_instances`
- Team Leader 负责根据任务负载动态调整角色实例数
- 多个成员不应同时写同一个任务目录内的高冲突文件
- 同角色的多个实例应分配不同的任务，避免重复工作
- 默认并行度控制在 2-5 个活跃成员

### 8.6 文档刷新规则

系统必须支持两类文档刷新判断：

- 团队级：面向工程级说明、协议、测试等文档
- 任务级：面向具体任务的分析、设计、计划、结果和内部文档

刷新流程必须遵循：

1. 先判断哪些文档可能过期
2. 再刷新需要更新的文档
3. 最后记录判断与更新结果

不允许"悄悄改文档但没有记录"。

### 8.7 追加式历史规则

- `progress.log` 必须保留历史，不应覆盖旧记录
- `events.jsonl` 必须采用追加式写入
- 聊天日志必须按日期归档，并避免重复写标题
- 讨论记录必须保留完整对话历史
- 汇总结果应基于 artifact，而不是只依赖对话记忆

### 8.8 Team Leader 行为约束

- Team Leader 只负责协调、分配、推进和汇报，**不亲自编写代码、执行分析设计或运行测试**
- 收到新任务后，应先委派一个 `member-analysis` 成员做分析与拆解，再继续派发后续执行任务
- Team Leader 应持续向用户说明"谁在做什么""完成到了哪一步""哪些任务仍在进行、等待或阻塞"
- 一旦进入团队协作模式，应持续按该模式调度成员，直到用户明确要求退出
- Team Leader 在新的长期 workspace 中应先 bootstrap，再把 memory 更新和 resume readiness 作为恢复闭环的一部分

### 8.9 信息确认规则

- Team Leader 处理任何任务时，都必须先自主分析哪些信息需要用户提供或确认
- 如果能合理推断推荐值，应先给出推荐值，再请用户确认
- 如果当前任务涉及生成、安装或重命名 skill，skill 名称必须由 Team Leader 提出推荐方案，但最终由用户决定
- Team Leader 需要把"哪些信息已确认、哪些仍待确认"明确反映到产出文档中

### 8.10 Workspace 持久化规则

- Team Leader 应在首次长期会话前完成 workspace bootstrap，创建 `TEAM.md`、`MEMORY.md`、`USER_CONTEXT.md`、`ROLES/`、`INBOX.md`、`SESSIONS/current.md`
- 做出新的长期决策、确认新的偏好或收敛新的约束后，应通过 `update_memory` 更新 `MEMORY.md`
- 在重新接续任务或中断恢复前，应先执行 resume readiness 检查，确认 workspace 和任务状态是否具备继续条件
- 临时执行日志继续写入 `ai-chat/`、`events.jsonl` 和 task artifacts，workspace memory 只承载值得跨会话长期保留的信息
- `SESSIONS/current.md` 应在每次会话中保持更新，记录当前运行摘要

## 9. 输入输出与交互要求

### 9.1 输入类型

系统至少要能处理以下输入：

- 用户自然语言任务指令
- 用户修订说明
- 用户暂停 / 取消 / 汇总请求
- Team Leader 发给团队的任务说明
- 成员之间的讨论消息
- 成员提交的评审请求
- 结构化脚本参数输入

### 9.2 输出类型

系统至少要能输出：

- 给用户看的中文阶段文档和结果文档
- 给成员恢复用的英文 brief / handoff
- 结构化状态文件（看板、花名册、任务状态）
- 聊天日志
- 讨论记录
- 文档刷新日志
- 团队进展摘要
- 需要用户确认的信息清单及推荐值
- 可执行的安装脚本

### 9.3 CLI / 工具能力建议

为了让团队可稳定运作，建议至少提供以下脚本或同等能力：

- `bootstrap_workspace` — 初始化长期 workspace（创建 TEAM.md、MEMORY.md、USER_CONTEXT.md、ROLES/、INBOX.md、SESSIONS/current.md）
- `init_task` — 初始化任务目录和状态文件
- `create_subtask` — 一次性创建子任务，包含父子关系、成员分配和初始 handoff
- `assign_member` — 把任务类型转换为标准成员角色名并写入任务状态
- `update_state` — 更新任务状态
- `append_event` — 追加事件到事件流
- `update_step` — 更新步骤状态
- `sync_task_doc` — 同步任务文档
- `write_analysis` / `write_design` / `write_plan` / `write_result` — 结构化写入分析、设计、计划、结果文档
- `write_artifact` — 通用 artifact 写入
- `checkpoint_task` — 记录 checkpoint
- `revise_task` — 修订任务
- `create_discussion` — 创建成员间讨论（支持 consult / sync 模式）
- `post_discussion_message` — 向讨论追加消息
- `resolve_discussion` — 记录讨论决议并同步回关联任务
- `log_chat_turn` — 记录聊天日志
- `suggest_doc_updates` — 建议需要刷新的文档
- `record_doc_refresh` — 记录文档刷新结果
- `render_summary` — 渲染团队进展摘要（支持按 owner / 任务类型 / 状态分组，支持仅显示阻塞任务，支持按实例分离同角色的并行 worker）
- `update_memory` — 向 workspace memory 追加长期事实、决策、偏好和约束
- `resume_readiness` — 检查 workspace 和任务状态是否可安全恢复
- `install_skill` — 安装 skill 到目标目录

## 10. 测试与验收要求

### 10.1 最低测试覆盖

至少要验证以下场景：

- 初始化团队时能正确创建花名册和看板
- 任务发布到看板后，成员可以正确领取
- 同一任务不能被多个成员同时领取
- 成员可以发起讨论，其他成员可以回复
- 评审机制正常工作（请求/通过/打回）
- 角色多实例可以正确创建和管理
- 结构化写入 analysis / design / plan / result 正常
- checkpoint 后状态、修订版本和 handoff 正常更新
- 步骤新增、开始、完成能正确同步状态与摘要
- 聊天日志能按天写入且不重复标题
- 文档刷新判断能返回合理标记
- 交接场景下新成员可以基于 handoff 文档恢复工作
- 安装脚本能把 skill 安装到目标目录
- workspace bootstrap 能正确创建 TEAM.md、MEMORY.md、USER_CONTEXT.md、ROLES/ 等文件
- update_memory 能正确追加事实和决策到 MEMORY.md
- resume_readiness 能正确判断 workspace 和任务状态是否可恢复
- create_subtask 能一次性完成父子关系、成员分配和初始 handoff
- render_summary 能按 owner / 任务类型 / 状态正确分组聚合
- 讨论决议能正确同步回关联任务

### 10.2 核心验收标准

- 用户只需要和 Team Leader 对话
- 团队成员可以自主从看板领取任务并执行
- 成员之间可以通过讨论区有效交流
- 同一角色可以有多个实例并行工作
- 中断后可以基于磁盘 artifact 恢复
- 交接时新成员可以无障碍接手
- 任务和子任务关系可追踪
- 每个任务都有完整的中文用户文档与英文内部文档
- 任务状态、步骤、事件、讨论之间相互一致
- Team Leader 可以基于 artifact 输出可信的团队进展总结
- Team Leader 不亲自执行分析、设计、开发或测试工作
- Workspace 持久化层能跨会话保持团队长期状态
- 恢复就绪性检查能在中断后正确判断是否可以继续

## 11. 非功能要求

### 11.1 可恢复性

- 系统在多轮对话和中断后仍可恢复
- 不依赖单次上下文记忆作为唯一事实来源
- 任何成员中断后，其他成员或新实例可以通过 artifact 接手
- Workspace 层（TEAM.md、MEMORY.md、SESSIONS/current.md）提供跨会话的长期恢复能力
- 恢复前应先执行 resume readiness 检查，确认 workspace 和任务状态具备继续条件

### 11.2 可追踪性

- 能回答"任务何时变更、为什么变更、由谁触发"
- 能追踪分析、设计、计划和结果的更新时间
- 能定位 Team Leader 与各成员的职责边界
- 能回溯讨论过程和评审结论

### 11.3 可扩展性

- 后续可以新增更多角色类型
- 后续可以接入更多成员实例
- 后续可以扩展更复杂的任务分类和调度策略
- 后续可以增加更丰富的讨论和评审机制

### 11.4 可读性

- 用户文档应简洁、结构化、可直接阅读
- 内部文档应足够紧凑，便于 Agent 快速恢复上下文
- 讨论记录应结构清晰，便于回溯

## 12. 第一版边界与非目标

第一版明确不追求：

- 无限递归拆分子任务
- 成员完全自治，脱离 Team Leader 的协调
- 多个成员同时共享高冲突写入区域
- 数据库优先的复杂存储系统
- 完全实时的成员间通信（第一版使用异步讨论机制）
- 完全脱离用户监督的长期自治系统

## 13. 交付物要求

新项目第一版建议至少交付：

- 可运行的 AI 团队协作原型
- 完整的目录脚手架与状态文件约定（看板、花名册、任务目录）
- 一组可被 Agent 调用的 CLI 脚本或等价工具接口
- 用户可读的分析、设计、计划、结果模板
- 讨论与评审模板
- 聊天归档与文档刷新机制
- 回归测试
- 项目说明文档
- 可安装的 skill 包，至少包含 `SKILL.md`、配套 references 和安装/使用说明
- 一份说明哪些信息由 Agent 推荐、哪些信息需要用户确认的交付说明
- 一个可执行的安装脚本
- Workspace bootstrap 脚本和 memory / resume readiness 工具
- 成员分配脚本（`assign_member`）和子任务一次性创建入口（`create_subtask`）
- 成员讨论脚本（`create_discussion`、`post_discussion_message`、`resolve_discussion`）
- Team Leader 视角的状态面板（`render_summary`），支持多维聚合和阻塞过滤

## 14. 建议的实施顺序

建议按以下顺序开发：

1. 先实现 Workspace 持久化层：bootstrap、TEAM.md、MEMORY.md、USER_CONTEXT.md、ROLES/、INBOX.md、SESSIONS/
2. 再实现团队基础设施：花名册、任务看板、角色定义、成员分配
3. 然后实现任务发布、领取、状态流转和子任务一次性创建入口
4. 再实现成员间讨论和评审机制（集中式讨论存储、consult / sync 模式、决议同步）
5. 然后实现 artifact 写入与步骤/事件管理
6. 再实现聊天归档和文档刷新判断机制
7. 补充 checkpoint、中断恢复、resume readiness 检查、交接和任务修订
8. 最后补充团队摘要渲染（多维聚合）、memory 更新、回归测试和文档收尾

## 15. 一句话定义

这个项目的目标，是做一个"让 AI Agent 像一个真实团队一样工作"的协作系统——Team Leader 对外接收任务并汇报状态，团队成员按角色从看板领取任务并细化执行，成员之间可以相互讨论和评审，每个角色按需可有多个实例，全过程 artifact 落盘支持中断恢复和交接。
