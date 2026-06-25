# 团队 AI Memory Hub / Memory Gateway 落地方案

> 目标：让团队成员日常使用的不同 AI 开发工具（Claude Code、Cursor、Codex、Trae、Hermes 等）共享同一套团队记忆，而不是让各工具互相同步上下文。

---

## 1. 背景与目标

团队中每个人都在使用不同的 AI 开发工具。每个工具都有自己的上下文、规则文件、记忆机制和交互方式。如果不统一，长期会出现以下问题：

- 项目决策散落在不同人的聊天记录中。
- Claude Code 知道的上下文，Cursor 不知道。
- 某个 bad case 的经验只存在于某个人的会话里。
- AI 自动生成的错误经验被反复引用。
- 新成员无法快速继承团队已有经验。
- 旧规则、过期结论、临时假设混在一起，污染后续开发。

因此需要建设一个独立于具体工具的 **团队记忆层**。

核心原则：

```text
不是让 Claude Code 记住 Cursor 的东西，
也不是让 Cursor 直接同步 Trae 的上下文，
而是让所有 AI 开发工具共同连接到一个 Team Memory Gateway。
```

---

## 2. 总体架构

```text
Claude Code / Cursor / Codex / Trae / Hermes / OpenClaw
                         ↓
                  MCP / CLI / API
                         ↓
                 Team Memory Gateway
                         ↓
        ┌────────────────┬────────────────┬────────────────┐
        │ Markdown + Git │ Vector Search  │ Graph / Timeline│
        │ 人类可读与审计 │ 语义检索       │ 关系与演化追踪  │
        └────────────────┴────────────────┴────────────────┘
```

第一阶段不追求复杂系统，优先使用：

- Gitea 仓库作为团队记忆源。
- Markdown 作为正式记忆格式。
- inbox 机制承接 AI 自动生成的候选记忆。
- 人工 review 后进入正式记忆。
- Claude Code / Cursor / Codex / Trae 通过规则文件读取同一套记忆。
- 后续再加 MCP Server、向量检索和 Memory Gateway API。

---

## 3. 记忆分层

团队记忆不应该把所有聊天记录都同步，而应该只沉淀“长期有效、可复用、可验证”的知识。

### 3.1 Personal Memory：个人记忆

记录个人工作偏好、常用命令、熟悉模块、常见问题。

示例：

```text
某成员更熟悉 React 前端，对 Docker 和部署流程不熟。
某成员负责 Eval 模块，擅长指标设计，但需要提醒关注数据版本。
```

默认私有，除非本人同意共享。

---

### 3.2 Project Memory：项目记忆

记录项目事实、架构决策、模块边界、路线图。

示例：

```text
Agent OS 当前分为 Runtime、Skill、Eval、Simulator 四个核心模块。
Runtime 第一阶段不做复杂 DAG，先支持 loop + tool + eval hook。
Skill 更新必须经过 sandbox eval，不允许直接进入生产。
```

这部分应该团队共享。

---

### 3.3 Skill Memory：技能记忆

记录 skill 的版本、适用场景、失败案例、修复历史、评测结果。

示例：

```text
套电话术 skill v3 在抖音渠道风险升高。
原因：过早索要手机号，触发平台管控。
修复：先识别意向强度，低意向只做资料引导或弱转化。
```

这部分是 Agent OS 的核心资产，必须自主可控。

---

### 3.4 Eval Memory：评测记忆

记录评测集、指标、bad case、诊断结论、回归结果。

示例：

```text
客服 agent 在“客户明确拒绝”场景仍继续套电。
失败类型：合规风险 / 意图识别失败 / 策略未中止。
建议：新增拒绝意图 hard stop evaluator。
```

这部分适合结构化存储，后续可接 Postgres。

---

### 3.5 Organization Memory：组织记忆

记录团队规范、角色分工、会议结论、招聘标准、绩效指标。

示例：

```text
团队文化强调质疑 AI、快速验证、结果导向。
产品实习生需要优先熟悉 Runtime、Skill、Eval、Simulator 四个模块。
```

