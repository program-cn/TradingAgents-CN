#!/bin/bash
# 开发环境启动脚本

cd /home/robot/agi/TradingAgents-CN

echo "🚀 启动开发环境..."

# 启动数据库
echo "📦 启动 MongoDB 和 Redis..."
docker compose -f docker-compose.hub.nginx.yml up -d mongodb redis

# 等待数据库就绪
sleep 5

# 启动后端（挂载本地代码）
echo "🔧 启动后端（开发模式）..."
docker compose -f docker-compose.hub.nginx.yml -f docker-compose.dev.yml up -d backend

# 启动前端（开发模式）- 强制使用开发镜像
echo "🎨 启动前端（开发模式）..."

# 检查是否需要重新构建
echo "   检查前端开发镜像..."
if ! docker images | grep -q "tradingagents-frontend-dev"; then
    echo "   构建前端开发镜像..."
    docker compose -f docker-compose.hub.nginx.yml -f docker-compose.dev.yml build --no-cache frontend
fi

# 停止可能存在的生产容器
docker stop tradingagents-frontend 2>/dev/null || true
docker rm tradingagents-frontend 2>/dev/null || true

# 启动前端开发容器
docker compose -f docker-compose.hub.nginx.yml -f docker-compose.dev.yml up -d frontend

echo ""
echo "✅ 开发环境已启动！"
echo ""
echo "📍 访问地址："
echo "   前端开发服务器: http://localhost:5173"
echo "   后端 API:       http://localhost:8000"
echo "   API 文档:       http://localhost:8000/docs"
echo ""
echo "📋 查看日志："
echo "   后端: docker compose logs -f backend"
echo "   前端: docker compose logs -f frontend"
echo ""
echo "🛑 停止服务："
echo "   docker compose -f docker-compose.hub.nginx.yml -f docker-compose.dev.yml down"
echo ""
echo "🔄 重新构建前端："
echo "   docker compose -f docker-compose.hub.nginx.yml -f docker-compose.dev.yml build --no-cache frontend"