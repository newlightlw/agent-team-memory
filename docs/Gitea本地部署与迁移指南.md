# Gitea 本地部署与迁移指南

> 为 AI Native 团队记忆系统提供代码托管底座。本文记录在 macOS 上用 Docker Compose 部署 Gitea 的完整方案，并给出后续迁移到 CentOS 服务器的步骤。同一份 `docker-compose.yml` 在两个平台完全通用。

---

## TL;DR — 60 秒速查

```bash
# 1. 建目录
mkdir -p ~/gitea/data/gitea
# 2. 写 .env 和 docker-compose.yml（见第四节）
# 3. 启动 Docker 守护进程（OrbStack）
open -a OrbStack && docker info >/dev/null 2>&1 && echo "daemon: OK"
# 4. 国内网络先走镜像源拉镜像（直连 Docker Hub 多半被阻断）
docker pull docker.m.daocloud.io/gitea/gitea:1.22
docker tag docker.m.daocloud.io/gitea/gitea:1.22 gitea/gitea:1.22
# 5. 启动 + 验证
cd ~/gitea && docker compose up -d
curl -s -o /dev/null -w "HTTP %{http_code}\n" http://localhost:3000/   # 期望 200
# 6. 浏览器打开 http://localhost:3000 完成初始化
```

> **最大坑提醒**：数据库类型环境变量必须写 **`sqlite3`**，写成 `sqlite` 会导致 Gitea fatal 崩溃并陷入 `restart: always` 死循环（详见第九节）。

---

## 一、方案选型

| 维度 | 选择 | 理由 |
|------|------|------|
| 部署方式 | Docker Compose | Mac 和 CentOS 用同一份配置，迁移零改动 |
| 数据库 | SQLite（起步） | 12 人规模完全够用，零额外容器；后续可平滑升级 Postgres |
| 版本控制 | 镜像 `gitea/gitea:1.22` | 锁定次版本，保证 Mac/CentOS 镜像一致（当前实际为 1.22.6） |
| SSH | Gitea 内置 SSH（端口 2222） | 不与宿主机 22 端口冲突，迁移无差异 |
| 持久化 | `./data/gitea:/data` 单卷挂载 | 所有状态（仓库、DB、配置）一处，整目录拷贝即迁移 |

---

## 二、前提条件

| 工具 | 版本（已验证） | 说明 |
|------|----------------|------|
| Docker | 28.5.2 | Mac 上推荐 OrbStack（比 Docker Desktop 轻） |
| Docker Compose | v2.40.3 | 内置于 Docker，用 `docker compose`（非 `docker-compose`） |
| 架构 | arm64 | Apple Silicon；CentOS 换成 amd64 即可，镜像多架构支持 |

---

## 三、目录结构

```
~/gitea/
├── docker-compose.yml      # Mac / CentOS 共用，唯一可移植配置
├── .env                    # 平台相关变量（迁移时只改这里）
└── data/
    └── gitea/              # 容器内 /data，全部持久化数据
        ├── git/            # Git 仓库存储
        ├── gitea/          # app.ini 配置 + SQLite 数据库（gitea.db）
        └── ssh/            # SSH 主机密钥
```

迁移到 CentOS 时，整个 `~/gitea/` 目录打包拷贝即可。SQLite 数据库实际路径为 `~/gitea/data/gitea/gitea/gitea.db`（跟随默认，无需单独挪出，详见第九节末尾）。

---

## 四、配置文件

### 4.1 `.env`

```env
# Mac 本地调试用 localhost；迁移到 CentOS 时改成服务器 IP 或域名
GITEA_DOMAIN=localhost
GITEA_ROOT_URL=http://localhost:3000/

# 时区
TZ=Asia/Shanghai

# 数据库：必须写 sqlite3（不是 sqlite），否则 Gitea 报 unknown database type
DB_TYPE=sqlite3
```

> **⚠️ 关键约定**：Gitea 的数据库类型字面量是 `sqlite3`，不是 `sqlite`。写错会让 Gitea 在初始化 DB 时 fatal 退出，配合 `restart: always` 形成崩溃死循环，浏览器表现为「连接建立但空响应」。

### 4.2 `docker-compose.yml`

```yaml
# Gitea — Mac 本地调试 / CentOS 生产 共用同一份配置
# 迁移步骤：1) docker compose down  2) 整个 ~/gitea 目录拷到 CentOS  3) 改 .env  4) docker compose up -d

services:
  gitea:
    image: gitea/gitea:1.22
    container_name: gitea
    environment:
      - USER_UID=1000
      - USER_GID=1000
      - TZ=${TZ:-Asia/Shanghai}
      # 通过环境变量预置配置，避免首次启动后还要在 Web 里填
      - GITEA__server__DOMAIN=${GITEA_DOMAIN}
      - GITEA__server__ROOT_URL=${GITEA_ROOT_URL}
      - GITEA__server__SSH_DOMAIN=${GITEA_DOMAIN}
      - GITEA__server__SSH_PORT=2222
      - GITEA__server__SSH_LISTEN_PORT=2222
      - GITEA__server__START_SSH_SERVER=true
      - GITEA__database__DB_TYPE=${DB_TYPE}
      # 注册控制：调试期放开，正式用改为 enable 或 admin
      - GITEA__service__DISABLE_REGISTRATION=false
      - GITEA__service__REQUIRE_SIGNIN_VIEW=false
    restart: always
    volumes:
      - ./data/gitea:/data
    ports:
      - "3000:3000"
      - "2222:2222"
```