---

## 4. 哪些记忆可以共享

### 4.1 可以直接共享

- 项目架构决策
- 模块边界
- 接口约定
- 代码规范
- 常用命令
- PR 经验
- 客户规则
- 评测指标
- bad case 总结
- skill 更新记录
- agent 运行日志总结

---

### 4.2 不建议直接共享

- 个人偏好
- 个人草稿
- 临时代码思路
- 未验证方案
- 隐私信息
- 某个人与 AI 的完整对话上下文
- 带有情绪化判断的复盘

---

### 4.3 可以共享但必须审核

- AI 自动总结出的经验
- 某次 bad case 的原因
- 某个 skill 的改进建议
- 某段代码的长期设计判断
- 某个客户策略变化
- 某个模块未来方向

原则：

```text
AI 可以提交 memory candidate，
但不能直接写入正式 team memory。
```

---

## 5. 推荐仓库结构

在内网 Gitea 创建一个独立仓库：

```text
team-memory/
  README.md
  AGENTS.md

  inbox/
    memory-candidates.md
    candidate-template.md

  approved/
    project-memory.md
    skill-memory.md
    eval-memory.md
    org-memory.md

  project/
    agent-os-overview.md
    architecture-decisions.md
    module-boundaries.md
    roadmap.md

  runtime/
    design-notes.md
    api-contract.md
    known-issues.md

  skill/
    skill-design.md
    skill-evolution-log.md
    release-rules.md

  eval/
    metrics.md
    badcases.md
    regression-log.md
    evaluator-rules.md

  simulator/
    visitor-profile.md
    scenario-design.md
    simulation-rules.md

  org/
    team-principles.md
    coding-rules.md
    review-rules.md
    role-responsibilities.md

  members/
    README.md
    vayne.md
    intern-a.md
    intern-b.md

  deprecated/
    old-decisions.md

  conflicts/
    conflict-log.md
```

---

## 6. 统一入口：AGENTS.md

在项目根目录和 team-memory 仓库中都放置 `AGENTS.md`，作为不同 AI 工具的统一说明。

示例：

```markdown
# AGENTS.md

## 项目记忆规则

本项目的团队记忆位于 `./team-memory`。

开发前必须优先阅读：

1. `team-memory/project/agent-os-overview.md`
2. `team-memory/project/module-boundaries.md`
3. `team-memory/org/coding-rules.md`
4. 当前模块对应的 `design-notes.md`

## 记忆写入规则

AI 工具不得直接修改正式记忆文件，除非用户明确要求。

如果在开发过程中产生了长期有效经验，请先写入：

`team-memory/inbox/memory-candidates.md`

候选记忆必须包含：

- Scope
- Source
- Project
- Created at
- Proposed by
- Evidence
- Content
- Status

## 禁止写入

以下内容不得写入团队正式记忆：

- 未验证假设
- 个人隐私
- 情绪化评价
- 完整聊天记录
- 无来源的结论
- 已经过期但未标记的规则
```

---

## 7. 候选记忆模板

文件：`team-memory/inbox/candidate-template.md`

```markdown
## Memory Candidate: <一句话标题>

- Scope: project / runtime / skill / eval / simulator / org / personal
- Source: Claude Code / Cursor / Codex / Trae / Hermes / meeting / PR / eval
- Project: agent-os
- Created at: YYYY-MM-DD
- Proposed by: <name or tool>
- Confidence: low / medium / high
- Status: pending_review

### Content

<需要被团队长期记住的内容>

### Evidence

- <来自哪次 PR / 会议 / bad case / eval report / commit>

### Why it matters

<为什么这条记忆值得长期保存>

### Suggested destination

- `team-memory/project/architecture-decisions.md`
- `team-memory/skill/skill-evolution-log.md`
- `team-memory/eval/badcases.md`
- or others
```

---

## 8. 正式记忆模板

