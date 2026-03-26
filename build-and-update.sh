#!/bin/bash
# TradingAgents-CN 构建并更新脚本
# 用于修改代码后重新构建镜像并重启服务
# 使用方法：./build-and-update.sh [backend|frontend|all]

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

# 参数处理
TARGET=${1:-all}

echo -e "${BLUE}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║     TradingAgents-CN 构建并更新脚本                      ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════╝${NC}"
echo ""

# 检查 Docker
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}✗ Docker 未运行${NC}"
    exit 1
fi

# 构建函数
build_service() {
    local service=$1
    echo -e "${YELLOW}🔨 构建 $service 镜像...${NC}"
    
    if docker compose -f docker-compose.hub.nginx.yml build $service; then
        echo -e "${GREEN}✓ $service 构建成功${NC}"
    else
        echo -e "${RED}✗ $service 构建失败${NC}"
        exit 1
    fi
}

# 重启函数
restart_service() {
    local service=$1
    echo -e "${YELLOW}🔄 重启 $service 服务...${NC}"
    
    docker compose -f docker-compose.hub.nginx.yml up -d $service
    echo -e "${GREEN}✓ $service 重启成功${NC}"
}

# 根据参数构建
case $TARGET in
    backend)
        build_service backend
        restart_service backend
        ;;
    frontend)
        build_service frontend
        restart_service frontend
        ;;
    all)
        echo -e "${YELLOW}🔨 构建所有服务...${NC}"
        build_service backend
        build_service frontend
        echo ""
        echo -e "${YELLOW}🔄 重启所有服务...${NC}"
        restart_service backend
        restart_service frontend
        # 重启 Nginx（依赖前后端）
        docker compose -f docker-compose.hub.nginx.yml restart nginx 2>/dev/null || true
        ;;
    *)
        echo -e "${RED}无效参数: $TARGET${NC}"
        echo -e "${YELLOW}用法: $0 [backend|frontend|all]${NC}"
        exit 1
        ;;
esac

echo ""
echo -e "${BLUE}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}✅ 构建并更新完成！${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════╝${NC}"
echo ""

# 显示状态
echo -e "${BLUE}📋 服务状态：${NC}"
docker compose -f docker-compose.hub.nginx.yml ps
echo ""

# 显示访问地址
echo -e "${BLUE}📍 访问地址：${NC}"
echo -e "   前端:  ${GREEN}http://localhost${NC}"
echo -e "   API:   ${GREEN}http://localhost:8000/api${NC}"
echo ""

# 显示日志提示
echo -e "${BLUE}💡 查看日志：${NC}"
echo -e "   docker compose logs -f backend"
echo -e "   docker compose logs -f frontend"
echo ""
