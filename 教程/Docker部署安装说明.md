# TradingAgents-CN Docker 部署安装说明

## 项目简介

TradingAgents-CN 是一个面向中文用户的**多智能体与大模型股票分析学习平台**。

### 核心特性

- **多智能体分析框架**：市场分析师、基本面分析师、新闻分析师、研究员等协同工作
- **多 LLM 提供商支持**：OpenAI、DeepSeek、阿里百炼、百度文心、Google Gemini 等
- **多数据源支持**：Tushare、AKShare、BaoStock（支持 A股/港股/美股）
- **用户权限管理**：完整的用户认证、角色管理、操作日志系统
- **专业报告导出**：支持 Markdown/Word/PDF 多格式输出
- **实时通知系统**：SSE+WebSocket 双通道推送

### 技术栈

| 组件 | 技术 |
|------|------|
| 后端框架 | FastAPI + Uvicorn |
| 前端框架 | Vue 3 + Vite + Element Plus |
| 数据库 | MongoDB + Redis |
| 容器化 | Docker + Docker Compose |
| 反向代理 | Nginx |

---

## 环境要求

### 硬件要求

| 资源 | 最低配置 | 推荐配置 |
|------|---------|---------|
| CPU | 2 核 | 4 核+ |
| 内存 | 4 GB | 8 GB+ |
| 磁盘 | 20 GB | 50 GB+ |

### 软件要求

| 软件 | 版本要求 | 验证命令 |
|------|---------|---------|
| Docker | 20.10+ | `docker --version` |
| Docker Compose | 2.0+ | `docker compose version` |

### 网络要求

- 开放 80 端口（HTTP）或 443 端口（HTTPS）
- 如使用国内 LLM 服务（阿里百炼、DeepSeek 等），需确保能访问国内网络
- 如使用 OpenAI、Google 等，需确保网络能访问国外服务

---

## 安装步骤

### 步骤 1：创建项目目录

```bash
# 创建项目目录
mkdir -p ~/tradingagents-demo
cd ~/tradingagents-demo
```

### 步骤 2：准备配置文件

从项目源码复制必要的配置文件：

```bash
# 复制 Docker Compose 配置文件
cp /path/to/TradingAgents-CN/docker-compose.hub.nginx.yml .

# 复制环境配置模板
cp /path/to/TradingAgents-CN/.env.docker .
mv .env.docker .env

# 创建 Nginx 配置目录并复制配置
mkdir -p nginx
cp /path/to/TradingAgents-CN/nginx/nginx.conf nginx/nginx.conf
```

**或使用 wget 下载（推荐）**：

```bash
# 下载 Docker Compose 配置文件
wget https://raw.githubusercontent.com/hsliuping/TradingAgents-CN/v1.0.0-preview/docker-compose.hub.nginx.yml

# 下载环境配置模板
wget https://raw.githubusercontent.com/hsliuping/TradingAgents-CN/v1.0.0-preview/.env.docker -O .env

# 创建 Nginx 配置目录并下载配置
mkdir -p nginx
wget https://raw.githubusercontent.com/hsliuping/TradingAgents-CN/v1.0.0-preview/nginx/nginx.conf -O nginx/nginx.conf
```

### 步骤 3：配置环境变量

编辑 `.env` 文件，配置 API 密钥：

```bash
nano .env  # 或使用 gedit、vim 等编辑器
```

**必需配置**（至少配置一个 LLM 提供商）：

```bash
# 阿里百炼（推荐，国产模型，中文优化）
DASHSCOPE_API_KEY=your_dashscope_api_key_here
DASHSCOPE_ENABLED=true

# 或 DeepSeek（推荐，性价比高）
DEEPSEEK_API_KEY=your_deepseek_api_key_here
DEEPSEEK_ENABLED=true

# 或 OpenAI（需要国外网络）
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_ENABLED=true
```

**API 密钥获取地址**：

| 服务 | 获取地址 | 说明 |
|------|---------|------|
| 阿里百炼 | https://dashscope.aliyun.com/ | 国产模型，中文优化，推荐 |
| DeepSeek | https://platform.deepseek.com/ | 性价比高，推荐 |
| OpenAI | https://platform.openai.com/ | 需要国外网络 |
| Google AI | https://ai.google.dev/ | Gemini 模型 |
| Tushare | https://tushare.pro/register?reg=tacn | 专业金融数据（可选） |

### 步骤 4：拉取 Docker 镜像

```bash
# 拉取所有镜像（约 2-5 分钟，取决于网络速度）
docker compose -f docker-compose.hub.nginx.yml pull
```

**预期输出**：
```
[+] Pulling 5/5
 ✔ mongodb Pulled
 ✔ redis Pulled
 ✔ backend Pulled
 ✔ frontend Pulled
 ✔ nginx Pulled
```

### 步骤 5：启动服务

```bash
# 启动所有服务（后台运行）
docker compose -f docker-compose.hub.nginx.yml up -d

# 查看服务状态
docker compose -f docker-compose.hub.nginx.yml ps
```