**关键设计说明**：

- `GITEA__xxx__yyy` 格式的环境变量会被 Gitea 自动写入 `app.ini` 的 `[xxx] yyy`，省去 Web 安装页手填。
- `START_SSH_SERVER=true` 启用 Gitea 内置 SSH 服务，避免占用宿主机 22。
- 端口映射 `3000:3000`（Web）和 `2222:2222`（SSH 克隆）。

---

## 五、安装步骤（macOS）

### 第一步：创建目录

```bash
mkdir -p ~/gitea/data/gitea
```

### 第二步：写入 `.env` 和 `docker-compose.yml`

内容见上文第四节，放到 `~/gitea/` 下。

### 第三步：启动 Docker 守护进程

OrbStack 不会开机自启，需手动拉起：

```bash
open -a OrbStack
docker info >/dev/null 2>&1 && echo "daemon: OK" || echo "daemon 未就绪，等几秒再试"
```

### 第四步：拉取镜像（国内网络必看）

直连 Docker Hub（`registry-1.docker.io`）通常被阻断，报 `EOF` 或超时。用 daocloud 镜像源拉取，再打回标准标签，保持 compose 文件干净：

```bash
docker pull docker.m.daocloud.io/gitea/gitea:1.22
docker tag docker.m.daocloud.io/gitea/gitea:1.22 gitea/gitea:1.22
```

> **一劳永逸方案**：在 Docker daemon 配置（OrbStack 的 `~/.orbstack/config.yml` 或 CentOS 的 `/etc/docker/daemon.json`）加 `registry-mirrors: ["https://docker.m.daocloud.io"]`，之后 `docker pull` 直接走镜像源，无需改镜像名。

### 第五步：启动服务

```bash
cd ~/gitea
docker compose up -d
```

### 第六步：验证

```bash
# 容器状态（期望 Up）
docker ps --filter name=gitea --format "{{.Names}}: {{.Status}}"

# HTTP 健康检查（期望 HTTP 200）
curl -s -o /dev/null -w "HTTP %{http_code}\n" http://localhost:3000/

# 关键日志（期望出现 ORM engine initialization successful!）
docker logs gitea 2>&1 | grep -iE "Listen|ORM engine|unknown database" | tail -5

# 重启次数（期望 0；持续 >0 说明在崩溃循环）
docker inspect gitea --format 'RestartCount: {{.RestartCount}}'
```

**验证通过的标志**：容器 `Up`、HTTP 200、日志含 `ORM engine initialization successful!`、`RestartCount: 0`。

---

## 六、首次初始化

打开 http://localhost:3000，会出现以下两种情况之一：

- **情况 A（首次干净部署）**：看到安装页，数据库类型、域名、URL 已通过环境变量预填 → 确认 **SQLite3** → 点「安装 Gitea」。
- **情况 B（配置已落盘）**：环境变量已让 Gitea 进入已安装态，直接是登录/注册页。

两种都是正常的。之后统一执行：

1. 第一个注册的账号**自动成为管理员**。
2. 新建 Organization（如 `ai-team`），在其中创建 `team-memory` 仓库。
3. 邀请团队成员加入 Organization。

---

## 七、迁移到 CentOS

### 7.1 Mac 端：停止并打包

```bash
cd ~/gitea && docker compose down
cd ~ && tar czf gitea-backup.tar.gz gitea/
```

### 7.2 传到服务器

```bash
scp gitea-backup.tar.gz user@<服务器IP>:~/
```

### 7.3 CentOS 端：解压

```bash
tar xzf gitea-backup.tar.gz
cd ~/gitea
```

### 7.4 应用「生产环境三处改动」

**改动 1 — `.env`**（换成服务器 IP 或域名）：

```env
GITEA_DOMAIN=<服务器IP或域名>
GITEA_ROOT_URL=http://<服务器IP或域名>:3000/
```

**改动 2 — `docker-compose.yml`** 端口绑定 `0.0.0.0`（让内网可访问）+ 关闭开放注册：

```yaml
    environment:
      # ...其余不变...
      - GITEA__service__DISABLE_REGISTRATION=true   # 邀请制
    ports:
      - "0.0.0.0:3000:3000"
      - "0.0.0.0:2222:2222"
```

**改动 3 — 防火墙放行**：

