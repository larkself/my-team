# My Team

一个 AI agent 团队协作 skill，让 AI agent 能像一个团队一样工作：main agent as team leader 负责对外沟通和任务协调，团队成员各司其职完成分析、设计、编码、测试等工作。

安装后的 skill 名称：`my-team`（该名称固定，不提供重命名功能）。

## 功能特性

- **Team Leader + Member 协作模型**：team leader coordinating and reporting progress，Member 负责具体执行
- **真正的子 Agent 并行执行**：通过 `runSubagent` 调度独立的子 agent 执行成员工作，而非顺序角色扮演
- **member-first analysis**：Team Leader 优先委派一个 member 完成需求拆解，再分发实现任务
- **members handling analysis, design, coding, and testing**：同时支持 review/docs/release/integration 等扩展角色
- **8 种标准角色**：使用 task-type matched member names —— `member-analysis`、`member-design`、`member-coding`、`member-testing`、`member-review`、`member-docs`、`member-release`、`member-integration`
- **同角色多实例**：同一角色可并行多个实例（如 `member-coding-1`、`member-coding-2`）
- **成员间讨论机制**：支持 consult/sync 模式的结构化讨论，决议可回写关联任务
- **Workspace 持久层**：跨会话保持团队契约、记忆、角色说明等长期状态
- **统一 `.my-team/` 目录**：所有 skill 运行时文件放在项目根的 `.my-team/` 下，和项目自身文件隔离
- **任务全生命周期管理**：从 received → analysis → design → planning → executing → reporting → completed，支持 interrupted 和 revising
- **结构化 Artifact 落盘**：分析、设计、计划、结果等文档持续写入磁盘
- **检查点与恢复**：支持 checkpoint、revision 和 resume readiness 检查

## 目录结构

```
skill/
├── SKILL.md                # Skill 入口（被 Codex 加载）
├── README.md               # 本文件
├── install_skill.py        # Codex CLI 安装脚本
├── install_copilot.py      # GitHub Copilot 安装脚本
├── references/
│   ├── agent-protocol.md   # 操作协议和检查点规则
│   ├── analysis.md         # 产品分析和需求边界
│   └── design.md           # 设计说明
├── scripts/                # 25 个 CLI 工具脚本
│   ├── orchestrator_common.py
│   ├── init_task.py
│   ├── create_subtask.py
│   ├── assign_member.py
│   ├── update_state.py
│   ├── append_event.py
│   ├── update_step.py
│   ├── sync_task_doc.py
│   ├── write_artifact.py
│   ├── write_analysis.py
│   ├── write_design.py
│   ├── write_plan.py
│   ├── write_result.py
│   ├── checkpoint_task.py
│   ├── revise_task.py
│   ├── log_chat_turn.py
│   ├── suggest_doc_updates.py
│   ├── record_doc_refresh.py
│   ├── render_summary.py
│   ├── create_discussion.py
│   ├── post_discussion_message.py
│   ├── resolve_discussion.py
│   ├── bootstrap_workspace.py
│   ├── update_memory.py
│   └── resume_readiness.py
└── tests/
    ├── __init__.py
    └── test_scripts.py
```

## 安装

### 前提条件

- Python 3.8+

### 方式一：安装到 Codex CLI

