# Claude Code、Cursor、Hermes 记忆共享落地方案

## 1. 方案目标

你当前的核心诉求是：

- 平时同时使用 Claude Code、Cursor、Hermes 等 AI 工具；
- 希望它们共享同一套项目记忆，避免上下文割裂；
- 后续希望把这套个人记忆共享机制复用到团队级记忆管理；
- 需要方案可落地、可维护、可审计，而不是一开始就做复杂中台。

因此，推荐采用：

> **文件化 Memory + Git 版本管理 + 工具侧软链接/导入 + 人工审核机制**

第一阶段不要急着上向量数据库、RAG 服务或 Memory Server，而是先用 Markdown + Git 把“团队认知”沉淀下来。

---

## 2. 总体架构

```text
                    ┌────────────────────┐
                    │    Gitea 内网仓库    │
                    │  agent-os-memory    │
                    └─────────┬──────────┘
                              │
              ┌───────────────┼───────────────┐
              │               │               │
        ┌─────▼─────┐   ┌─────▼─────┐   ┌─────▼─────┐
        │ Claude    │   │ Cursor    │   │ Hermes    │
        │ Code      │   │ Rules     │   │ Skill     │
        └─────┬─────┘   └─────┬─────┘   └─────┬─────┘
              │               │               │
              └───────────────┼───────────────┘
                              │
                    ┌─────────▼─────────┐
                    │   Agent OS 项目    │
                    │   .memory 软链接   │
                    └─────────┬─────────┘
                              │
                    ┌─────────▼─────────┐
                    │  人工 Review / PR  │
                    └───────────────────┘
```

这套方案的本质是：

> **用 Git 承载团队长期记忆，用 Markdown 保持可读性，用 Claude Code、Cursor、Hermes 分别消费同一套上下文，用 PR 保证记忆质量。**

---

## 3. Memory 仓库设计

建议在内网 Gitea 上新建仓库：

```bash
agent-os-memory/
```

这个仓库不是代码仓库，而是团队和 Agent 共用的“工作记忆仓库”。

它需要满足：

- 人能直接阅读；
- AI 工具能读取；
- 所有修改有 Git 记录；
- 可以通过 PR 审核；
- 可以回滚历史版本；
- 后续可以升级为 RAG、向量检索或 Memory 服务。

---

## 4. 推荐目录结构

```bash
agent-os-memory/
├── README.md
├── global/
│   ├── team_principles.md
│   ├── coding_standards.md
│   ├── ai_workflow.md
│   └── glossary.md
│
├── projects/
│   └── agent-os/
│       ├── project.md
│       ├── architecture.md
│       ├── roadmap.md
│       ├── decisions.md
│       ├── constraints.md
│       ├── open_questions.md
│       ├── eval_rules.md
│       ├── skill_inventory.md
│       └── changelog.md
│
├── roles/
│   ├── backend.md
│   ├── frontend.md
│   ├── fullstack.md
│   ├── product.md
│   └── data_eval.md
│
├── workflows/
│   ├── daily_dev.md
│   ├── pr_review.md
│   ├── bug_fix.md
│   ├── feature_design.md
│   ├── eval_iteration.md
│   └── skill_update.md
│
├── people/
│   ├── vayne.md
│   ├── intern_a.md
│   └── intern_b.md
│
├── templates/
│   ├── decision_record.md
│   ├── skill_card.md
│   ├── eval_case.md
│   ├── bug_report.md
│   └── weekly_summary.md
│
└── tools/
    ├── claude-code.md
    ├── cursor.md
    └── hermes.md
```

注意：不要把所有内容都塞进一个 `memory.md`。记忆需要按类型拆开，否则后期会很难维护。

---

## 5. Memory 类型划分

### 5.1 全局记忆

路径：

```bash
global/
```

用于存放所有项目、所有成员都应该遵守的长期共识。

例如：

```bash
global/team_principles.md
global/coding_standards.md
global/ai_workflow.md
```

适合记录：

- 团队开发原则；
- AI Native 工作方式；
- 代码风格；
- AI 工具使用边界；
- 什么情况下必须写评测；
- 什么情况下必须先问人类。

---

### 5.2 项目记忆

路径：

```bash
projects/agent-os/
```