```markdown
## <记忆标题>

- Status: active / deprecated / conflict
- Scope: project / runtime / skill / eval / simulator / org / personal
- Owner: <owner>
- Since: YYYY-MM-DD
- Updated at: YYYY-MM-DD
- Source: <meeting / PR / eval / human decision>
- Evidence: <link or reference>

### Rule / Fact / Decision

<正式记忆内容>

### Reason

<为什么这样规定 / 为什么这个结论成立>

### Usage

<什么时候应该使用这条记忆>

### Expiration / Review

<是否需要定期复查，何时可能过期>
```

---

## 9. Claude Code 接入方式

### 9.1 在项目根目录加入 CLAUDE.md

```markdown
# CLAUDE.md

## 必读上下文

你正在协助开发 Agent OS 项目。

在进行任何代码修改、架构设计、评测设计、skill 设计之前，请优先阅读：

1. `team-memory/project/agent-os-overview.md`
2. `team-memory/project/module-boundaries.md`
3. `team-memory/org/coding-rules.md`
4. 当前任务所属模块的记忆文件：
   - Runtime: `team-memory/runtime/design-notes.md`
   - Skill: `team-memory/skill/skill-design.md`
   - Eval: `team-memory/eval/metrics.md`
   - Simulator: `team-memory/simulator/scenario-design.md`

## 记忆规则

当你发现长期有效的项目经验、架构约束、bad case、修复经验时，不要直接写入正式记忆。

请整理成 memory candidate，并追加到：

`team-memory/inbox/memory-candidates.md`

## 写入格式

使用 `team-memory/inbox/candidate-template.md` 中的格式。

## 禁止行为

- 不要把完整聊天记录写入 memory。
- 不要把未经验证的猜测写入正式 memory。
- 不要覆盖已有正式记忆，除非用户明确要求。
- 如果发现旧规则与新规则冲突，请写入 `team-memory/conflicts/conflict-log.md`。
```

---

### 9.2 给 Claude Code 的开发任务 Prompt

可以直接给 Claude Code：

```text
请基于当前仓库实现一个团队 AI Memory Hub v0.1。

目标：
1. 创建 team-memory 目录结构。
2. 创建 AGENTS.md、CLAUDE.md、README.md。
3. 创建候选记忆模板和正式记忆模板。
4. 创建 project/runtime/skill/eval/simulator/org 等模块的初始记忆文件。
5. 创建一个简单 CLI，支持：
   - memory add
   - memory list
   - memory review
   - memory approve
   - memory deprecate
6. 第一版只需要操作 Markdown 文件，不需要数据库。
7. 所有候选记忆先进入 team-memory/inbox/memory-candidates.md。
8. 正式记忆需要人工 approve 后进入对应 approved 或模块文件。
9. 请补充基础测试和 README 使用说明。

技术要求：
- 使用 Python 或 Node.js 均可，优先选择当前项目更适合的语言。
- 保持实现简单，可读性优先。
- 不要引入复杂外部依赖。
- 所有操作必须可回滚，避免覆盖已有内容。
```

---

## 10. Cursor 接入方式

在项目中增加 `.cursor/rules/team-memory.mdc`：

```markdown
# Team Memory Rules

开发本项目时，优先参考 `team-memory` 目录中的团队记忆。

必须遵守：

- 修改 Runtime 前，阅读 `team-memory/runtime/design-notes.md`
- 修改 Skill 前，阅读 `team-memory/skill/skill-design.md`
- 修改 Eval 前，阅读 `team-memory/eval/metrics.md`
- 修改 Simulator 前，阅读 `team-memory/simulator/scenario-design.md`
- 涉及架构判断时，阅读 `team-memory/project/architecture-decisions.md`

如果产生长期有效经验，请写入：

`team-memory/inbox/memory-candidates.md`

不要直接修改正式记忆。
```

---

## 11. Hermes 接入方式

Hermes 可以作为团队 memory 管家，支持以下命令：

