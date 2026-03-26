#!/bin/bash
# TradingAgents-CN 开发环境快速启动脚本
# 使用方法：./dev-start.sh

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 项目目录
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

echo -e "${BLUE}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║     TradingAgents-CN 开发环境启动脚本                    ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════╝${NC}"
echo ""

# 检查 Docker 是否运行
echo -e "${YELLOW}[1/5] 检查 Docker 环境...${NC}"
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}✗ Docker 未运行，请先启动 Docker${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Docker 运行正常${NC}"

# 检查配置文件
echo -e "${YELLOW}[2/5] 检查配置文件...${NC}"
if [ ! -f ".env" ]; then
    if [ -f ".env.docker" ]; then
        echo -e "${YELLOW}  复制 .env.docker 到 .env...${NC}"
        cp .env.docker .env
    else
        echo -e "${RED}✗ 找不到 .env 配置文件${NC}"
        echo -e "${YELLOW}  请手动创建 .env 文件或复制 .env.docker${NC}"
        exit 1
    fi
fi
echo -e "${GREEN}✓ 配置文件存在${NC}"

# 启动数据库服务
echo -e "${YELLOW}[3/5] 启动数据库服务 (MongoDB + Redis)...${NC}"
docker compose -f docker-compose.hub.nginx.yml up -d mongodb redis

# 等待数据库就绪
echo -e "${YELLOW}  等待数据库就绪...${NC}"
sleep 5

# 检查 MongoDB
if docker compose -f docker-compose.hub.nginx.yml ps mongodb | grep -q "Up"; then
    echo -e "${GREEN}✓ MongoDB 启动成功${NC}"
else
    echo -e "${RED}✗ MongoDB 启动失败${NC}"
    docker compose -f docker-compose.hub.nginx.yml logs mongodb
    exit 1
fi

# 检查 Redis
if docker compose -f docker-compose.hub.nginx.yml ps redis | grep -q "Up"; then
    echo -e "${GREEN}✓ Redis 启动成功${NC}"
else
    echo -e "${RED}✗ Redis 启动失败${NC}"
    docker compose -f docker-compose.hub.nginx.yml logs redis
    exit 1
fi

# 启动后端（开发模式）
echo -e "${YELLOW}[4/5] 启动后端服务（开发模式 - 挂载本地代码）...${NC}"
if [ -f "docker-compose.dev.yml" ]; then
    docker compose -f docker-compose.hub.nginx.yml -f docker-compose.dev.yml up -d backend
    echo -e "${GREEN}✓ 后端启动成功（源码挂载模式）${NC}"
else
    echo -e "${YELLOW}  未找到 docker-compose.dev.yml，使用标准模式启动${NC}"
    docker compose -f docker-compose.hub.nginx.yml up -d backend
    echo -e "${GREEN}✓ 后端启动成功${NC}"
fi

# 启动前端（开发模式）
echo -e "${YELLOW}[5/5] 启动前端服务（开发模式）...${NC}"
if [ -f "docker-compose.dev.yml" ]; then
    docker compose -f docker-compose.hub.nginx.yml -f docker-compose.dev.yml up -d frontend
    echo -e "${GREEN}✓ 前端启动成功（Vite 开发服务器）${NC}"
else
    echo -e "${YELLOW}  未找到 docker-compose.dev.yml，使用标准模式启动${NC}"
    docker compose -f docker-compose.hub.nginx.yml up -d frontend
    echo -e "${GREEN}✓ 前端启动成功${NC}"
fi

# 显示状态
echo ""
echo -e "${BLUE}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}✅ 开发环境启动完成！${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════╝${NC}"
echo ""

echo -e "${BLUE}📍 访问地址：${NC}"
echo -e "   前端开发服务器:  ${GREEN}http://localhost:5173${NC}"
echo -e "   后端 API:        ${GREEN}http://localhost:8000${NC}"
echo -e "   API 文档:        ${GREEN}http://localhost:8000/docs${NC}"
echo -e "   MongoDB:         ${GREEN}localhost:27017${NC}"
echo -e "   Redis:           ${GREEN}localhost:6379${NC}"
echo ""

echo -e "${BLUE}📋 常用命令：${NC}"
echo -e "   查看后端日志:    ${YELLOW}docker compose logs -f backend${NC}"
echo -e "   查看前端日志:    ${YELLOW}docker compose logs -f frontend${NC}"
echo -e "   查看所有服务:    ${YELLOW}docker compose ps${NC}"
echo -e "   停止所有服务:    ${YELLOW}./dev-stop.sh${NC}"
echo ""

echo -e "${BLUE}💡 开发提示：${NC}"
echo -e "   • 后端代码修改后会自动重载（--reload）"
echo -e "   • 前端代码修改后会自动热更新（HMR）"
echo -e "   • 数据库数据保存在 Docker volumes 中"
echo ""