这是最核心的目录，用于记录 Agent OS 项目的目标、架构、约束、决策、评测规则等。

重点维护：

```bash
project.md
architecture.md
roadmap.md
decisions.md
constraints.md
open_questions.md
eval_rules.md
skill_inventory.md
```

---

### 5.3 工作流记忆

路径：

```bash
workflows/
```

用于记录团队怎么做事。

例如：

```bash
workflows/daily_dev.md
workflows/pr_review.md
workflows/eval_iteration.md
workflows/skill_update.md
```

它可以告诉 AI：

- 开发前需要读哪些记忆；
- 修改代码后要补什么文档；
- 涉及评测时要怎么验证；
- 涉及 Skill 更新时要怎么回归。

---

### 5.4 角色记忆

路径：

```bash
roles/
```

用于记录不同角色的职责边界。

例如：

```bash
roles/fullstack.md
roles/product.md
roles/data_eval.md
```

适合用于团队管理和实习生考核。

---

### 5.5 个人记忆

路径：

```bash
people/
```

用于记录成员在工作中的长期上下文。

例如：

```bash
people/vayne.md
people/intern_a.md
people/intern_b.md
```

注意：个人记忆只建议记录工作相关内容，例如：

- 负责模块；
- 工作偏好；
- 当前重点；
- 常犯问题；
- 协作方式。

不建议记录隐私信息。

---

## 6. 核心文件模板

### 6.1 `project.md`

```md
# Agent OS 项目记忆

## 项目目标

构建一个面向客服 Agent 的自进化系统，通过 Runtime、Skill、Eval、Simulator 四个模块，实现从对话生成、评估、诊断、优化到验证的闭环。

## 当前阶段

MVP 阶段，优先跑通单科室、单渠道、单业务目标下的最小闭环。

## 当前重点

1. Runtime：支持 Agent 对话流程编排；
2. Eval：支持对话质量评估；
3. Simulator：支持访客画像模拟；
4. Skill：支持客服话术策略结构化沉淀。
```

---

### 6.2 `architecture.md`

```md
# Agent OS 架构记忆

## 核心模块

- Runtime：负责 Agent 执行、状态流转、工具调用；
- Skill：负责策略、话术、行为规范沉淀；
- Eval：负责对话质量、留资概率、违规风险评估；
- Simulator：负责生成模拟访客、模拟对话环境。

## 当前架构原则

1. 先文件化，不急于数据库化；
2. 先人工审核，不做全自动发布；
3. Eval 先规则 + LLM 混合，不追求一步到位；
4. Skill 更新必须经过验证集回归。
```

---

### 6.3 `decisions.md`

```md
# 决策记录

## 2026-06-23：Memory 先采用文件化方案

### 背景

团队同时使用 Claude Code、Cursor、Hermes，直接做统一 Memory 服务成本较高。

### 决策

先使用 Git 管理 Markdown Memory，工具侧通过软链接或引用方式读取。

### 原因

- 成本低；
- 可审计；
- 可版本回滚；
- 方便团队协作；
- 后续可升级为 RAG 服务。

### 暂不做

- 暂不引入复杂向量数据库；
- 暂不做全自动记忆写入；
- 暂不允许 Agent 自动覆盖核心记忆。
```

---

### 6.4 `constraints.md`

```md
# 项目约束

## 技术约束

- 当前优先支持内网环境；
- 代码托管使用 Gitea；
- Memory 以 Markdown 为主；
- 不依赖外部 SaaS。

## 业务约束

- 客服策略必须可解释；
- 涉及客户话术更新必须人工审核；
- 不能为了留资而违反平台规则；
- 抖音渠道必须加强套电合规控制。
```

---

### 6.5 `open_questions.md`

```md
# 待讨论问题

## Eval 模块

- 留资率预测是否应该独立成一个 reward model？
- LLM 评估器和规则评估器的权重如何分配？
- 模拟访客生成的数据是否会过拟合当前 Skill？

## Skill 模块

- Skill 是按科室拆，还是按意图拆？
- Skill 更新是否要引入灰度发布？
```

---

### 6.6 `daily_dev.md`