```text
/memory recall agent-os runtime
/memory remember "Eval 模块新增 hard stop evaluator"
/memory review pending
/memory approve <candidate_id>
/memory deprecate <memory_id>
```

Hermes 的推荐职责：

- 每天汇总新增 memory candidate。
- 每周整理 bad case。
- 定期发现冲突记忆。
- 提醒哪些记忆可能过期。
- 将 agent 运行日志提炼为候选记忆。

---

## 12. CLI v0.1 设计

命令示例：

```bash
memory add --scope skill --source claude-code --content "Skill 更新必须先跑 regression eval"

memory list --status pending_review

memory review

memory approve --id mem_20260625_001 --to team-memory/skill/release-rules.md

memory deprecate --id mem_20260620_003 --reason "已被新规则替代"
```

第一版 CLI 只需要操作 Markdown 文件。

---

## 13. Memory Gateway API v0.2 设计

后续可以抽象成统一 API：

```text
POST /remember
POST /recall
POST /review
POST /approve
POST /deprecate
POST /conflict-check
```

### 13.1 remember

写入候选记忆。

```json
{
  "scope": "skill",
  "source": "claude-code",
  "project": "agent-os",
  "content": "修改客服 skill 后必须先通过 regression eval",
  "evidence": ["eval_case_20260622_001"],
  "confidence": "medium"
}
```

### 13.2 recall

按任务召回相关记忆。

```json
{
  "query": "修改 Eval 模块 hard stop evaluator",
  "scope": ["eval", "skill"],
  "project": "agent-os",
  "top_k": 5
}
```

### 13.3 approve

将候选记忆转为正式记忆。

```json
{
  "candidate_id": "mem_20260625_001",
  "destination": "team-memory/eval/evaluator-rules.md",
  "approved_by": "vayne"
}
```

---

## 14. 记忆数据结构

每条记忆建议至少包含以下字段：

```json
{
  "memory_id": "mem_001",
  "scope": "personal/project/skill/eval/org",
  "owner": "vayne",
  "project": "agent-os",
  "source": "claude-code / cursor / meeting / eval / pr",
  "content": "客服 skill v3 在低意向场景下不应继续套电",
  "tags": ["客服", "skill", "合规", "抖音"],
  "confidence": 0.86,
  "status": "active / deprecated / conflict / pending_review",
  "created_at": "2026-06-25",
  "updated_at": "2026-06-25",
  "expires_at": null,
  "evidence": ["eval_case_20260622_001"],
  "version": 1
}
```

---

## 15. Review 机制

每周安排一次 memory review。

Review 内容：

- 哪些候选记忆可以进入正式记忆？
- 哪些候选记忆证据不足，需要补充？
- 哪些记忆已经过期？
- 哪些记忆之间存在冲突？
- 哪些记忆被频繁使用，值得升级为规则？
- 哪些记忆从未被使用，是否需要清理？

候选记忆状态：

```text
pending_review：待审核
approved：已通过
declined：拒绝写入
deprecated：已废弃
conflict：存在冲突
private：个人私有
```

---

## 16. 冲突与过期机制

### 16.1 冲突记录

文件：`team-memory/conflicts/conflict-log.md`

```markdown
## Conflict: Runtime 是否支持复杂 DAG

- Found at: 2026-06-25
- Source A: `team-memory/project/architecture-decisions.md`
- Source B: `team-memory/runtime/design-notes.md`

### Conflict

A 文件中记录：Runtime 第一阶段不做复杂 DAG。
B 文件中记录：Runtime 需要支持 DAG 编排。

### Suggested action

需要确认当前阶段是否仍然坚持 loop + tool + eval hook，还是进入 DAG 版本。

### Status

pending_review
```

---

### 16.2 过期机制

以下类型记忆必须设置复查时间：

- 客户策略
- 平台规则
- 模型效果结论
- eval 指标阈值
- 业务转化策略
- 团队分工

---

## 17. 开发里程碑

### v0.1：Markdown + Git

目标：一周内落地。

功能：

