# Team Memory — 团队 Agent Memory 共享系统

把分散在 **Cursor / Claude Code / Codex / Hermes** 中的记忆，统一汇聚到 **Gitea**，
让团队成员可以**加载团队记忆**并**沉淀经验**。

> Phase 1 走纯 Git 路线：Markdown + YAML frontmatter 是唯一真相，Gitea 承载版本管理。
> 不依赖向量数据库（早期 mem0 探索见 `test_mem0.py`，已不再使用）。

---

## 为什么需要它

平时同时用多个 AI coding 工具，每个工具都有自己的记忆（Cursor 的 `.cursorrules`、
Claude Code 的 `CLAUDE.md`/`MEMORY.md`、Codex 的 `AGENTS.md`、Hermes 的 Skill），
导致**上下文割裂**、经验无法复用、新人接手成本高。

本系统把"团队认知"压缩成一套 **Git 管理的 Markdown 记忆仓库**，所有工具读同一套上下文，
所有修改有版本、可审核、可回滚。

设计依据见 [`docs/`](docs/)：
- [`docs/团队记忆系统技术方案.md`](docs/团队记忆系统技术方案.md) — 四层记忆模型、五类记忆、Gitea 集成
- [`docs/claude_cursor_hermes_memory_share_plan.md`](docs/claude_cursor_hermes_memory_share_plan.md) — 三阶段落地路径

---

## 快速开始

```bash
# 1. 安装(开发模式)
cd agent-team-memory
pip install -e ".[dev]"

# 2. 在任意位置初始化一个团队记忆仓库(默认生成到 ./memory)
team-memory init

# 3. 沉淀一条记忆(自动生成 id、frontmatter、落盘)
team-memory capture -t decision "记忆系统采用纯 Git 路线"

# 4. 桥接到所有 AI 工具(Claude Code / Codex / Hermes / Trae 全局 skill)
team-memory load --global

# 5. (可选) 给单个项目生成项目级桥接(CLAUDE.md / AGENTS.md / .trae/rules)
team-memory load -t ../my-project

# 6. 同步到 Gitea(填好 .env 里的 GITEA_REMOTE_URL 后)
team-memory sync
```

---

## 目录结构

### 本仓库（工具本身）

```
agent-team-memory/
├── team_memory/          # Python CLI 工具
│   ├── cli.py            # 入口: init / capture / load / sync
│   ├── config.py         # 配置(.env → Config)
│   ├── models.py         # MemoryEntry + frontmatter 解析
│   ├── store.py          # 记忆仓库定位 + CRUD
│   ├── sources.py        # 多源聚合(team-memory + tencent-openclaw)
│   └── commands/         # 各命令实现
├── templates/            # 记忆模板(init 时拷贝到记忆仓库)
├── tests/                # pytest
└── docs/                 # 方案文档
```

### 记忆仓库（`team-memory init` 生成，独立 git、推 Gitea）

```
memory/
├── README.md             # 团队记忆说明
├── CLAUDE.md             # 团队级 Agent 指令(各工具桥接的源头)
├── rules/                # 团队规范(团队文化、代码标准)
├── memory/
│   ├── project/          # 项目记忆: 做什么、架构、约束
│   ├── decisions/        # 决策记忆(ADR)
│   ├── errors/           # 错误记忆: 现象、根因、排查、预防
│   └── skills/           # Skill 记忆: 已验证的可复用流程
├── templates/            # 模板
└── .env                  # Gitea remote 配置(不入库)
```

---

## 记忆数据模型

每条记忆统一为 YAML frontmatter + Markdown 正文，五类之一：

| 类型 | 目录 | 何时写 |
|---|---|---|
| `project` | `memory/project/` | 项目范围/架构变化时 |
| `decision` | `memory/decisions/` | 做出重要技术决策后(ADR) |
| `error` | `memory/errors/` | 解决非平凡错误后 |
| `skill` | `memory/skills/` | 验证可复用流程后 |

字段：`id`(mem-YYYYMMDD-NNN)、`type`、`scope`(team/project/module)、`author`、`role`、
`created`、`updated`、`expires`、`status`(active/deprecated/superseded)、`tags`、`related`。

> **废弃不删除**：更新 `status` 并链接到新记忆，保留旧的作为审计记录。

---

## 工具桥接（全局注册）

`team-memory load --global` 一次把记忆仓库注册到所有 AI 工具，所有项目自动可用：

| 工具 | 全局位置 | 方式 |
|---|---|---|
| Claude Code | `~/.claude/skills/team-memory/SKILL.md` | skill |
| Codex | `~/.codex/AGENTS.md` | 标记段（幂等，不破坏已有内容） |
| Hermes | `~/.hermes/skills/team-memory/SKILL.md` | skill（Hermes 只支持全局） |
| Trae | `~/.trae/skills/team-memory/SKILL.md` | skill |

未安装的工具会自动跳过。换记忆仓库路径后重跑 `load --global -p <新路径>` 即可更新所有工具的指向。

项目级桥接（不加 `--global`）：在指定项目生成 `CLAUDE.md` / `AGENTS.md` / `.trae/rules/team-memory.md`。

---

## 与现有 `sync-remote-memory` 的关系

你已有一套在跑的远程同步脚本（同步到 tencent-openclaw）。本系统**与之并存**：
- `team-memory` 作为**团队共享层**（本工具管理，推 Gitea）
- `tencent-openclaw` 作为**另一类源**（沿用现有脚本，不重写）
- `sources.py` 提供多源注册表，`load` 可聚合读取所有源（在 `.env` 配置 `TENCENT_OPENCLAW_PATH` 后启用）

---

## 设计原则

1. **Memory 先文件化，后服务化** — Markdown + Git，不急着上向量库/Memory Server
2. **Memory 是压缩后的共识，不是聊天记录** — 只存目标/决策/约束/经验
3. **Agent 可建议写，但不默认改核心记忆** — 写入走 Git + 人工审核
4. **新写入不在当前 session 生效** — 写入后下个会话才加载，避免污染当前对话
5. **secrets 全部 `.gitignore`** — `.env`、token、db 文件绝不入库

---

## 路线图

- **Phase 1（已完成）**：纯 Git，4 核心命令（init/capture/load/sync），**Claude / Codex / Hermes / Trae 四工具全局桥接**
- **Phase 1.5（下轮）**：`validate`/`index`/`search`（关键字）命令，Gitea CI 校验，项目级桥接增强
- **Phase 2（未来）**：可选 mem0 向量语义检索（MCP 只读层），Git 仍是唯一真相

---

## 开发

```bash
pip install -e ".[dev]"
pytest                    # 跑测试
pytest --cov=team_memory  # 覆盖率
```
