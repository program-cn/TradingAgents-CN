#!/bin/bash
# TradingAgents-CN 开发环境停止脚本
# 使用方法：./dev-stop.sh

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 项目目录
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

echo -e "${BLUE}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║     TradingAgents-CN 开发环境停止脚本                    ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════╝${NC}"
echo ""

# 询问是否停止数据库
echo -e "${YELLOW}请选择停止模式：${NC}"
echo -e "  1) 仅停止前后端服务（保留数据库）"
echo -e "  2) 停止所有服务（包括数据库）"
echo -e "  3) 取消"
echo ""
read -p "请输入选项 [1-3]: " choice

case $choice in
    1)
        echo -e "${YELLOW}停止前后端服务...${NC}"
        docker compose -f docker-compose.hub.nginx.yml stop backend frontend nginx 2>/dev/null || true
        docker compose -f docker-compose.hub.nginx.yml rm -f backend frontend nginx 2>/dev/null || true
        echo -e "${GREEN}✓ 前后端服务已停止${NC}"
        echo -e "${BLUE}数据库服务仍在运行${NC}"
        ;;
    2)
        echo -e "${YELLOW}停止所有服务...${NC}"
        docker compose -f docker-compose.hub.nginx.yml down
        echo -e "${GREEN}✓ 所有服务已停止${NC}"
        ;;
    3)
        echo -e "${YELLOW}已取消${NC}"
        exit 0
        ;;
    *)
        echo -e "${RED}无效选项${NC}"
        exit 1
        ;;
esac

echo ""
echo -e "${BLUE}📋 当前服务状态：${NC}"
docker compose -f docker-compose.hub.nginx.yml ps 2>/dev/null || echo "  无运行服务"
echo ""