- 创建 team-memory 仓库。
- 创建目录结构。
- 创建 AGENTS.md / CLAUDE.md。
- 创建候选记忆模板。
- 创建正式记忆模板。
- 提供基础 CLI 操作 Markdown。
- 支持 Claude Code、Cursor 读取同一套文件。

验收标准：

- Claude Code 能根据 CLAUDE.md 找到 team-memory。
- Cursor 能根据 rules 读取 team-memory。
- AI 产生的新经验会进入 inbox，而不是直接进入正式记忆。
- 人工可以 review 后合并到正式记忆。
- 所有变更都能通过 Git 追踪。

---

### v0.2：检索层

目标：2-4 周内落地。

功能：

- Markdown 文件切 chunk。
- 建立向量索引。
- 支持 `memory recall`。
- 根据当前任务召回相关记忆。
- 支持简单 API。

可选技术：

- Postgres + pgvector
- Qdrant
- Milvus
- Elasticsearch

---

### v0.3：Memory Gateway + MCP

目标：1-2 个月。

功能：

- 提供统一 Memory Gateway API。
- 提供 MCP Server。
- Claude Code / Cursor / Hermes / Codex 通过同一服务读写候选记忆。
- 增加权限、冲突检测、过期检测、使用统计。
- 接入 eval/bad case 系统。

---

## 18. 最容易踩的坑

### 18.1 把所有聊天记录都同步

不要同步完整聊天记录。聊天记录太脏，里面包含临时想法、错误判断、过期上下文、情绪化表达和 AI 胡说。

应该同步的是“被提炼后的记忆”。

---

### 18.2 没有状态

每条记忆必须有状态：

```text
pending_review
active
deprecated
conflict
private
```

---

### 18.3 没有来源

每条记忆必须有来源：

```text
来自哪次会议？
哪次 PR？
哪个 bad case？
哪个 eval report？
谁确认的？
```

没有来源的记忆，长期会变成团队谣言。

---

### 18.4 个人记忆和团队记忆混在一起

个人偏好可以辅助协作，但不能默认进入团队公共记忆。

建议分开：

```text
personal-memory/
team-memory/
project-memory/
```

---

### 18.5 只做 recall，不做 memory eval

团队记忆也会退化。

后续需要评估：

- 这条记忆有没有被使用？
- 使用后有没有提升效率？
- 有没有造成错误？
- 是否过期？
- 是否和新规则冲突？

---

## 19. Claude Code 第一阶段开发 Checklist

```text
[ ] 创建 team-memory 目录结构
[ ] 创建 README.md
[ ] 创建 AGENTS.md
[ ] 创建 CLAUDE.md
[ ] 创建 inbox/memory-candidates.md
[ ] 创建 inbox/candidate-template.md
[ ] 创建正式记忆模板
[ ] 创建 project/agent-os-overview.md
[ ] 创建 project/architecture-decisions.md
[ ] 创建 runtime/design-notes.md
[ ] 创建 skill/skill-design.md
[ ] 创建 eval/metrics.md
[ ] 创建 simulator/scenario-design.md
[ ] 创建 org/coding-rules.md
[ ] 创建 conflicts/conflict-log.md
[ ] 创建 deprecated/old-decisions.md
[ ] 实现 memory add
[ ] 实现 memory list
[ ] 实现 memory approve
[ ] 实现 memory deprecate
[ ] 增加 README 使用示例
[ ] 增加基础测试
```

---

## 20. 最终原则

一句话：

```text
不同 AI 开发工具不应该互相同步上下文，
而应该共享同一个团队记忆源。
```

当前最适合的落地方式：

```text
Gitea 上建 team-memory 仓库，
用 Markdown 管正式记忆，
用 inbox 管候选记忆，
用 AGENTS.md / CLAUDE.md / .cursor/rules 接入不同工具，
后续再加 MCP + 向量检索 + Memory Gateway。
```

这套方案的重点不是“记住更多”，而是：

```text
只记住值得长期复用、可验证、可审计、可演化的团队经验。
```