```md
# 日常开发工作流

## 开发前

1. 先阅读项目记忆：
   - projects/agent-os/project.md
   - projects/agent-os/architecture.md
   - projects/agent-os/constraints.md

2. 明确当前任务属于：
   - 新功能；
   - Bug 修复；
   - 重构；
   - 评测优化；
   - Skill 更新。

## 开发中

1. 小步提交；
2. 每次改动必须说明影响范围；
3. 涉及核心逻辑必须补充测试；
4. 涉及 Agent 行为必须补充 Eval Case。

## 开发后

1. 更新 changelog.md；
2. 如产生新决策，更新 decisions.md；
3. 如发现新问题，更新 open_questions.md。
```

---

## 7. Claude Code 接入方式

在 Agent OS 项目根目录放一个 `CLAUDE.md`。

项目结构示例：

```bash
agent-os/
├── CLAUDE.md
├── src/
├── tests/
└── ...
```

建议先在项目中创建软链接：

```bash
cd agent-os
ln -s ../agent-os-memory .memory
```

然后 `CLAUDE.md` 内容可以这样写：

```md
# Claude Code 工作说明

你正在协助开发 Agent OS 项目。

请优先阅读以下共享记忆：

- .memory/global/team_principles.md
- .memory/global/coding_standards.md
- .memory/projects/agent-os/project.md
- .memory/projects/agent-os/architecture.md
- .memory/projects/agent-os/constraints.md
- .memory/projects/agent-os/decisions.md
- .memory/workflows/daily_dev.md

## 工作规则

1. 不要绕过共享记忆中的架构约束。
2. 如果发现代码和记忆冲突，先指出冲突，不要直接修改。
3. 如果产生新的架构决策，请建议更新 decisions.md。
4. 如果发现未解决问题，请建议更新 open_questions.md。
5. 涉及 Eval、Skill、Simulator 的改动，必须说明验证方式。
```

---

## 8. Cursor 接入方式

Cursor 可以通过项目内规则文件接入。

目录示例：

```bash
agent-os/
├── .cursor/
│   └── rules/
│       ├── memory.mdc
│       ├── coding.mdc
│       └── eval.mdc
```

`memory.mdc` 可以这样写：

```md
---
description: Shared memory rules for Agent OS
alwaysApply: true
---

# Shared Memory

Before modifying code, refer to the shared memory files:

- .memory/projects/agent-os/project.md
- .memory/projects/agent-os/architecture.md
- .memory/projects/agent-os/constraints.md
- .memory/projects/agent-os/decisions.md
- .memory/workflows/daily_dev.md

When your change introduces a new architectural decision, suggest an update to:

- .memory/projects/agent-os/decisions.md

When your change exposes an unresolved issue, suggest an update to:

- .memory/projects/agent-os/open_questions.md
```

这样 Cursor 和 Claude Code 都会读取同一套 `.memory`。

---

## 9. Hermes 接入方式

Hermes 更适合把共享记忆封装成 Skill。

示例路径：

```bash
~/.hermes/skills/agent-os-memory/SKILL.md
```

内容示例：

```md
---
name: agent-os-memory
description: 读取和维护 Agent OS 项目的共享记忆，包括架构、决策、约束、工作流和评测规则。
---

# Agent OS Memory Skill

## 使用场景

当用户进行 Agent OS 项目的开发、评测、Skill 设计、Simulator 设计、Runtime 设计、团队协作设计时，必须优先使用本 Skill。

## 共享记忆位置

共享记忆仓库路径：

/path/to/agent-os-memory

重点读取：

- global/team_principles.md
- global/coding_standards.md
- projects/agent-os/project.md
- projects/agent-os/architecture.md
- projects/agent-os/constraints.md
- projects/agent-os/decisions.md
- projects/agent-os/eval_rules.md
- projects/agent-os/skill_inventory.md
- workflows/daily_dev.md
- workflows/eval_iteration.md
- workflows/skill_update.md

## 工作规则

1. 回答前先参考共享记忆。
2. 不要擅自改写核心决策。
3. 如发现新决策，建议追加到 decisions.md。
4. 如发现新问题，建议追加到 open_questions.md。
5. 涉及 Skill 更新时，必须说明评测和验证方式。
6. 涉及客服话术更新时，必须考虑合规风险。
```

Hermes 更适合承担：

- 记忆整理；
- 周报总结；
- Skill 生成；
- Eval Case 生成；
- 对话诊断；
- 决策沉淀。

