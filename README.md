# Team Memory — 团队 Agent 记忆共享系统

让 Claude Code / Codex / Cursor / Trae / Hermes 等 AI coding 工具共享同一套团队长期记忆。

Team Memory 用 **Git 管理的 Markdown 仓库** 保存项目背景、技术决策、错误复盘和可复用流程。它不是聊天记录库，也不强依赖向量数据库；Markdown 是唯一真相，Git 提供版本、审核和回滚。

版本 0.3.0 · Python 3.11+ · macOS / Linux / Windows

## v0.3：GitHub 团队共享与一键成员接入

公开源码与私有团队记忆分开。新成员默认获取只读 Git 缓存与独立 MCP；个人材料先在本机准备，经本人审阅后才进入 Git 审核流程。

```sh
curl -fsSL https://raw.githubusercontent.com/newlightlw/agent-team-memory/v0.3.0/scripts/install.sh | bash -s -- --repo YOUR_ORG/team-shared-memory --author alice --tools codex
```

前置条件：Python 3.11+、Git，以及本人对私有库的访问权限。HTTPS 首次可用 `gh auth login` 和 `gh auth setup-git`。安装不使用 sudo，不覆盖原 MCP，失败立即停止；可选 Claude Code、Hermes 配置。完整的成员、管理员、飞书来源选材与回滚步骤见 **[GitHub 共享指南](docs/GITHUB_SHARING.md)**。

现有 Git 原生 CLI/Web/桥接保留。飞书团队服务继续保存自己的权威记录，进入 Git 的是经审阅的副本，不把 Git approve 当作双人共识。GitHub 历史也不能提供消息彻底撤回保证。

## 解决什么问题

当团队同时使用多个 AI coding 工具时，经验很容易散落在不同会话和不同工具里：

- Claude Code 知道的上下文，Codex 不知道。
- 这周解决过的错误，下周换个工具又要重新解释。
- 架构约束、历史决策、踩坑记录没有稳定入口。
- AI 可以总结经验，但不应该直接把未验证内容写成团队事实。

Team Memory 把这些经验沉淀为一个独立的 Git 仓库，让人和 Agent 都能读取、提交候选、审核和同步。

## 核心特性

- **Git + Markdown**：记忆文件人类可读、AI 可读、可 review、可回滚。
- **五类记忆**：`project` / `code` / `decision` / `error` / `skill`。
- **候选审核**：AI 产出先进 `inbox/`，人工 `approve` 后才进入正式 `memory/`。
- **跨工具桥接**：支持 Claude Code、Codex、Hermes、Trae 的全局 skill / 规则入口。
- **MCP Server**：AI 工具可在对话中动态 `search/get/list`，新只读 MCP 另支持本机私有草稿。
- **Web UI**：本地浏览、搜索、查看来源和版本历史。
- **安全保护**：防止把团队记忆误写进工具源码仓库；secrets 默认不入库。

## 5 分钟本地体验

这条路径不需要远端仓库，适合第一次试用。

```bash
git clone <THIS_REPO_URL>
cd agent-team-memory
python -m pip install -e .

# 初始化一个本地记忆仓库
team-memory init -p ~/team-memory -n "Demo Team" -a alice

# 写一条正式记忆。注意: 不在 agent-team-memory 目录里写记忆, 要用 -p 指向数据仓库
team-memory capture "采用 Git 管理团队记忆" \
  -t decision \
  --via codex \
  -p ~/team-memory \
  --note "团队长期记忆使用 Markdown 文件保存, Git 作为版本和审核机制。"

# 查看
team-memory list -p ~/team-memory
team-memory web -p ~/team-memory
```

如果你想让“写记忆 + git commit”一步完成，用 `save`：

```bash
team-memory save "记录一次可复用流程" \
  -t skill \
  --via claude \
  -p ~/team-memory \
  --note "任务完成后, 只沉淀未来会复用的结论, 不保存完整聊天记录。"
```

## 团队部署

团队通常需要两个仓库：

```text
agent-team-memory  工具仓库：CLI / Web / MCP / 模板 / 文档
team-memory        数据仓库：团队记忆 Markdown 文件
```

管理员初始化：

```bash
git clone <TOOL_REPO>
cd agent-team-memory
python -m pip install -e .

team-memory init -p ~/team-memory -n "<TEAM_NAME>" -a <admin>
cd ~/team-memory
git remote add origin <MEMORY_REPO>
git add .
git commit -m "init team memory"
git push -u origin HEAD
```

成员接入：

```bash
git clone <TOOL_REPO>
cd agent-team-memory
python scripts/onboard.py <MEMORY_REPO> <author>
```

更多细节：

| 文档 | 用途 |
| --- | --- |
| [管理员操作清单.md](docs/管理员操作清单.md) | 团队管理员初始化和验收 |
| [组员操作清单.md](docs/组员操作清单.md) | 成员接入和日常使用 |
| [快速参考卡.md](docs/快速参考卡.md) | 常用命令速查 |

