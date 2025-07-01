#!/bin/bash

# AI投标系统增强版启动脚本

set -e

echo "🚀 启动AI投标系统增强版..."

# 检查Docker和Docker Compose
if ! command -v docker &> /dev/null; then
    echo "❌ Docker未安装，请先安装Docker"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose未安装，请先安装Docker Compose"
    exit 1
fi

# 创建必要的目录
echo "📁 创建必要的目录..."
mkdir -p uploads outputs logs ssl

# 设置权限
chmod 755 uploads outputs logs

# 检查配置文件
if [ ! -f "config.toml" ]; then
    echo "❌ 配置文件config.toml不存在，请先创建配置文件"
    exit 1
fi

# 检查环境变量文件
if [ ! -f ".env" ]; then
    echo "⚠️  .env文件不存在，将使用默认配置"
    echo "建议创建.env文件并配置相关环境变量"
fi

# 停止现有服务
echo "🛑 停止现有服务..."
docker-compose -f docker-compose.enhanced.yml down --remove-orphans

# 清理旧的镜像（可选）
read -p "是否清理旧的Docker镜像？(y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🧹 清理旧的Docker镜像..."
    docker system prune -f
fi

# 构建镜像
echo "🔨 构建Docker镜像..."
docker-compose -f docker-compose.enhanced.yml build --no-cache

# 启动服务
echo "🚀 启动增强版服务..."
docker-compose -f docker-compose.enhanced.yml up -d

# 等待服务启动
echo "⏳ 等待服务启动..."
sleep 30

# 检查服务状态
echo "🔍 检查服务状态..."
docker-compose -f docker-compose.enhanced.yml ps

# 检查健康状态
echo "🏥 检查应用健康状态..."
max_attempts=30
attempt=1

while [ $attempt -le $max_attempts ]; do
    if curl -f http://localhost:8000/health > /dev/null 2>&1; then
        echo "✅ 后端服务健康检查通过"
        break
    else
        echo "⏳ 等待后端服务启动... ($attempt/$max_attempts)"
        sleep 5
        ((attempt++))
    fi
done

if [ $attempt -gt $max_attempts ]; then
    echo "❌ 后端服务启动失败，请检查日志"
    docker-compose -f docker-compose.enhanced.yml logs backend
    exit 1
fi

# 显示服务信息
echo ""
echo "🎉 AI投标系统增强版启动成功！"
echo ""
echo "📊 服务访问地址："
echo "  - 后端API:        http://localhost:8000"
echo "  - API文档:        http://localhost:8000/docs"
echo "  - 前端界面:       http://localhost:7860"
echo "  - Celery监控:     http://localhost:5555"
echo "  - 数据库:         localhost:5432"
echo "  - Redis:          localhost:6379"
echo ""
echo "🔧 管理命令："
echo "  - 查看日志:       docker-compose -f docker-compose.enhanced.yml logs -f [service]"
echo "  - 停止服务:       docker-compose -f docker-compose.enhanced.yml down"
echo "  - 重启服务:       docker-compose -f docker-compose.enhanced.yml restart [service]"
echo "  - 查看状态:       docker-compose -f docker-compose.enhanced.yml ps"
echo ""
echo "📝 新功能特性："
echo "  ✅ 全自动化LangGraph工作流"
echo "  ✅ 持久化和状态恢复"
echo "  ✅ 内容校验和纠错机制"
echo "  ✅ 异步任务处理(Celery)"
echo "  ✅ Word格式输出解析器"
echo "  ✅ PostgreSQL数据库支持"
echo "  ✅ Redis缓存和消息队列"
echo "  ✅ Flower任务监控"
echo ""
echo "🚀 系统已准备就绪，可以开始使用！"
