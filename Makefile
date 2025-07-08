.PHONY: help install dev-install setup run run-backend run-frontend run-all clean test lint format check build docker-build docker-run docker-compose-up docker-compose-down

# 项目配置
PROJECT_NAME := ai-bidding
PYTHON := python3
PIP := pip
BACKEND_PORT := 8000
FRONTEND_PORT := 7860

# 默认目标
help:
	@echo "🤖 AI投标方案生成系统 - 可用命令："
	@echo ""
	@echo "📦 环境管理:"
	@echo "  make install       - 安装生产环境依赖"
	@echo "  make dev-install   - 安装开发环境依赖"
	@echo "  make setup         - 初始化项目环境"
	@echo "  make clean         - 清理缓存文件"
	@echo ""
	@echo "🚀 运行服务:"
	@echo "  make run           - 一键启动所有服务"
	@echo "  make run-backend   - 启动后端服务 (端口:$(BACKEND_PORT))"
	@echo "  make run-frontend  - 启动前端服务 (端口:$(FRONTEND_PORT))"
	@echo "  make run-all       - 分别启动所有服务"
	@echo ""
	@echo "🧪 测试和质量:"
	@echo "  make test          - 运行测试"
	@echo "  make test-cov      - 运行测试并生成覆盖率报告"
	@echo "  make lint          - 代码检查"
	@echo "  make format        - 代码格式化"
	@echo "  make check         - 完整代码质量检查"
	@echo ""
	@echo "🐳 Docker部署:"
	@echo "  make build         - 构建项目"
	@echo "  make docker-build  - 构建Docker镜像"
	@echo "  make docker-run    - 运行Docker容器"
	@echo "  make docker-compose-up   - 使用docker-compose启动"
	@echo "  make docker-compose-down - 停止docker-compose服务"

# ==================== 环境管理 ====================

install:
	@echo "📦 安装生产环境依赖..."
	$(PIP) install -e .

dev-install:
	@echo "📦 安装开发环境依赖..."
	$(PIP) install -e ".[dev]"

setup: dev-install
	@echo "🔧 初始化项目环境..."
	@mkdir -p uploads outputs logs
	@echo "✅ 项目环境初始化完成"
	@echo "⚠️  请确保在 config.toml 中配置正确的 API 密钥"

# ==================== 运行服务 ====================

run:
	@echo "🚀 启动AI投标方案生成系统..."
	$(PYTHON) run.py

run-backend:
	@echo "🚀 启动后端服务..."
	uvicorn backend.main:app --host 0.0.0.0 --port $(BACKEND_PORT) --reload

run-frontend:
	@echo "🚀 启动前端服务..."
	$(PYTHON) -m frontend.app

# ==================== 测试和质量 ====================

test:
	@echo "🧪 运行测试..."
	pytest tests/ -v

test-cov:
	@echo "🧪 运行测试并生成覆盖率报告..."
	pytest tests/ -v --cov=backend --cov=frontend --cov-report=html --cov-report=term
	@echo "📊 覆盖率报告已生成: htmlcov/index.html"

lint:
	@echo "🔍 代码检查..."
	ruff check backend/ frontend/ tests/

format:
	@echo "🎨 代码格式化..."
	black backend/ frontend/ tests/
	ruff check --fix backend/ frontend/ tests/

check: lint test
	@echo "✅ 代码质量检查完成"

# ==================== 构建和部署 ====================

build:
	@echo "🔨 构建项目..."
	$(PYTHON) -m build

docker-build:
	@echo "🐳 构建Docker镜像..."
	docker build -t $(PROJECT_NAME):latest .

docker-run:
	@echo "🐳 运行Docker容器..."
	docker run -p $(BACKEND_PORT):$(BACKEND_PORT) -p $(FRONTEND_PORT):$(FRONTEND_PORT) \
		-v $(PWD)/uploads:/app/uploads \
		-v $(PWD)/outputs:/app/outputs \
		-v $(PWD)/config.toml:/app/config.toml \
		$(PROJECT_NAME):latest

docker-compose-up:
	@echo "🐳 使用docker-compose启动服务..."
	docker-compose up -d

docker-compose-down:
	@echo "🐳 停止docker-compose服务..."
	docker-compose down

# ==================== 清理 ====================

clean:
	@echo "🧹 清理缓存文件..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name ".coverage" -delete 2>/dev/null || true
	rm -rf htmlcov/ .pytest_cache/ .ruff_cache/ build/ dist/ *.egg-info/
	@echo "✅ 清理完成"

clean-all: clean
	@echo "🧹 深度清理..."
	rm -rf uploads/* outputs/* logs/*
	@echo "✅ 深度清理完成"

# ==================== 开发工具 ====================

dev-server:
	@echo "🔧 启动开发服务器..."
	uvicorn backend.main:app --host 0.0.0.0 --port $(BACKEND_PORT) --reload --log-level debug

logs:
	@echo "📋 查看日志..."
	tail -f logs/app.log

check-config:
	@echo "🔧 检查配置..."
	$(PYTHON) -c "from backend.core.toml_config import toml_config; print('✅ 配置加载成功'); print(f'LLM Provider: {toml_config.llm.provider}'); print(f'Model: {toml_config.llm.model_name}')"

# ==================== 帮助信息 ====================

status:
	@echo "📊 项目状态:"
	@echo "  项目名称: $(PROJECT_NAME)"
	@echo "  Python版本: $(shell $(PYTHON) --version)"
	@echo "  后端端口: $(BACKEND_PORT)"
	@echo "  前端端口: $(FRONTEND_PORT)"
	@echo "  上传目录: $(shell ls -la uploads 2>/dev/null | wc -l) 个文件"
	@echo "  输出目录: $(shell ls -la outputs 2>/dev/null | wc -l) 个文件"