Claude Code 和 Cursor 更适合承担代码开发。

---

## 10. Memory 写入权限设计

不要允许 Agent 随便写核心记忆，否则 Memory 会很快变成幻觉垃圾堆。

建议把记忆分成三类权限。

---

### 10.1 A 类：核心共识记忆

包括：

```bash
project.md
architecture.md
constraints.md
decisions.md
eval_rules.md
```

规则：

- 只能人工审核后修改；
- AI 可以提议修改；
- 不允许 AI 自动覆盖；
- 通过 PR 合并；
- 由项目负责人最终把关。

---

### 10.2 B 类：过程记忆

包括：

```bash
changelog.md
open_questions.md
weekly_summary.md
bug_report.md
```

规则：

- AI 可以生成草稿；
- 人可以快速确认；
- 可以低门槛合入；
- 主要用于记录过程和复盘。

---

### 10.3 C 类：个人记忆

包括：

```bash
people/vayne.md
people/intern_a.md
people/intern_b.md
```

规则：

- 本人可改；
- Leader 可建议；
- 不建议公开敏感内容；
- 只记录工作习惯、负责模块、当前上下文。

示例：

```md
# Vayne 工作记忆

## 角色

Agent OS 项目主导者，负责整体架构、产品方向、评测体系、团队 AI Native 工作流。

## 偏好

- 希望方案先能落地，再追求复杂架构；
- 喜欢文件化、可审计、可复用的系统；
- 强调 Eval、Skill、Simulator、Runtime 四模块闭环；
- 不喜欢空泛的概念设计。

## 当前关注

- Agent OS MVP；
- 团队 Memory 共享；
- 客服 Agent 自进化；
- AI Native 团队协作机制。
```

---

## 11. 三阶段落地路径

## 阶段一：个人版跑通

目标：先让你自己的 Claude Code、Cursor、Hermes 共用一套 Memory。

周期：1 天内可以完成。

### 步骤 1：新建 Memory 仓库

```bash
mkdir agent-os-memory
cd agent-os-memory
git init
```

初始化目录：

```bash
mkdir -p global projects/agent-os roles workflows people templates tools
```

### 步骤 2：先写 6 个核心文件

```bash
global/team_principles.md
projects/agent-os/project.md
projects/agent-os/architecture.md
projects/agent-os/decisions.md
projects/agent-os/constraints.md
workflows/daily_dev.md
```

### 步骤 3：在 Agent OS 项目里创建软链接

```bash
cd ../agent-os
ln -s ../agent-os-memory .memory
```

### 步骤 4：配置 Claude Code

在项目根目录新增：

```bash
CLAUDE.md
```

### 步骤 5：配置 Cursor

新增：

```bash
.cursor/rules/memory.mdc
```

### 步骤 6：配置 Hermes Skill

新增：

```bash
~/.hermes/skills/agent-os-memory/SKILL.md
```

完成后，你个人的三套工具就能共享同一套记忆。

---

## 阶段二：团队版试点

目标：让 2 个全栈实习生也使用这套 Memory。

周期：3 到 5 天。

团队成员本地 clone：

```bash
git clone <你的内网gitea地址>/agent-os-memory.git
git clone <你的内网gitea地址>/agent-os.git
```

然后在项目里软链接：

```bash
cd agent-os
ln -s ../agent-os-memory .memory
```

团队硬规则：

```md
# 团队 Memory 使用规则

1. 开发前必须阅读 .memory/projects/agent-os/project.md 和 architecture.md。
2. 修改核心模块前，必须检查 decisions.md 是否已有相关决策。
3. 遇到架构分歧，不允许直接拍脑袋改代码，先更新 open_questions.md。
4. 每次完成一个功能，必须补充 changelog.md。
5. 涉及 Eval、Skill、Simulator 的改动，必须补充对应的验证说明。
```

这套规则不仅能帮助协作，还能用于实习生能力考核，观察他们是否具备：

- 上下文理解能力；
- AI 协作能力；
- 遵守团队记忆的能力；
- 沉淀经验的能力；
- 把问题转化为可复用资产的能力。

---

## 阶段三：升级为团队 Memory 管理机制

当个人和小团队跑通后，再升级为正式团队机制。

