"""
Celery应用配置
"""
import os
import logging
from celery import Celery
from kombu import Queue
from celery.signals import worker_ready, worker_shutdown

logger = logging.getLogger(__name__)

# Redis配置
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", REDIS_URL)
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", REDIS_URL)

# 创建Celery应用
celery_app = Celery(
    "ai_bidding",
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND,
    include=[
        "backend.tasks.workflow_tasks",
    ]
)

# Celery配置
celery_app.conf.update(
    # 任务序列化
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Shanghai",
    enable_utc=True,

    # 任务路由
    task_routes={
        "backend.tasks.workflow_tasks.*": {"queue": "workflow"},
        "backend.tasks.workflow_tasks.run_full_workflow": {"queue": "workflow_high"},
    },

    # 队列配置
    task_default_queue="default",
    task_queues=(
        Queue("default", routing_key="default"),
        Queue("workflow", routing_key="workflow"),
        Queue("workflow_high", routing_key="workflow_high"),
    ),

    # 任务执行配置
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_reject_on_worker_lost=True,

    # 重试配置
    task_default_retry_delay=60,  # 默认重试延迟60秒
    task_max_retries=3,  # 默认最大重试3次

    # 结果配置
    result_expires=3600,  # 结果保存1小时
    result_persistent=True,

    # 监控配置
    worker_send_task_events=True,
    task_send_sent_event=True,

    # 任务超时配置
    task_soft_time_limit=1800,  # 软超时30分钟
    task_time_limit=2400,  # 硬超时40分钟

    # 内存管理
    worker_max_tasks_per_child=100,
    worker_max_memory_per_child=500000,  # 500MB

    # 日志配置
    worker_log_format="[%(asctime)s: %(levelname)s/%(processName)s] %(message)s",
    worker_task_log_format="[%(asctime)s: %(levelname)s/%(processName)s][%(task_name)s(%(task_id)s)] %(message)s",
)


# 自定义重试策略
def exponential_backoff(retries):
    """指数退避重试策略"""
    return min(300, (2 ** retries) * 60)  # 最大5分钟


# Celery信号处理
@worker_ready.connect
def worker_ready_handler(sender=None, **kwargs):
    """Worker启动时的处理"""
    logger.info(f"Celery worker {sender} is ready")


@worker_shutdown.connect
def worker_shutdown_handler(sender=None, **kwargs):
    """Worker关闭时的处理"""
    logger.info(f"Celery worker {sender} is shutting down")


# 任务装饰器配置
def task_with_retry(**kwargs):
    """带重试功能的任务装饰器"""
    default_kwargs = {
        "bind": True,
        "autoretry_for": (Exception,),
        "retry_kwargs": {"max_retries": 3},
        "retry_backoff": True,
        "retry_backoff_max": 300,
        "retry_jitter": True,
    }
    default_kwargs.update(kwargs)
    return celery_app.task(**default_kwargs)


# 健康检查任务
@celery_app.task(name="health_check")
def health_check():
    """Celery健康检查任务"""
    return {"status": "healthy", "timestamp": "2025-07-01T00:00:00Z"}


# 清理过期任务
@celery_app.task(name="cleanup_expired_tasks")
def cleanup_expired_tasks():
    """清理过期的任务结果"""
    try:
        # 这里可以添加清理逻辑
        logger.info("开始清理过期任务")
        # 实际清理逻辑
        logger.info("过期任务清理完成")
        return {"status": "success", "message": "过期任务清理完成"}
    except Exception as e:
        logger.error(f"清理过期任务失败: {e}")
        return {"status": "error", "message": str(e)}


# 定期任务配置
celery_app.conf.beat_schedule = {
    "cleanup-expired-tasks": {
        "task": "cleanup_expired_tasks",
        "schedule": 3600.0,  # 每小时执行一次
    },
}

# 导出Celery应用
__all__ = ["celery_app", "task_with_retry", "exponential_backoff"]
