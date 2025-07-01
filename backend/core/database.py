"""
数据库配置和连接管理
"""
import os
import logging
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import MetaData

logger = logging.getLogger(__name__)

# 数据库配置
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./ai_bidding.db")

# 创建异步引擎
engine = create_async_engine(
    DATABASE_URL,
    echo=os.getenv("DATABASE_ECHO", "false").lower() == "true",
    pool_pre_ping=True,
    pool_recycle=300,
)

# 创建会话工厂
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=True,
    autocommit=False,
)

# 元数据配置
metadata = MetaData(
    naming_convention={
        "ix": "ix_%(column_0_label)s",
        "uq": "uq_%(table_name)s_%(column_0_name)s",
        "ck": "ck_%(table_name)s_%(constraint_name)s",
        "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
        "pk": "pk_%(table_name)s"
    }
)


class Base(DeclarativeBase):
    """数据库模型基类"""
    metadata = metadata


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """获取数据库会话"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_database():
    """初始化数据库"""
    logger.info("正在初始化数据库...")
    
    try:
        async with engine.begin() as conn:
            # 创建所有表
            await conn.run_sync(Base.metadata.create_all)
        
        logger.info("数据库初始化完成")
        
    except Exception as e:
        logger.error(f"数据库初始化失败: {e}")
        raise


async def close_database():
    """关闭数据库连接"""
    logger.info("正在关闭数据库连接...")
    await engine.dispose()
    logger.info("数据库连接已关闭")


# 数据库健康检查
async def check_database_health() -> bool:
    """检查数据库连接健康状态"""
    try:
        async with AsyncSessionLocal() as session:
            from sqlalchemy import text
            await session.execute(text("SELECT 1"))
            return True
    except Exception as e:
        logger.error(f"数据库健康检查失败: {e}")
        return False