### 1. Memory PR 机制

所有重要 Memory 修改都走 PR。

分支命名示例：

```bash
feature/update-eval-rules
feature/add-simulator-decision
feature/update-skill-inventory
```

PR 模板：

```md
## 修改了什么

## 为什么修改

## 影响哪些模块

## 是否和已有决策冲突

## 是否需要同步到 Claude/Cursor/Hermes
```

这样 Memory 就不是散乱笔记，而是团队认知资产。

---

### 2. 每周 Memory Review

每周固定 30 分钟做一次 Memory Review。

检查：

- decisions.md 是否过期；
- open_questions.md 是否有问题已经解决；
- architecture.md 是否和代码不一致；
- skill_inventory.md 是否需要更新；
- eval_rules.md 是否需要补充。

Memory 最大的问题不是没写，而是写了之后没人维护，慢慢变成错误上下文。

---

### 3. 自动生成 Memory Draft

可以让 Hermes 或 Claude Code 做一个命令：

```bash
/memory summarize this week
```

输出：

```md
## 本周新增决策

## 本周修改模块

## 本周发现的问题

## 建议更新的 Memory 文件

## 需要人工确认的地方
```

注意：自动生成的是 draft，不是自动合入。

---

### 4. Memory Lint

后续可以做一个简单脚本：

```bash
memory-lint
```

检查内容：

- 是否有超过 30 天未更新的核心文件；
- decisions.md 是否有未填写原因的决策；
- open_questions.md 是否有长期未关闭的问题；
- architecture.md 是否引用了已经不存在的模块；
- skill_inventory.md 是否和实际代码不一致。

这一步会让你的团队 Memory 管理机制逐渐系统化。

---

## 12. 工具分工建议

| 工具 | 核心用途 | Memory 使用方式 |
|---|---|---|
| Claude Code | 深度代码开发、重构、测试 | 读取项目架构、约束、决策 |
| Cursor | 日常编码、局部修改、快速补全 | 读取规则、代码规范、模块上下文 |
| Hermes | 记忆整理、周报、Skill、诊断、复盘 | 读取全量 Memory，并生成更新建议 |
| Gitea | Memory 版本管理、团队协作 | PR、Review、历史追踪 |

个人工作流可以设计为：

```text
Claude Code / Cursor 负责做事
Hermes 负责总结和沉淀
Gitea 负责审计和同步
Memory 仓库负责长期复用
```

---

## 13. 最小可行版本

如果不想一开始做得太复杂，建议先只维护 8 个文件：

```bash
agent-os-memory/
├── README.md
├── global/
│   ├── team_principles.md
│   └── coding_standards.md
├── projects/
│   └── agent-os/
│       ├── project.md
│       ├── architecture.md
│       ├── decisions.md
│       ├── constraints.md
│       └── open_questions.md
└── workflows/
    └── daily_dev.md
```

这个版本已经足够个人使用，也足够两个实习生试点。

---

## 14. 关键设计原则

### 1. Memory 先文件化，后服务化

先用 Markdown + Git。

不要急着上数据库、向量库、Memory Server。

当前最重要的是：

- 人能看懂；
- AI 能读取；
- 团队能审核；
- 版本能回滚。

---

### 2. Memory 不是聊天记录，而是压缩后的共识

不要把所有对话都存进去。

只存：

- 项目目标；
- 架构决策；
- 业务约束；
- 模块边界；
- 工作流；
- 评测规则；
- 未解决问题；
- 可复用经验。

一句话：

> **Memory 不是日志，而是团队认知的压缩包。**

---

### 3. Agent 可以建议写 Memory，但不能默认改核心 Memory

可以允许 AI 写：

```bash
memory_draft.md
```

但不要允许它直接覆盖：

```bash
architecture.md
decisions.md
constraints.md
```

因为这些是团队共识，不是 AI 的临时理解。

---

### 4. 每个 Memory 文件都要有责任人

示例：

```md
# Owner

- project.md：vayne
- architecture.md：vayne
- eval_rules.md：数据实习生 + vayne
- skill_inventory.md：产品助理 + vayne
- coding_standards.md：全栈实习生 + vayne
```

否则最后会没人维护。

---

### 5. Memory 要服务于行动，不是为了记录而记录

每个文件都要能回答一个具体问题。