适用于 [Codex CLI](https://github.com/openai/codex)，需要 `CODEX_HOME` 环境变量（默认 `~/.codex`）。

```bash
cd skill
python3 install_skill.py --codex-home "$CODEX_HOME"
```

覆盖已有安装：

```bash
python3 install_skill.py --codex-home "$CODEX_HOME" --force
```

安装完成后，skill 会被复制到 `$CODEX_HOME/skills/my-team/`。

### 方式二：安装到 GitHub Copilot (VS Code)

**个人级安装**（所有项目可用）：

```bash
cd skill
python3 install_copilot.py
```

安装到 `~/.copilot/skills/my-team/`。

**项目级安装**（仅当前项目可用，可提交到 git）：

```bash
cd skill
python3 install_copilot.py --project /path/to/your/project
```

安装到 `<项目根目录>/.github/skills/my-team/`。

覆盖已有安装：

```bash
python3 install_copilot.py --force
python3 install_copilot.py --project /path/to/your/project --force
```

### Source vs Installed Package

仓库根目录是源码权威来源；Codex 实际使用的 skill 副本应位于用户目录 `$CODEX_HOME/skills/my-team`。修改源码后需重新运行安装脚本才能生效。

### Recommended Defaults / Need User Confirmation

| 配置项 | 推荐默认值 | 是否需要用户确认 |
|--------|-----------|----------------|
| Skill 名称 | `my-team` | 否（固定） |
| 安装路径 | `$CODEX_HOME/skills/my-team` | 是（可通过 `--codex-home` 调整） |
| Workspace 根目录 | `.my-team/` (项目根目录下) | 是（首次使用时确认） |
| 用户文档语言 | 简体中文 | 否 |
| 内部笔记语言 | English | 否 |

### 验证安装

运行回归测试确认安装正确：

```bash
cd skill
python3 -m unittest discover -s tests -v
```

## 使用方法

### 启动 My Team 模式

在对话中提及 skill 名称即可激活。Use [$my-team](SKILL.md) 或直接描述工作：

**Codex CLI**：
```
请使用 [$my-team] 来帮我完成这个项目的开发。
```

**GitHub Copilot (VS Code)**：输入 `/my-team` 或在对话中描述工作让 Copilot 自动匹配：
```
我需要一个团队来帮我完成以下需求：...
```

### Team Leader 的工作方式

激活后，主 agent 会作为 Team Leader 运行：

1. **接收需求**：分析用户提出的任务，确认需要用户提供或确认的信息
2. **委派分析**：先用 `create_subtask.py` 创建分析子任务，再通过 `runSubagent` 调度一个真正的 `member-analysis` 子 agent 执行需求拆解
3. **分发任务**：根据分析结果，为每个实现/测试任务创建子任务并通过 `runSubagent` 分发给对应角色的 member；独立任务可**并行**调度
4. **协调推进**：跟踪各 member 进展，处理阻塞，协调成员间讨论
5. **汇报状态**：及时向用户报告进展、完成情况和阻塞项

### Workspace 初始化

对于需要跨会话持久化的长期任务，Team Leader 会先在项目根目录下初始化 `.my-team/` workspace：

```bash
python3 scripts/bootstrap_workspace.py --workspace .my-team
```

这会在 `.my-team/` 下创建 `TEAM.md`、`MEMORY.md`、`USER_CONTEXT.md`、`ROLES/`、`INBOX.md`、`SESSIONS/` 等持久化文件。任务状态保存在 `.my-team/orchestrator-state/` 下。

### 常用脚本说明

| 脚本 | 用途 |
|------|------|
| `init_task.py` | 初始化一个新任务 |
| `create_subtask.py` | 创建子任务（含父任务关联、成员分配、交接信息） |
| `assign_member.py` | 给任务分配标准角色成员 |
| `update_state.py` | 更新任务状态字段 |
| `update_step.py` | 管理任务步骤（添加/开始/完成/阻塞/取消） |
| `write_analysis.py` | 写入结构化分析文档 |
| `write_design.py` | 写入结构化设计文档 |
| `write_plan.py` | 写入结构化计划文档 |
| `write_result.py` | 写入结构化结果文档 |
| `checkpoint_task.py` | 创建任务检查点快照 |
| `create_discussion.py` | 创建成员间讨论 |
| `post_discussion_message.py` | 向讨论追加消息 |
| `resolve_discussion.py` | 记录讨论决议并同步回任务 |
| `render_summary.py` | 输出团队状态面板 |
| `bootstrap_workspace.py` | 初始化 workspace |
| `update_memory.py` | 更新长期记忆 |
| `resume_readiness.py` | 检查恢复就绪状态 |

### 退出 My Team 模式

激活后进入 persistent my-team mode，持续按团队模式调度。告诉 Codex 退出即可：

```
退出 my-team 模式。
```

### What The Agent Should Analyze First

Team Leader 在接到新任务后应先分析：

- 用户是否已确认 workspace 根目录
- 任务中哪些信息需要用户提供或确认
- 是否需要先委派 member-analysis 进行需求拆解

Team Leader 负责 assignment and completion feedback：向用户汇报每个任务分配给了谁、完成到了哪一步、还有什么阻塞。

Skill 使用 fixed skill name `my-team`，不支持重命名。

## 开发

### 项目结构

- `docs/task-flow-brief.md`：完整需求文档
- `skill/`：skill 包源码（即安装内容）

### 运行测试

```bash
cd skill
python3 -m unittest discover -s tests -v
```

### 修改后重新安装

修改 `skill/` 下的文件后，重新运行对应的安装脚本即可：

```bash
cd skill
# Codex CLI
python3 install_skill.py --codex-home "$CODEX_HOME" --force
# GitHub Copilot
python3 install_copilot.py --force
```
