# EvoAgent macOS 配置与快速开始

本文面向 macOS（zsh / bash），用 [uv](https://docs.astral.sh/uv/) 创建 Python 3.11 虚拟环境并完成本地启动。完整功能说明见 [README.md](README.md)。

## 1. 前置条件

- macOS 12+（Apple Silicon / Intel 均可）
- 已安装 [Homebrew](https://brew.sh/)（可选，便于安装转发工具）
- 已安装 [uv](https://docs.astral.sh/uv/getting-started/installation/)

安装 uv（任选一种）：

```bash
# 官方安装脚本
curl -LsSf https://astral.sh/uv/install.sh | sh

# 或 Homebrew
brew install uv
```

安装后确认：

```bash
uv --version
```

## 2. 克隆并进入项目

```bash
cd /path/to/EvoAgent
```

## 3. 用 uv 创建 Python 3.11 虚拟环境

项目需要 **Python 3.11**。uv 会在本机没有该版本时自动下载：

```bash
# 在项目根目录创建 .venv，锁定 Python 3.11
uv venv --python 3.11

# 激活虚拟环境
source .venv/bin/activate

# 确认解释器版本
python --version   # 应显示 Python 3.11.x
which python       # 应指向 .../EvoAgent/.venv/bin/python
```

之后每次新开终端都需要重新执行 `source .venv/bin/activate`，或在命令前使用 `uv run`（见下文）。

## 4. 安装依赖

在已激活的虚拟环境中：

```bash
uv pip install -r requirements.txt
```

未激活时也可以直接：

```bash
uv pip install --python .venv/bin/python -r requirements.txt
```

## 5. 配置本地管理员（推荐启用登录）

不要直接使用示例占位符作为密码或密钥。环境变量只对当前 shell 及其子进程生效；修改后需重启 EvoAgent。

### 方式 A：当前终端临时导出

```bash
export EVOAGENT_AUTH_REQUIRED=true
export EVOAGENT_AUTH_SECRET="$(openssl rand -base64 32)"
export EVOAGENT_BOOTSTRAP_ADMIN_USERNAME=admin
export EVOAGENT_BOOTSTRAP_ADMIN_PASSWORD='<替换为至少 10 个字符的密码>'
```

### 方式 B：写入根目录 `.env`（推荐）

项目启动时会自动读取根目录 `.env`（也兼容 `evoagent/.env`）；**系统环境变量优先于 `.env`**。该文件已被 `.gitignore` 忽略。

```bash
cp .env.example .env
```

编辑 `.env`，至少设置：

```env
EVOAGENT_AUTH_REQUIRED=true
EVOAGENT_AUTH_SECRET=<用 openssl rand -base64 32 生成>
EVOAGENT_BOOTSTRAP_ADMIN_USERNAME=admin
EVOAGENT_BOOTSTRAP_ADMIN_PASSWORD=<至少 10 个字符的密码>
```

生成密钥示例：

```bash
openssl rand -base64 32
```

Bootstrap 管理员只在用户名尚不存在时创建；已有同名用户的密码不会在重启时被覆盖。

## 6. 启动服务

```bash
# 已激活 .venv
python -m evoagent

# 或未激活时
uv run --python .venv/bin/python -m evoagent
```

服务默认监听 `127.0.0.1:8080`。浏览器打开：

[http://127.0.0.1:8080/](http://127.0.0.1:8080/)

前端在业务 API 返回未授权时会显示登录层；登录状态保存在浏览器 `localStorage` 中。

健康检查：

```bash
curl -s http://127.0.0.1:8080/health
```

## 7. API 快速验证

登录并携带 Bearer Token：

```bash
PASSWORD='<你的密码>'

TOKEN="$(curl -s -X POST http://127.0.0.1:8080/v1/auth/login \
  -H 'Content-Type: application/json' \
  -d "{\"username\":\"admin\",\"password\":\"${PASSWORD}\"}" \
  | python -c 'import sys,json; print(json.load(sys.stdin)["access_token"])')"

curl -s -X POST http://127.0.0.1:8080/v1/reviews \
  -H "Authorization: Bearer ${TOKEN}" \
  -H 'Content-Type: application/json' \
  -d '{
    "repository": "demo/api",
    "pull_request": 12,
    "diff": "diff --git a/app.py b/app.py\n--- a/app.py\n+++ b/app.py\n@@ -1 +1,2 @@\n+password = '\''secret'\''\n+eval(user_input)"
  }'
```

查询任务（将 `<task-id>` 换成上一步返回的 id）：

```bash
curl -s -H "Authorization: Bearer ${TOKEN}" \
  http://127.0.0.1:8080/v1/tasks/<task-id>

curl -s -H "Authorization: Bearer ${TOKEN}" \
  http://127.0.0.1:8080/v1/tasks/<task-id>/report
```

## 8. 模型配置（可选）

默认 `EVOAGENT_LLM_PROVIDER=local`，只跑确定性本地规则 Agent，不调用大模型。

### DeepSeek 官方 API

在 `.env` 中：

```env
EVOAGENT_LLM_PROVIDER=deepseek
EVOAGENT_DEEPSEEK_API_KEY=你的真实APIKey
```

或当前终端：

```bash
export EVOAGENT_LLM_PROVIDER=deepseek
export EVOAGENT_DEEPSEEK_API_KEY='<deepseek-api-key>'
python -m evoagent
```

### OpenRouter 免费 DeepSeek

```bash
export EVOAGENT_LLM_PROVIDER=openrouter-deepseek-free
export EVOAGENT_OPENROUTER_API_KEY='<openrouter-api-key>'
python -m evoagent
```

免费模型若下线，可将 `EVOAGENT_LLM_MODEL` 改为其他 `:free` 模型，或把 Provider 改为 `openrouter-free`。

### 自定义 OpenAI 兼容端点

```bash
export EVOAGENT_LLM_PROVIDER=custom
export EVOAGENT_LLM_BASE_URL='https://example.com/v1'
export EVOAGENT_LLM_API_KEY='<token>'
export EVOAGENT_LLM_MODEL='<model-name>'
```

密钥只通过环境变量 / `.env` 读取，不要提交到仓库。

## 9. 运行测试

```bash
# 已激活 .venv
python -m unittest discover -s tests -v

# 或
uv run --python .venv/bin/python -m unittest discover -s tests -v
```

## 10. GitHub Webhook（可选）

本地演示流程：EvoAgent → 公网转发 → GitHub Webhook。

### 10.1 配置密钥与 Token

```bash
export EVOAGENT_GITHUB_WEBHOOK_SECRET="$(openssl rand -base64 32)"
# 私有仓库 / 评论回写 / 自动修复需要
export EVOAGENT_GITHUB_TOKEN='<GitHub fine-grained PAT>'
export EVOAGENT_AUTO_POST_REVIEW=true   # 默认 false；设为 true 才回写 PR 评论
python -m evoagent
```

`EVOAGENT_GITHUB_WEBHOOK_SECRET` 与 `EVOAGENT_AUTH_SECRET` 不要混用。Webhook 走 HMAC 签名认证，不携带管理台 Bearer Token。

fine-grained PAT 最小权限：

- 读私有 PR Diff：`Contents: Read`、`Pull requests: Read`
- 回写评论：`Pull requests: Read and write`
- 自动修复分支：`Contents: Read and write`、`Pull requests: Read and write`

### 10.2 公网转发

```bash
# Cloudflare Quick Tunnel（需先安装 cloudflared）
brew install cloudflare/cloudflare/cloudflared
cloudflared tunnel --url http://127.0.0.1:8080

# 或 ngrok
brew install ngrok
ngrok http 8080
```

将输出的 `https://...` 记为公网域名，并保持 EvoAgent 与转发进程同时运行。临时域名重启后会变，需同步更新 GitHub Webhook。

暴露到公网时务必保持 `EVOAGENT_AUTH_REQUIRED=true`，并使用强密码与随机 `EVOAGENT_AUTH_SECRET`。

### 10.3 在 GitHub 添加 Webhook

**Settings → Webhooks → Add webhook**：

| 字段 | 值 |
|---|---|
| Payload URL | `https://<公网域名>/webhooks/github` |
| Content type | `application/json` |
| Secret | 与 `EVOAGENT_GITHUB_WEBHOOK_SECRET` 相同 |
| Events | 仅勾选 **Pull requests** |

验证：

```bash
curl -s http://127.0.0.1:8080/health
curl -s https://<公网域名>/health
```

新建 / 重开 PR 或推送提交后，Recent Deliveries 应看到 `202`，管理台任务中心会出现审查任务。

## 11. Docker 生产模式（可选）

需要本机已安装 Docker Desktop：

```bash
cp .env.example .env
# 按需编辑 .env 后
docker compose up --build
```

会启动 PostgreSQL、Redis 与 EvoAgent。未配置这两项时，本地进程模式自动使用 SQLite 与进程内队列，适合演示。

## 常用命令速查

```bash
# 创建并激活环境
uv venv --python 3.11 && source .venv/bin/activate

# 安装依赖
uv pip install -r requirements.txt

# 启动
python -m evoagent

# 测试
python -m unittest discover -s tests -v

# 退出虚拟环境
deactivate
```

## 故障排查

| 现象 | 处理 |
|---|---|
| `python` 不是 3.11 | 重新 `uv venv --python 3.11` 并 `source .venv/bin/activate` |
| 修改 `.env` 不生效 | 停止进程后重新 `python -m evoagent`；确认没有被 shell 中同名 `export` 覆盖 |
| 登录失败 | 确认密码 ≥10 字符；若用户已存在，Bootstrap 不会覆盖密码 |
| Webhook 非 202 | 检查转发是否在跑、Payload URL 是否含 `/webhooks/github`、Secret 是否一致、PAT 权限 |
