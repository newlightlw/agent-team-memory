# 团队记忆系统 · Codex（Windows）接入指南

> 本文档面向 **Windows + Codex** 组员，按步骤操作即可接入团队共享记忆。全程约 **10 分钟**。
>
> **管理员填写后再发**：将下文 `<短名>` 替换为该组员的真实英文短名（如 `zhang3`）。

---

## 一、你需要准备什么

### 向管理员确认（应已具备）

| 项 | 你的值 |
|---|---|
| Gitea 地址 | `http://192.168.1.66:3000` |
| 组织 | `ai-team` |
| 记忆仓库 | `http://192.168.1.66:3000/ai-team/team-memory.git` |
| 工具仓库 | `http://192.168.1.66:3000/ai-team/agent-team-memory.git` |
| **你的英文短名** | `<短名>`（管理员分配，如 `zhang3`；**不能中文**，会写进记忆 id） |

### 本机软件

| 软件 | 要求 |
|---|---|
| **Python** | ≥ 3.11，安装时勾选 **Add Python to PATH** |
| **Git** | [Git for Windows](https://git-scm.com/download/win) |
| **Codex** | 已安装，并**至少打开/运行过一次** |
| **网络** | 能访问 `http://192.168.1.66:3000`（与服务器同一局域网） |

### 自行生成 Gitea Token（一次性）

1. 浏览器打开 http://192.168.1.66:3000 ，登录你的 Gitea 账号
2. 右上角头像 → **设置** → **应用** → **生成新的令牌**
3. 勾选 **`repository`** 权限，生成后**复制保存**（只显示一次）

下文用 `<TOKEN>` 表示这个令牌。

---

## 二、一键接入（推荐）

在 **PowerShell** 或 **CMD** 中依次执行：

```powershell
git clone http://192.168.1.66:3000/ai-team/agent-team-memory.git
cd agent-team-memory
python scripts/onboard.py http://192.168.1.66:3000/ai-team/team-memory.git <短名>
```

脚本会自动完成：

- clone 记忆仓库到 `C:\Users\<你的用户名>\team-memory`
- 安装 `team-memory` 命令行工具
- 写入 `.env`（仓库地址 + 短名）
- 尝试桥接到 Claude Code / **Codex** / Hermes / Trae
- 运行健康自检

**成功标志**：最后一行出现 `✓ 接入完成! 记忆仓库: ...`

> 若提示 `python 不是内部或外部命令`，改用 `py -3.11`，或重装 Python 并勾选 Add to PATH。

---

## 三、Codex 专用配置

### 3.1 Codex 桥接机制说明

与 Claude Code 不同，Codex 通过 **`AGENTS.md` 标记段** 加载团队上下文（幂等更新，不会覆盖你已有的其他内容）：

| 内容 | 路径 |
|---|---|
| 团队记忆上下文 | `%USERPROFILE%\.codex\AGENTS.md`（`<!-- team-memory:start/end -->` 段） |
| 对话沉淀（「提交下」） | `%USERPROFILE%\.codex\skills\auto-commit-memory\SKILL.md` |

### 3.2 确认桥接已安装

`onboard` 成功后，应看到类似输出：

```
✓ Codex AGENTS.md: C:\Users\<你>\.codex\AGENTS.md
✓ codex auto-commit skill: C:\Users\<你>\.codex\skills\auto-commit-memory\SKILL.md
```

若出现 **`Codex: 未检测到 ~/.codex，跳过`**：

1. 先打开 Codex 一次（会自动创建配置目录）
2. 再执行：

```powershell
python -m team_memory load --global --tools codex -p $env:USERPROFILE\team-memory
```

**新开一个 Codex 会话**后，上下文才会加载生效。

可用记事本打开 `%USERPROFILE%\.codex\AGENTS.md`，确认存在 `<!-- team-memory:start -->` … `<!-- team-memory:end -->` 段落。

### 3.3 配置 Token（推送记忆用）

用记事本打开 `C:\Users\<你的用户名>\team-memory\.env`，确认并补充：

```env
GITEA_REMOTE_URL=http://192.168.1.66:3000/ai-team/team-memory.git
GITEA_TOKEN=<TOKEN>
TEAM_NAME=AI Native 团队
DEFAULT_AUTHOR=<短名>
```

或在 PowerShell 追加（把 token 替换成真实值）：

```powershell
Add-Content $env:USERPROFILE\team-memory\.env "GITEA_TOKEN=<TOKEN>"
```

### 3.4 验证接入

```powershell
python -m team_memory doctor -p $env:USERPROFILE\team-memory
python -m team_memory web -p $env:USERPROFILE\team-memory
```

- `doctor` 应显示 **✓ 仓库健康**
- `web` 会在浏览器打开，能看到团队已有记忆和检索框

> **Windows 习惯用法**：若 `team-memory` 命令不可用，一律用 `python -m team_memory <子命令>`，不依赖 PATH。

---

## 四、（推荐）配置 MCP — 对话中动态查/写记忆

`AGENTS.md` 是启动时的静态快照；**MCP** 让 Codex 在对话里直接搜索、读取、提交候选记忆，更灵活。

### 4.1 安装 MCP 依赖

在已 clone 的工具仓库目录执行：

```powershell
cd agent-team-memory
python -m pip install -e ".[mcp]"
```

### 4.2 编辑 Codex 配置

编辑 `%USERPROFILE%\.codex\config.toml`（没有则新建），追加：

```toml
[mcp_servers.team-memory]
command = "python"
args = ["-m", "team_memory.mcp_server"]

[mcp_servers.team-memory.env]
TEAM_MEMORY_ROOT = "C:\\Users\\<你的用户名>\\team-memory"
```

> Windows 路径中的反斜杠在 TOML 里建议写成 `\\`，或使用正斜杠 `C:/Users/<你的用户名>/team-memory`。

### 4.3 MCP 可用能力

| Tool | 作用 |
|---|---|
| `search_memory` | 关键字搜索记忆 |
| `get_memory` | 单条详情 + 版本历史 |
| `list_memories` | 列出正式记忆 |
| `propose_memory` | 提交**候选**到 inbox（待审） |
| `list_inbox` | 查看待审候选 |
| `approve_memory` | 候选转正式（需人工授权） |

> 原则：**AI 可 propose，不直接写正式记忆**；你已确认的内容用 CLI `capture` 或明确授权 AI 调 `approve_memory`。

配置完成后**重启 Codex**，在 MCP 设置中确认 `team-memory` 已连接。

---

## 五、项目级桥接（可选）

若希望在**某个具体项目**里自动带上团队上下文，可在项目目录更新 `AGENTS.md`：

```powershell
python -m team_memory load --tools codex -p $env:USERPROFILE\team-memory C:\path\to\你的项目
```

会在项目根目录的 `AGENTS.md` 中写入/更新 team-memory 标记段（与全局 `%USERPROFILE%\.codex\AGENTS.md` 互不冲突，项目级优先于全局场景）。

---

## 六、日常使用

### 沉淀记忆（三种方式）

**方式 A — 命令行（已确认的经验）**

```powershell
python -m team_memory capture "记忆标题" -t decision --via codex -a <短名> --note "背景与结论..." -p $env:USERPROFILE\team-memory
```

类型可选：`decision`（决策）| `error`（踩坑）| `skill`（流程）| `project`（项目）| `code`（代码结构）

**方式 B — 对话里说「提交下」**

在 Codex 里完成一个有价值的任务后，直接说 **「提交下」** → `auto-commit-memory` skill 会尝试自动总结 → 给你看草稿 → 你确认后才入库。

> 注：Codex 对触发式 skill 的支持因版本而异；若「提交下」未触发，请直接用方式 A 或方式 C。

**方式 C — MCP 动态提交（配好 MCP 后）**

在对话中让 Codex 搜索相关记忆、整理本次结论，并调用 `propose_memory` 提交候选；你审核后再 `approve`。

**候选记忆（AI 推断 / 尚未验证）**

```powershell
python -m team_memory propose "标题" -t decision --via codex -a <短名> --confidence high --evidence "PR-123" -p $env:USERPROFILE\team-memory
python -m team_memory review -p $env:USERPROFILE\team-memory
python -m team_memory approve mem-YYYYMMDD-<短名>-001 -p $env:USERPROFILE\team-memory
```

### 读取团队记忆

```powershell
python -m team_memory list -p $env:USERPROFILE\team-memory
python -m team_memory show mem-20260626-<短名>-001 -p $env:USERPROFILE\team-memory
python -m team_memory web -p $env:USERPROFILE\team-memory
```

在 Codex 对话中，也可直接问：「查一下团队记忆里关于 XXX 的决策」——配了 MCP 后会自动调用 `search_memory`。

### 同步给团队（沉淀后必做）

`capture` **不会自动 commit**，需要手动提交再推送：

```powershell
cd $env:USERPROFILE\team-memory
git add -A
git commit -m "memory(decision): 记忆标题"
python -m team_memory sync -p $env:USERPROFILE\team-memory
```

### 拉取队友最新记忆

```powershell
python -m team_memory sync -p $env:USERPROFILE\team-memory
python -m team_memory load --global --tools codex -p $env:USERPROFILE\team-memory
```

然后**新开 Codex 会话**刷新 `AGENTS.md` 快照；或通过 MCP 直接读最新记忆（无需 refresh）。

---

## 七、工作约定

1. **沉淀后 commit + sync**：否则队友看不到
2. **核心记忆走 PR**：改 `memory/project/`、`memory/decisions/` 建议提 PR 让人 review
3. **secrets 不入库**：token、密码不要写进记忆 Markdown
4. **新写入下个会话才生效**：刚 capture 的内容，当前 Codex 对话不会立刻依赖它（MCP 读取除外）
5. **冲突按提示处理**：`sync` 报冲突时，编辑文件删除 `<<<<<<< ======= >>>>>>>` 标记 → `git add` → `git rebase --continue`；搞不定就 `git rebase --abort`

---

## 八、常见问题

| 现象 | 处理 |
|---|---|
| `Codex: 未检测到 ~/.codex，跳过` | 先打开 Codex，再 `load --global --tools codex` |
| `AGENTS.md` 没有 team-memory 段 | 重新执行 `load --global --tools codex`；检查文件是否被手动改坏 |
| 「提交下」没反应 | 改用 CLI `capture`，或配置 MCP 后在对话里让 Codex propose |
| MCP 未连接 | 检查 `pip install -e ".[mcp]"`；重启 Codex；检查 `%USERPROFILE%\.codex\config.toml` |
| `python 不是内部或外部命令` | 用 `py -3.11`，或重装 Python 勾选 Add to PATH |
| `team-memory 不是命令` | 改用 `python -m team_memory <命令>` |
| 浏览器打不开 192.168.1.66:3000 | 确认同一局域网；联系管理员检查防火墙是否放行 3000 端口 |
| `author 必须含 ascii 字母数字` | 短名必须是英文，如 `zhang3` |
| `sync` 说「未提交变更」 | 先 `git add -A && git commit`，或 `python -m team_memory sync --force` |
| `sync` push 403 | 确认管理员已把你加入 `ai-team` 组织，token 勾选了 `repository` |
| `sync` 报冲突 | 见上文「工作约定」第 5 条 |
| `web` 端口被占 | `python -m team_memory web -p $env:USERPROFILE\team-memory --port 8001` |

---

## 九、完成自检清单

接入完成后，请逐项确认：

- [ ] `python -m team_memory doctor` 显示仓库健康
- [ ] `web` 能打开并看到团队记忆
- [ ] `%USERPROFILE%\.codex\AGENTS.md` 含 team-memory 标记段
- [ ] `%USERPROFILE%\.codex\skills\auto-commit-memory\SKILL.md` 存在
- [ ] 能 `capture` 一条测试记忆 + `commit` + `sync` 推上去
- [ ] 新开 Codex 会话，对话中能引用团队上下文
- [ ] MCP `team-memory` 已连接，对话中能搜索记忆（可选）

有问题先查上表，仍无法解决请联系管理员。

---

## 附录：命令速查（复制用）

```powershell
# 变量（PowerShell 会话内）
$MEM = "$env:USERPROFILE\team-memory"
$NAME = "<短名>"

# 沉淀
python -m team_memory capture "标题" -t decision --via codex -a $NAME --note "..." -p $MEM

# 同步
cd $MEM; git add -A; git commit -m "memory: 标题"; python -m team_memory sync -p $MEM

# 查看
python -m team_memory list -p $MEM
python -m team_memory web -p $MEM

# 刷新 Codex AGENTS.md（sync 拉新记忆后）
python -m team_memory load --global --tools codex -p $MEM
```

### MCP 配置片段（粘贴到 `%USERPROFILE%\.codex\config.toml`）

```toml
[mcp_servers.team-memory]
command = "python"
args = ["-m", "team_memory.mcp_server"]

[mcp_servers.team-memory.env]
TEAM_MEMORY_ROOT = "C:/Users/<你的用户名>/team-memory"
```