## 记忆类型

| 类型 | 目录 | 适合记录 |
| --- | --- | --- |
| `project` | `memory/project/` | 项目目标、范围、架构、约束 |
| `code` | `memory/code/` | 代码结构、入口、模块关系、坑点 |
| `decision` | `memory/decisions/` | 技术选型、架构决策、ADR |
| `error` | `memory/errors/` | 错误现象、根因、修复方案 |
| `skill` | `memory/skills/` | 可复用流程、操作手册、实践方法 |

每条记忆都是带 frontmatter 的 Markdown：

```markdown
---
id: mem-20260706-alice-001
type: decision
scope: team
author: alice
source: codex
created: 2026-07-06
status: active
tags: [memory, git]
related: []
---

# 采用 Git 管理团队记忆

## Context
...

## Decision
...
```

## 工作流

```text
1. 开始任务前, Agent/成员读取相关记忆
2. 完成任务后, 提炼未来会复用的结论
3. 已确认经验用 capture/save 写入 memory/
4. AI 自动总结或未验证经验用 propose 写入 inbox/
5. 人工 review 后 approve/decline
6. commit + sync 推送到团队远端
7. 下一个会话加载新记忆
```

`capture` 和 `propose` 的区别：

| 命令 | 写到哪里 | 何时使用 |
| --- | --- | --- |
| `capture` | `memory/` | 人已确认的正式经验 |
| `save` | `memory/` + git commit | 想一步完成写入和提交 |
| `propose` | `inbox/` | AI 自动总结、证据不足、待审核内容 |

## 常用命令

```bash
# 初始化数据仓库
team-memory init -p ~/team-memory -n "Demo Team" -a alice

# 正式记忆
team-memory capture "标题" -t decision --via codex -p ~/team-memory --note "..."
team-memory save "标题" -t skill --via claude -p ~/team-memory --note "..."

# 候选记忆
team-memory propose "标题" -t error --via claude -p ~/team-memory --note "..."
team-memory review -p ~/team-memory
team-memory approve <memory-id> -p ~/team-memory
team-memory decline <memory-id> -p ~/team-memory --reason "证据不足"

# 查看和维护
team-memory list -p ~/team-memory
team-memory show <memory-id> -p ~/team-memory
team-memory update <memory-id> --note "补充说明" -p ~/team-memory
team-memory index -p ~/team-memory
team-memory doctor -p ~/team-memory
team-memory validate -p ~/team-memory

# 同步和可视化
team-memory sync -p ~/team-memory
team-memory web -p ~/team-memory

# 桥接到本机 AI 工具
team-memory load --global -p ~/team-memory
team-memory check-bridges -p ~/team-memory
```

## MCP 接入

安装可选依赖：

```bash
python -m pip install -e ".[mcp]"
TEAM_MEMORY_ROOT=~/team-memory python -m team_memory.mcp_server
```

MCP tools：

```text
search_memory(query, top_k=10)
get_memory(memory_id)
list_memories(type="")
propose_memory(title, type, source="", author="", confidence="medium", note="")
list_inbox(status="pending_review")
 # 审核仅由真人终端完成，不暴露 MCP approve
```

配置示例见 [MCP接入.md](docs/MCP接入.md)。

## 设计原则

1. **Git 原生长期知识以 Git 为准**；飞书原记录仍以团队服务为准。
2. **记忆保留作者与依据**：不保存完整聊天；审核入库不自动代表所有成员共识。
3. **AI 可以建议，正式记忆要审核**：候选先进 `inbox/`。
4. **新写入下个会话生效**：避免当前对话自我污染。
5. **废弃不删除**：用 `status: superseded` 和 `superseded_by` 追踪替代关系。
6. **secrets 不入库**：`.env`、token、密码、数据库文件默认忽略。

## 文档

| 文档 | 用途 |
| --- | --- |
| [系统说明.md](docs/系统说明.md) | 原理、架构、工作流 |
| [管理员操作清单.md](docs/管理员操作清单.md) | 团队管理员部署 |
| [组员操作清单.md](docs/组员操作清单.md) | 成员接入和日常使用 |
| [新人接入.md](docs/新人接入.md) | 更详细的新成员 Q&A |
| [快速参考卡.md](docs/快速参考卡.md) | 常用命令速查 |
| [MCP接入.md](docs/MCP接入.md) | MCP Server 配置 |

## 开发

```bash
python -m pip install -e ".[dev]"
PYTHONPATH=. pytest
```

当前 71 项测试通过：原 v0.2.3 的 58 项基线，以及 GitHub 同步、只读 MCP、配置保护和来源草稿等新增验证。分发安装另检查 wheel 模板与独立环境。

## License

MIT