**预期输出**：
```
NAME                       IMAGE                                    STATUS
tradingagents-backend      hsliup/tradingagents-backend:latest      Up (healthy)
tradingagents-frontend     hsliup/tradingagents-frontend:latest     Up (healthy)
tradingagents-mongodb      mongo:4.4                                Up (healthy)
tradingagents-nginx        nginx:alpine                             Up
tradingagents-redis        redis:7-alpine                           Up (healthy)
```

### 步骤 6：导入初始配置

**首次部署必须执行此步骤**：

```bash
# 导入镜像内置的配置数据
docker exec -it tradingagents-backend python scripts/import_config_and_create_user.py
```

**预期输出**：
```
💡 未指定文件，使用默认配置: /app/install/database_export_config_2025-10-17.json
================================================================================
📦 导入配置数据并创建默认用户
================================================================================

🔌 连接到 MongoDB...
✅ MongoDB 连接成功

📋 准备导入 11 个集合:
   - system_configs: 79 个文档
   - users: 1 个文档
   - llm_providers: 8 个提供商
   - model_catalog: 15+ 个模型
   ...

✅ 操作完成！

🔐 登录信息:
   用户名: admin
   密码: admin123
```

### 步骤 7：重启后端服务

```bash
docker restart tradingagents-backend

# 查看启动日志
docker logs -f tradingagents-backend
```

看到以下日志表示启动成功：
```
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### 步骤 8：访问系统

打开浏览器，访问：

- **本地部署**：http://localhost
- **服务器部署**：http://你的服务器IP

**默认登录信息**：
- 用户名：`admin`
- 密码：`admin123`

---

## 目录结构

```
~/tradingagents-demo/
├── docker-compose.hub.nginx.yml  # Docker Compose 配置文件
├── .env                          # 环境变量配置
├── nginx/
│   └── nginx.conf                # Nginx 配置文件
├── logs/                         # 日志目录（自动创建）
└── data/                         # 数据目录（自动创建）
```

---

## 服务架构

```
用户浏览器
    ↓
http://服务器IP:80
    ↓
┌─────────────────────────────────────┐
│  Nginx (统一入口)                    │
│  - 前端静态资源 (/)                  │
│  - API 反向代理 (/api → backend)    │
└─────────────────────────────────────┘
    ↓                    ↓
Frontend            Backend
(Vue 3)            (FastAPI)
    ↓                    ↓
                ┌────────┴────────┐
                ↓                 ↓
            MongoDB            Redis
          (数据存储)         (缓存)
```

---

## 常用命令

### 服务管理

```bash
# 查看服务状态
docker compose -f docker-compose.hub.nginx.yml ps

# 查看日志
docker compose -f docker-compose.hub.nginx.yml logs -f

# 查看特定服务日志
docker logs -f tradingagents-backend

# 重启服务
docker compose -f docker-compose.hub.nginx.yml restart

# 停止服务
docker compose -f docker-compose.hub.nginx.yml down

# 停止并删除数据卷（⚠️ 会删除所有数据）
docker compose -f docker-compose.hub.nginx.yml down -v
```

### 更新系统

```bash
# 拉取最新镜像
docker compose -f docker-compose.hub.nginx.yml pull

# 重启服务
docker compose -f docker-compose.hub.nginx.yml up -d
```

### 数据库操作

```bash
# 连接 MongoDB
docker exec -it tradingagents-mongodb mongo -u admin -p tradingagents123 --authenticationDatabase admin

# 备份数据
docker exec tradingagents-mongodb mongodump \
  -u admin -p tradingagents123 --authenticationDatabase admin \
  -d tradingagents -o /data/backup
```

---

## 常见问题

### 1. 服务启动失败

```bash
# 查看详细日志
docker compose -f docker-compose.hub.nginx.yml logs

# 检查端口占用
sudo netstat -tulpn | grep :80
```

### 2. 无法访问系统

```bash
# 检查防火墙
sudo ufw status  # Ubuntu
sudo firewall-cmd --list-all  # CentOS

# 开放 80 端口
sudo ufw allow 80  # Ubuntu
```

### 3. API 请求失败

```bash
# 检查后端健康状态
curl http://localhost:8000/api/health

# 查看后端日志
docker logs tradingagents-backend
```

### 4. 导入配置时出现重复键错误

这是正常的！说明数据库中已有数据。如需完全覆盖：

```bash
docker exec -it tradingagents-backend python scripts/import_config_and_create_user.py --overwrite
```

---

## 首次登录后建议

1. **修改默认密码**：右上角用户菜单 → 个人设置 → 修改密码
2. **检查 LLM 配置**：系统管理 → LLM 配置 → 确认 API 密钥已配置
3. **同步股票数据**：系统管理 → 数据同步 → 同步基础数据
4. **测试分析功能**：运行一个简单的股票分析任务

---

## 联系方式

- **GitHub Issues**: https://github.com/hsliuping/TradingAgents-CN/issues
- **邮箱**: hsliup@163.com
- **微信公众号**: TradingAgents-CN
