"""
任务管理API路由
"""
import logging
from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.database import get_db
from backend.models.task import (
    TaskCreate, TaskUpdate, TaskResponse, TaskCheckpointResponse,
    TaskStatus, TaskType
)
from backend.services.persistence_service import persistence_service
from backend.tasks.workflow_tasks import run_full_workflow

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post("/", response_model=TaskResponse)
async def create_task(
    task_data: TaskCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
) -> TaskResponse:
    """创建新任务"""
    try:
        # 创建任务记录
        task = await persistence_service.create_task(task_data)
        
        # 根据任务类型启动相应的后台任务
        if task_data.task_type == TaskType.FULL_WORKFLOW:
            # 启动完整工作流任务
            document_path = task_data.config.get("document_path")
            if not document_path:
                raise HTTPException(status_code=400, detail="完整工作流任务需要提供document_path")
            
            # 使用Celery异步执行
            run_full_workflow.delay(
                task_id=task.id,
                project_id=task.project_id,
                document_path=document_path,
                config=task_data.config
            )
        
        logger.info(f"创建任务成功: {task.id}")
        return task
        
    except Exception as e:
        logger.error(f"创建任务失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(task_id: str) -> TaskResponse:
    """获取任务详情"""
    try:
        task = await persistence_service.get_task(task_id)
        
        if not task:
            raise HTTPException(status_code=404, detail="任务不存在")
        
        return task
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取任务失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{task_id}", response_model=TaskResponse)
async def update_task(task_id: str, task_update: TaskUpdate) -> TaskResponse:
    """更新任务状态"""
    try:
        task = await persistence_service.update_task(task_id, task_update)
        
        if not task:
            raise HTTPException(status_code=404, detail="任务不存在")
        
        return task
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新任务失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{task_id}/retry", response_model=TaskResponse)
async def retry_task(task_id: str, background_tasks: BackgroundTasks) -> TaskResponse:
    """重试任务"""
    try:
        # 获取任务信息
        task = await persistence_service.get_task(task_id)
        
        if not task:
            raise HTTPException(status_code=404, detail="任务不存在")
        
        # 检查任务状态
        if task.status not in [TaskStatus.FAILED, TaskStatus.CANCELLED]:
            raise HTTPException(status_code=400, detail="只能重试失败或已取消的任务")
        
        # 检查重试次数
        if task.retry_count >= task.max_retries:
            raise HTTPException(status_code=400, detail="已达到最大重试次数")
        
        # 增加重试次数
        updated_task = await persistence_service.increment_retry_count(task_id)
        
        # 重新启动任务
        if task.task_type == TaskType.FULL_WORKFLOW.value:
            document_path = task.config.get("document_path")
            run_full_workflow.delay(
                task_id=task.id,
                project_id=task.project_id,
                document_path=document_path,
                config=task.config
            )
        
        logger.info(f"重试任务: {task_id}")
        return updated_task
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"重试任务失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{task_id}/cancel", response_model=TaskResponse)
async def cancel_task(task_id: str) -> TaskResponse:
    """取消任务"""
    try:
        # 更新任务状态为已取消
        task_update = TaskUpdate(status=TaskStatus.CANCELLED)
        task = await persistence_service.update_task(task_id, task_update)
        
        if not task:
            raise HTTPException(status_code=404, detail="任务不存在")
        
        # TODO: 这里可以添加取消Celery任务的逻辑
        
        logger.info(f"取消任务: {task_id}")
        return task
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"取消任务失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{task_id}/checkpoints", response_model=List[TaskCheckpointResponse])
async def get_task_checkpoints(task_id: str) -> List[TaskCheckpointResponse]:
    """获取任务的所有检查点"""
    try:
        checkpoints = await persistence_service.get_task_checkpoints(task_id)
        return checkpoints
        
    except Exception as e:
        logger.error(f"获取任务检查点失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{task_id}/latest-checkpoint", response_model=TaskCheckpointResponse)
async def get_latest_checkpoint(task_id: str) -> TaskCheckpointResponse:
    """获取任务的最新检查点"""
    try:
        checkpoint = await persistence_service.get_latest_checkpoint(task_id)
        
        if not checkpoint:
            raise HTTPException(status_code=404, detail="未找到检查点")
        
        return checkpoint
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取最新检查点失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{task_id}/status")
async def get_task_status(task_id: str) -> Dict[str, Any]:
    """获取任务状态摘要"""
    try:
        task = await persistence_service.get_task(task_id)
        
        if not task:
            raise HTTPException(status_code=404, detail="任务不存在")
        
        # 获取检查点信息
        checkpoints = await persistence_service.get_task_checkpoints(task_id)
        
        # 计算进度信息
        total_steps = len(checkpoints) if checkpoints else 1
        completed_steps = len([cp for cp in checkpoints if cp.is_completed])
        
        return {
            "task_id": task.id,
            "status": task.status,
            "progress": task.progress,
            "current_step": task.current_step,
            "total_steps": total_steps,
            "completed_steps": completed_steps,
            "retry_count": task.retry_count,
            "max_retries": task.max_retries,
            "started_at": task.started_at,
            "completed_at": task.completed_at,
            "error_message": task.error_message,
            "checkpoints": [
                {
                    "step_name": cp.step_name,
                    "is_completed": cp.is_completed,
                    "completed_at": cp.completed_at
                }
                for cp in checkpoints
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取任务状态失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/project/{project_id}", response_model=List[TaskResponse])
async def get_project_tasks(project_id: str) -> List[TaskResponse]:
    """获取项目的所有任务"""
    try:
        # 这里需要在persistence_service中添加相应的方法
        # 暂时返回空列表
        return []
        
    except Exception as e:
        logger.error(f"获取项目任务失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/")
async def list_tasks(
    status: str = None,
    task_type: str = None,
    limit: int = 50,
    offset: int = 0
) -> Dict[str, Any]:
    """列出任务"""
    try:
        # 这里需要在persistence_service中添加相应的方法
        # 暂时返回空结果
        return {
            "tasks": [],
            "total": 0,
            "limit": limit,
            "offset": offset
        }
        
    except Exception as e:
        logger.error(f"列出任务失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