| 文件 | 解决的问题 |
|---|---|
| project.md | 我们到底在做什么？ |
| architecture.md | 系统怎么设计？ |
| decisions.md | 哪些事情已经定了？ |
| constraints.md | 哪些事情不能做？ |
| open_questions.md | 哪些事情还没想清楚？ |
| eval_rules.md | 怎么判断做得好不好？ |
| skill_inventory.md | 现在有哪些可复用能力？ |
| daily_dev.md | 每天怎么开发？ |

---

### 6. Memory 更新要进入团队节奏

建议和周报、日报、PR 绑定。

例如：

- 每次 PR：是否需要更新 Memory？
- 每次周报：本周 Memory 有哪些变化？
- 每次复盘：哪些经验应该沉淀成 Memory？
- 每次实习生考核：是否能正确读取和更新 Memory？

这样它才会变成活的机制，而不是死文档。

---

## 15. 第一版 README 模板

可以直接放到 `agent-os-memory/README.md`：

```md
# Agent OS Memory

这是 Agent OS 项目的共享记忆仓库，用于在 Claude Code、Cursor、Hermes 以及团队成员之间同步项目上下文。

## 目标

1. 让不同 AI Coding 工具读取同一套项目上下文。
2. 让团队成员共享项目目标、架构、约束和决策。
3. 让关键经验从聊天记录中沉淀为可复用资产。
4. 为后续团队级 Memory 系统、Skill 系统和 Eval 系统打基础。

## 使用方式

在项目根目录创建软链接：

```bash
ln -s ../agent-os-memory .memory
```

Claude Code 通过 `CLAUDE.md` 读取 `.memory`。

Cursor 通过 `.cursor/rules` 读取 `.memory`。

Hermes 通过 `agent-os-memory` Skill 读取该仓库。

## Memory 类型

### 核心记忆

- project.md
- architecture.md
- decisions.md
- constraints.md
- eval_rules.md

核心记忆必须人工审核后修改。

### 过程记忆

- changelog.md
- open_questions.md
- weekly_summary.md

过程记忆可以由 AI 生成草稿，但需要人工确认。

### 个人记忆

- people/*.md

个人记忆用于记录工作习惯、负责模块、上下文偏好，不记录隐私信息。

## 修改规则

1. 不允许 Agent 自动覆盖核心记忆。
2. Agent 可以提出 Memory 更新建议。
3. 重要修改必须走 PR。
4. 每周进行一次 Memory Review。
5. 如果代码和 Memory 冲突，优先暴露冲突，不要直接覆盖。
```

---

## 16. 当前最推荐的启动方式

第一步不要做大。

今天就可以建一个仓库，只放这些文件：

```bash
agent-os-memory/
├── README.md
├── global/
│   ├── team_principles.md
│   └── coding_standards.md
├── projects/
│   └── agent-os/
│       ├── project.md
│       ├── architecture.md
│       ├── decisions.md
│       ├── constraints.md
│       └── open_questions.md
└── workflows/
    └── daily_dev.md
```

然后配置：

```bash
agent-os/CLAUDE.md
agent-os/.cursor/rules/memory.mdc
~/.hermes/skills/agent-os-memory/SKILL.md
```

先让你自己的三个工具共用起来。

运行 3 天后，再让两个实习生接入。

再运行 1 周后，重点观察：

- 哪些记忆真的有用；
- 哪些记忆没人看；
- 哪些文件需要拆分；
- 哪些流程可以自动化；
- 团队成员是否真的具备 AI Native 协作能力。

---

## 17. 最终结论

这套机制不是为了“存更多信息”，而是为了形成一套团队级的认知基础设施。

你的第一版重点不是智能化，而是：

- 统一上下文；
- 降低重复解释；
- 保留决策历史；
- 让 AI 工具遵守团队共识；
- 让团队成员围绕同一套 Memory 协作；
- 后续自然演进为 Agent OS 的团队记忆中枢。

最适合你的路线是：

> **个人三工具共享 Memory → 两个实习生试点 → 团队 PR 管理 Memory → 自动生成 Memory Draft → Memory Lint → 团队级 Memory 服务。**

这条路径足够轻、足够实用，也能逐步演进成你后续要推广的团队级记忆管理机制。
