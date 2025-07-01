"""
持久化服务 - 负责任务状态和检查点的持久化管理
"""
import logging
import uuid
from datetime import datetime
from typing import Optional, List

from sqlalchemy import select, update

from backend.core.database import get_db
from backend.models.generation import WorkflowState
from backend.models.task import (
    TaskDB, TaskCheckpointDB, TaskCreate, TaskUpdate,
    TaskResponse, TaskCheckpointCreate, TaskCheckpointResponse,
    TaskStatus
)

logger = logging.getLogger(__name__)


class PersistenceService:
    """持久化服务类"""

    async def create_task(self, task_data: TaskCreate) -> TaskResponse:
        """创建新任务"""
        async for db in get_db():
            try:
                task_id = str(uuid.uuid4())

                db_task = TaskDB(
                    id=task_id,
                    project_id=task_data.project_id,
                    task_type=task_data.task_type.value,
                    config=task_data.config,
                    max_retries=task_data.max_retries,
                    status=TaskStatus.PENDING.value
                )

                db.add(db_task)
                await db.commit()
                await db.refresh(db_task)

                logger.info(f"创建任务成功: {task_id}")
                return TaskResponse.model_validate(db_task)

            except Exception as e:
                await db.rollback()
                logger.error(f"创建任务失败: {e}")
                raise

    async def get_task(self, task_id: str) -> Optional[TaskResponse]:
        """获取任务详情"""
        async for db in get_db():
            try:
                stmt = select(TaskDB).where(TaskDB.id == task_id)
                result = await db.execute(stmt)
                task = result.scalar_one_or_none()

                if task:
                    return TaskResponse.model_validate(task)
                return None

            except Exception as e:
                logger.error(f"获取任务失败: {e}")
                raise

    async def update_task(self, task_id: str, task_update: TaskUpdate) -> Optional[TaskResponse]:
        """更新任务状态"""
        async for db in get_db():
            try:
                # 构建更新数据
                update_data = {}
                if task_update.status is not None:
                    update_data["status"] = task_update.status.value
                if task_update.progress is not None:
                    update_data["progress"] = task_update.progress
                if task_update.current_step is not None:
                    update_data["current_step"] = task_update.current_step
                if task_update.result is not None:
                    update_data["result"] = task_update.result
                if task_update.error_message is not None:
                    update_data["error_message"] = task_update.error_message

                # 添加时间戳
                update_data["updated_at"] = datetime.utcnow()

                # 如果状态变为运行中，设置开始时间
                if task_update.status == TaskStatus.RUNNING:
                    update_data["started_at"] = datetime.utcnow()

                # 如果状态变为完成或失败，设置完成时间
                if task_update.status in [TaskStatus.SUCCESS, TaskStatus.FAILED, TaskStatus.CANCELLED]:
                    update_data["completed_at"] = datetime.utcnow()

                # 执行更新
                stmt = update(TaskDB).where(TaskDB.id == task_id).values(**update_data)
                await db.execute(stmt)
                await db.commit()

                # 返回更新后的任务
                return await self.get_task(task_id)

            except Exception as e:
                await db.rollback()
                logger.error(f"更新任务失败: {e}")
                raise

    async def increment_retry_count(self, task_id: str) -> Optional[TaskResponse]:
        """增加重试次数"""
        async for db in get_db():
            try:
                stmt = (
                    update(TaskDB)
                    .where(TaskDB.id == task_id)
                    .values(
                        retry_count=TaskDB.retry_count + 1,
                        status=TaskStatus.RETRY.value,
                        updated_at=datetime.utcnow()
                    )
                )
                await db.execute(stmt)
                await db.commit()

                return await self.get_task(task_id)

            except Exception as e:
                await db.rollback()
                logger.error(f"增加重试次数失败: {e}")
                raise

    async def create_checkpoint(self, checkpoint_data: TaskCheckpointCreate) -> TaskCheckpointResponse:
        """创建任务检查点"""
        async for db in get_db():
            try:
                checkpoint_id = str(uuid.uuid4())

                db_checkpoint = TaskCheckpointDB(
                    id=checkpoint_id,
                    task_id=checkpoint_data.task_id,
                    step_name=checkpoint_data.step_name,
                    step_order=checkpoint_data.step_order,
                    state_data=checkpoint_data.state_data,
                    started_at=datetime.utcnow()
                )

                db.add(db_checkpoint)
                await db.commit()
                await db.refresh(db_checkpoint)

                logger.info(f"创建检查点成功: {checkpoint_id}")
                return TaskCheckpointResponse.model_validate(db_checkpoint)

            except Exception as e:
                await db.rollback()
                logger.error(f"创建检查点失败: {e}")
                raise

    async def complete_checkpoint(self, checkpoint_id: str) -> Optional[TaskCheckpointResponse]:
        """完成检查点"""
        async for db in get_db():
            try:
                now = datetime.utcnow()

                # 获取检查点以计算持续时间
                stmt = select(TaskCheckpointDB).where(TaskCheckpointDB.id == checkpoint_id)
                result = await db.execute(stmt)
                checkpoint = result.scalar_one_or_none()

                if not checkpoint:
                    return None

                duration = None
                if checkpoint.started_at:
                    duration = int((now - checkpoint.started_at).total_seconds())

                # 更新检查点
                stmt = (
                    update(TaskCheckpointDB)
                    .where(TaskCheckpointDB.id == checkpoint_id)
                    .values(
                        is_completed=True,
                        completed_at=now,
                        duration_seconds=duration,
                        updated_at=now
                    )
                )
                await db.execute(stmt)
                await db.commit()

                # 返回更新后的检查点
                await db.refresh(checkpoint)
                return TaskCheckpointResponse.model_validate(checkpoint)

            except Exception as e:
                await db.rollback()
                logger.error(f"完成检查点失败: {e}")
                raise

    async def get_task_checkpoints(self, task_id: str) -> List[TaskCheckpointResponse]:
        """获取任务的所有检查点"""
        async for db in get_db():
            try:
                stmt = (
                    select(TaskCheckpointDB)
                    .where(TaskCheckpointDB.task_id == task_id)
                    .order_by(TaskCheckpointDB.step_order)
                )
                result = await db.execute(stmt)
                checkpoints = result.scalars().all()

                return [TaskCheckpointResponse.model_validate(cp) for cp in checkpoints]

            except Exception as e:
                logger.error(f"获取任务检查点失败: {e}")
                raise

    async def get_latest_checkpoint(self, task_id: str) -> Optional[TaskCheckpointResponse]:
        """获取任务的最新检查点"""
        async for db in get_db():
            try:
                stmt = (
                    select(TaskCheckpointDB)
                    .where(TaskCheckpointDB.task_id == task_id)
                    .where(TaskCheckpointDB.is_completed == True)
                    .order_by(TaskCheckpointDB.step_order.desc())
                    .limit(1)
                )
                result = await db.execute(stmt)
                checkpoint = result.scalar_one_or_none()

                if checkpoint:
                    return TaskCheckpointResponse.model_validate(checkpoint)
                return None

            except Exception as e:
                logger.error(f"获取最新检查点失败: {e}")
                raise

    async def save_workflow_state(self, task_id: str, step_name: str, state: WorkflowState) -> TaskCheckpointResponse:
        """保存工作流状态为检查点"""
        try:
            # 获取当前步骤顺序
            checkpoints = await self.get_task_checkpoints(task_id)
            step_order = len(checkpoints) + 1

            # 将WorkflowState转换为字典
            state_data = state.model_dump() if hasattr(state, 'model_dump') else state.__dict__

            checkpoint_data = TaskCheckpointCreate(
                task_id=task_id,
                step_name=step_name,
                step_order=step_order,
                state_data=state_data
            )

            checkpoint = await self.create_checkpoint(checkpoint_data)
            await self.complete_checkpoint(checkpoint.id)

            logger.info(f"保存工作流状态成功: {task_id} - {step_name}")
            return checkpoint

        except Exception as e:
            logger.error(f"保存工作流状态失败: {e}")
            raise

    async def restore_workflow_state(self, task_id: str) -> Optional[WorkflowState]:
        """从检查点恢复工作流状态"""
        try:
            latest_checkpoint = await self.get_latest_checkpoint(task_id)

            if latest_checkpoint:
                # 从状态数据恢复WorkflowState
                state_data = latest_checkpoint.state_data
                workflow_state = WorkflowState(**state_data)

                logger.info(f"恢复工作流状态成功: {task_id} - {latest_checkpoint.step_name}")
                return workflow_state

            return None

        except Exception as e:
            logger.error(f"恢复工作流状态失败: {e}")
            raise


# 全局实例
persistence_service = PersistenceService()
