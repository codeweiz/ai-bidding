.PHONY: help install dev-install run-backend run-frontend run-celery run-all clean test lint format

# 默认目标
help:
	@echo "Available commands:"
	@echo "  make install       - Install production dependencies"
	@echo "  make dev-install   - Install development dependencies"
	@echo "  make run-backend   - Run FastAPI backend server"
	@echo "  make run-frontend  - Run Gradio frontend"
	@echo "  make run-celery    - Run Celery worker"
	@echo "  make run-all       - Run all services"
	@echo "  make test          - Run tests"
	@echo "  make lint          - Run linting"
	@echo "  make format        - Format code"
	@echo "  make clean         - Clean cache files"

# 安装依赖
install:
	uv pip install -e .

dev-install:
	uv pip install -e ".[dev]"

# 运行服务
run-backend:
	uvicorn backend.main:app --reload --port 8000

run-frontend:
	python -m frontend.app

run-celery:
	celery -A backend.tasks.celery_app worker --loglevel=info

run-redis:
	redis-server

run-mysql:
	@echo "Please ensure MySQL is running on your system"

# 同时运行所有服务（需要多个终端）
run-all:
	@echo "Starting all services..."
	@echo "Please run the following commands in separate terminals:"
	@echo "1. make run-redis"
	@echo "2. make run-mysql"
	@echo "3. make run-celery"
	@echo "4. make run-backend"
	@echo "5. make run-frontend"

# 测试
test:
	pytest tests/ -v --cov=backend --cov-report=html

# 代码质量
lint:
	ruff check backend/ frontend/ tests/

format:
	black backend/ frontend/ tests/
	ruff check --fix backend/ frontend/ tests/

# 清理
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name ".coverage" -delete
	rm -rf htmlcov/
	rm -rf .pytest_cache/
	rm -rf .ruff_cache/

# 数据库迁移
db-init:
	python -m backend.core.database init

db-upgrade:
	python -m backend.core.database upgrade

# 环境设置
setup-env:
	cp .env.example .env
	@echo "Please edit .env file with your configuration"