```bash
sudo firewall-cmd --add-port=3000/tcp --permanent
sudo firewall-cmd --add-port=2222/tcp --permanent
sudo firewall-cmd --reload
```

### 7.5 镜像准备

若服务器同样无法直连 Docker Hub，二选一：

```bash
# 方式 A：手动拉取 + 打标签
docker pull docker.m.daocloud.io/gitea/gitea:1.22
docker tag docker.m.daocloud.io/gitea/gitea:1.22 gitea/gitea:1.22

# 方式 B：配置 daemon.json 一劳永逸
echo '{ "registry-mirrors": ["https://docker.m.daocloud.io"] }' | sudo tee /etc/docker/daemon.json
sudo systemctl restart docker
```

### 7.6 启动

```bash
cd ~/gitea
docker compose up -d
```

团队成员即可通过 `http://<服务器IP>:3000` 访问。

---

## 八、运维命令速查

```bash
cd ~/gitea
docker compose logs -f gitea                  # 实时日志
docker compose restart                        # 重启
docker compose down                           # 停止并移除容器（数据保留）
docker compose pull && docker compose up -d   # 升级到最新镜像
docker inspect gitea --format '{{.RestartCount}}'  # 查重启次数（排查崩溃循环）
```

**完整备份**（定期做，需先 `docker compose down` 保证数据落盘）：

```bash
cd ~ && tar czf gitea-backup-$(date +%F).tar.gz gitea/data/
```

---

## 九、踩坑与排错

### 9.1 现象：HTTP 000 / 空响应 + 容器反复重启

**根因**：`.env` 里 `DB_TYPE=sqlite`（错误），Gitea 不识别，初始化 DB 时 fatal 退出，`restart: always` 拉起后再次崩溃，形成死循环。浏览器表现是 TCP 连得上但空响应。

**诊断**：

```bash
docker logs gitea 2>&1 | grep "unknown database type"
# 出现 unknown database type: sqlite 即为此坑
docker inspect gitea --format '{{.RestartCount}}'   # 会看到一个持续增长的数字
```

**修复**：

```bash
# 1. 改 .env：DB_TYPE=sqlite3
# 2. 同步修正已落盘的 app.ini
docker exec gitea sed -i 's/^DB_TYPE = sqlite$/DB_TYPE = sqlite3/' /data/gitea/conf/app.ini
# 3. 重建容器使 .env 生效
cd ~/gitea && docker compose up -d --force-recreate
```

### 9.2 现象：`Cannot connect to the Docker daemon`

**根因**：OrbStack 未启动（不会开机自启）。

**修复**：

```bash
open -a OrbStack
# 等 1~2 秒
docker info >/dev/null 2>&1 && echo "daemon: OK"
```

### 9.3 现象：拉镜像报 `EOF` 或超时

**根因**：国内网络直连 `registry-1.docker.io` 被阻断。

**修复**：用 daocloud 镜像源（见第五步第四节），或在 daemon 配置加 `registry-mirrors`。

### 9.4 关于 SQLite 文件路径

SQLite 文件跟随默认落在 `~/gitea/data/gitea/gitea/gitea.db`（容器内 `/data/gitea/gitea.db`）。

- **SQLite 阶段**：保持默认，不要单独挪出。单卷 `data/` 是完整备份单元，分离会让备份/迁移漏文件，收益为零。
- **Postgres 阶段**（升级后）：给 Postgres 独立子目录 `./data/postgres`，但仍留在 `~/gitea/data/` 树内，保证一次 `tar` 带走全部状态。
- 判据：**一次 `tar` 能带走 DB + 仓库 + 配置 + 密钥**，就算合格。

---

## 十、后续升级路径

| 触发条件 | 动作 |
|----------|------|
| 团队超 20 人 / 并发压力大 | SQLite → Postgres：在 compose 加 postgres 服务，改 `DB_TYPE=postgres`，用 Gitea 内置迁移工具转数据 |
| 需要 CI 校验记忆格式 | 启用 Gitea Actions（兼容 GitHub Actions 语法），为 team-memory 仓库加 workflow |
| 需要语义检索 | Phase 2 部署 MCP 记忆服务器，Gitea webhook 触发重新索引 |

---

## 十一、端口与地址清单

| 用途 | 本地调试 | CentOS 生产 |
|------|----------|-------------|
| Web 访问 | http://localhost:3000 | http://\<服务器IP\>:3000 |
| HTTP 克隆 | http://localhost:3000/...git | http://\<服务器IP\>:3000/...git |
| SSH 克隆 | `ssh git@localhost -p 2222` | `ssh git@<服务器IP> -p 2222` |
| HTTP API | http://localhost:3000/api/v1 | http://\<服务器IP\>:3000/api/v1 |

---

*安装完成后，在 Gitea 上创建 `team-memory` 仓库，按《AI Native 团队记忆落地实操指南》的 4 周计划推进即可。*
