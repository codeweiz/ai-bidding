import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from backend.core.toml_config import toml_config
from backend.core.database import init_database, close_database
from backend.api.routes import projects, documents, generation, tasks

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时初始化数据库
    logger.info("正在初始化应用...")
    await init_database()
    logger.info("应用初始化完成")

    yield

    # 关闭时清理资源
    logger.info("正在关闭应用...")
    await close_database()
    logger.info("应用关闭完成")


# 创建FastAPI应用
app = FastAPI(
    title="AI投标方案生成系统",
    description="基于AI的投标方案辅助生成系统",
    version="2.0.0",
    lifespan=lifespan
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生产环境中应该设置具体的域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(projects.router, prefix="/api")
app.include_router(documents.router, prefix="/api")
app.include_router(generation.router, prefix="/api")
app.include_router(tasks.router, prefix="/api")

# 创建必要的目录
Path("uploads").mkdir(exist_ok=True)
Path("outputs").mkdir(exist_ok=True)
Path("logs").mkdir(exist_ok=True)

# 静态文件服务
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
app.mount("/outputs", StaticFiles(directory="outputs"), name="outputs")


@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "AI投标方案生成系统",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    from backend.core.database import check_database_health

    # 检查数据库健康状态
    db_healthy = await check_database_health()

    return {
        "status": "healthy" if db_healthy else "unhealthy",
        "database": "healthy" if db_healthy else "unhealthy",
        "llm_provider": toml_config.llm.provider,
        "llm_model": toml_config.llm.model_name,
        "version": "2.0.0",
        "features": [
            "全自动化LangGraph工作流",
            "持久化和状态恢复",
            "内容校验和纠错",
            "异步任务处理",
            "Word格式输出"
        ]
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
