#!/bin/bash

# AI投标方案生成系统部署脚本
set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 项目配置
PROJECT_NAME="ai-bidding"
DOCKER_IMAGE="$PROJECT_NAME:latest"

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查依赖
check_dependencies() {
    log_info "检查系统依赖..."
    
    if ! command -v docker &> /dev/null; then
        log_error "Docker 未安装，请先安装 Docker"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose 未安装，请先安装 Docker Compose"
        exit 1
    fi
    
    log_success "系统依赖检查通过"
}

# 检查配置文件
check_config() {
    log_info "检查配置文件..."
    
    if [ ! -f "config.toml" ]; then
        log_error "config.toml 文件不存在"
        exit 1
    fi
    
    # 检查API密钥
    if grep -q 'api_key = ""' config.toml; then
        log_warning "请在 config.toml 中配置正确的 API 密钥"
    fi
    
    log_success "配置文件检查通过"
}

# 创建必要目录
create_directories() {
    log_info "创建必要目录..."
    mkdir -p uploads outputs logs
    log_success "目录创建完成"
}

# 构建Docker镜像
build_image() {
    log_info "构建Docker镜像..."
    docker build -t $DOCKER_IMAGE .
    log_success "Docker镜像构建完成"
}

# 部署服务
deploy_services() {
    log_info "部署服务..."
    
    # 停止现有服务
    docker-compose down 2>/dev/null || true
    
    # 启动服务
    docker-compose up -d
    
    log_success "服务部署完成"
}

# 等待服务启动
wait_for_services() {
    log_info "等待服务启动..."
    
    # 等待后端服务
    for i in {1..30}; do
        if curl -f http://localhost:8000/health &>/dev/null; then
            log_success "后端服务启动成功"
            break
        fi
        if [ $i -eq 30 ]; then
            log_error "后端服务启动超时"
            exit 1
        fi
        sleep 2
    done
    
    # 等待前端服务
    sleep 5
    log_success "前端服务启动成功"
}

# 显示服务状态
show_status() {
    log_info "服务状态："
    docker-compose ps
    
    echo ""
    log_success "部署完成！"
    echo -e "${GREEN}🌐 前端界面: http://localhost:7860${NC}"
    echo -e "${GREEN}📊 后端API: http://localhost:8000${NC}"
    echo -e "${GREEN}📚 API文档: http://localhost:8000/docs${NC}"
}

# 清理函数
cleanup() {
    log_info "清理资源..."
    docker-compose down
    docker rmi $DOCKER_IMAGE 2>/dev/null || true
    log_success "清理完成"
}

# 主函数
main() {
    echo -e "${BLUE}"
    echo "🤖 AI投标方案生成系统部署脚本"
    echo "=================================="
    echo -e "${NC}"
    
    case "${1:-deploy}" in
        "deploy")
            check_dependencies
            check_config
            create_directories
            build_image
            deploy_services
            wait_for_services
            show_status
            ;;
        "build")
            check_dependencies
            build_image
            ;;
        "start")
            docker-compose up -d
            wait_for_services
            show_status
            ;;
        "stop")
            log_info "停止服务..."
            docker-compose down
            log_success "服务已停止"
            ;;
        "restart")
            log_info "重启服务..."
            docker-compose restart
            wait_for_services
            show_status
            ;;
        "logs")
            docker-compose logs -f
            ;;
        "status")
            docker-compose ps
            ;;
        "clean")
            cleanup
            ;;
        "help")
            echo "用法: $0 [命令]"
            echo ""
            echo "命令:"
            echo "  deploy   - 完整部署（默认）"
            echo "  build    - 只构建镜像"
            echo "  start    - 启动服务"
            echo "  stop     - 停止服务"
            echo "  restart  - 重启服务"
            echo "  logs     - 查看日志"
            echo "  status   - 查看状态"
            echo "  clean    - 清理资源"
            echo "  help     - 显示帮助"
            ;;
        *)
            log_error "未知命令: $1"
            echo "使用 '$0 help' 查看可用命令"
            exit 1
            ;;
    esac
}

# 捕获中断信号
trap 'log_warning "部署被中断"; exit 1' INT TERM

# 执行主函数
main "$@"
