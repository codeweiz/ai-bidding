import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from backend.core.toml_config import toml_config
from backend.api.routes import projects, documents, generation, config, formatting

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建FastAPI应用
app = FastAPI(
    title="AI投标方案生成系统",
    description="基于AI的投标方案辅助生成系统",
    version="1.0.0"
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
app.include_router(config.router, prefix="/api")
app.include_router(formatting.router, prefix="/api")

# 创建必要的目录
Path("uploads").mkdir(exist_ok=True)
Path("outputs").mkdir(exist_ok=True)
Path("logs").mkdir(exist_ok=True)
Path("config").mkdir(exist_ok=True)

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
    return {
        "status": "healthy",
        "llm_provider": toml_config.llm.provider,
        "llm_model": toml_config.llm.model_name
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
