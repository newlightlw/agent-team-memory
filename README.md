# Team Memory — 团队 Agent 记忆共享系统

> 让 **Claude Code / Codex / Trae / Hermes** 共享同一套团队记忆（Git 管理）。
> 加载、沉淀、检索、可视化、AI 动态读写。Markdown 即真相，零向量依赖。

版本 0.2.0 · [49 测试通过] · Mac / Linux / Windows

---

## 这是什么

把分散在各 AI 工具里的团队经验，汇聚到 **Git 管理的 Markdown 仓库**，让所有工具和成员读同一套上下文。四种接入方式、15 个命令、Web 可视化、MCP Server、CI 校验。

## 特性

- **四种接入**：全局 skill / CLI / Web UI / **MCP Server**（AI 对话中动态查/写）
- **15 命令**：`init` `capture` `propose` `review` `approve` `decline` `load` `sync` `list` `show` `web` `update` `doctor` `validate` `index`
- **inbox 候选审核**：AI 经验先进 inbox（pending），人工 approve 才转正式——防 AI 错误污染团队记忆
- **来源/版本追溯**：每条记忆带 `source`（哪个工具沉淀）/ `author` / git 版本历史
- **id 防撞号**：`mem-日期-{author}-序号`，每人独立序号空间，多人并发不撞
- **零向量依赖**：Markdown+Git 即真相（向量检索留 Phase 2）
- **CI 校验**：Gitea Actions PR 自动校验 frontmatter / id 唯一性
- **跨平台**：`onboard.py` + `python -m team_memory`（不依赖 PATH）

---

## 快速开始（单人 3 分钟）

```bash
git clone <repo> && cd agent-team-memory
pip install -e .                        # 装；要用 MCP 改成 -e ".[mcp]"
team-memory init -p ~/team-memory -n "团队名" -a <你的英文短名>
team-memory capture "首条记忆" -t decision --via claude --note "..."
team-memory web -p ~/team-memory        # 浏览器可视化 + 检索
```

---

## 团队部署（给团队用）

| 角色 | 文档（可交给 AI 工具执行） |
|---|---|
| **管理员**（一次性部署） | [docs/管理员操作清单.md](docs/管理员操作清单.md) |
| **组员**（每人接入） | [docs/组员操作清单.md](docs/组员操作清单.md) |
| 一页纸贴群 | [docs/快速参考卡.md](docs/快速参考卡.md) |

组员一键接入：
```bash
python scripts/onboard.py <Gitea仓库地址> <英文短名>
# Windows: python scripts/onboard.py ...
```

---

## 命令速查（15）

| 命令 | 作用 |
|---|---|
| `init` | 初始化记忆仓库（骨架 + git + Gitea remote） |
| `capture` | 沉淀**正式**记忆（已确认的经验） |
| `propose` | 提交**候选**记忆到 inbox（AI/未验证，待审） |
| `review` / `approve` / `decline` | 审核 inbox 候选 → 转正式 / 拒绝 |
| `load --global` | 桥接到 4 工具（claude/codex/hermes/trae）+ 装 auto-commit skill |
| `sync` | 同步 Gitea（pull --rebase + push，含冲突指引） |
| `list` / `show` | 查看记忆（表格 / 详情+版本历史） |
| `web` | Web 可视化（检索框 / 来源 / 时间 / 版本） |
| `update` | 更新记忆（原子；`--supersede` 标记废弃） |
| `doctor` / `validate` | 诊断 / 校验（CI 同款，坏文件/重复 id/过期/悬空引用） |
| `index` | 生成各类型 `_index.md` 索引 |

> 对话里说"**提交下**" → `auto-commit-memory` skill 自动总结、确认后提交。

---

## 四种接入方式

| 方式 | 场景 | 启用 |
|---|---|---|
| **MCP Server** | AI 对话中动态 search/get/propose/approve | `pip install -e ".[mcp]"` → 配置见 [docs/MCP接入.md](docs/MCP接入.md) |
| 全局 skill | 会话启动加载团队上下文 | `team-memory load --global` |
| CLI | 人工命令行操作 | `pip install -e .` |
| Web UI | 浏览器可视化 + 检索 | `team-memory web` |

四种方式都指向**同一个 Git 仓库**，可组合用。

---

## 核心工作流：capture vs propose

- **`capture`（正式）**：你**已确认**的经验 → 直接进 `memory/`（active）
- **`propose`（候选）**：**AI 自动总结 / 未验证**的经验 → 先进 `inbox/`（pending_review）→ `review` → `approve` 转正式

> **原则**：AI 可以 propose（候选），但**不直接写正式记忆**；approve 由人触发。
> 这样既给 AI 动态贡献能力，又守住人工审核关。

---

## 设计原则

1. **Git 是唯一真相**——Markdown 是事实来源；Web/MCP/skill 都是派生视图
2. **新写入下个会话才生效**——不污染当前对话
3. **废弃不删除**——`status: superseded` + `superseded_by` 链接新记忆
4. **AI 可建议写，不自动覆盖核心记忆**——project/decisions 走人工审核
5. **secrets 不入库**——`.env` / token / db 全部 gitignore

---

## 文档索引

| 文档 | 用途 |
|---|---|
| [系统说明.md](docs/系统说明.md) | 原理 / 工作流 / 何时触发存储与共享 |
| [管理员操作清单.md](docs/管理员操作清单.md) | 一次性部署（建仓库/推工具/CI/验收） |
| [组员操作清单.md](docs/组员操作清单.md) | 接入 + 日常使用 |
| [快速参考卡.md](docs/快速参考卡.md) | 一页纸贴群 |
| [MCP接入.md](docs/MCP接入.md) | AI 工具动态读写（MCP 配置） |
| [新人接入.md](docs/新人接入.md) | 详细 Q&A |
| [Gitea本地部署与迁移指南.md](docs/Gitea本地部署与迁移指南.md) | Gitea 底座部署 |
| [team_memory_gateway_for_claude_code.md](docs/team_memory_gateway_for_claude_code.md) | Gateway 方案（设计参考） |

---

## 开发

```bash
pip install -e ".[dev]"      # 含 pytest
pip install -e ".[mcp]"      # 含 MCP（可选）
pytest                       # 49 用例
```

Python ≥ 3.11。依赖：`typer` `rich` `pyyaml`（核心）；`mcp`（可选，仅 MCP Server）。
