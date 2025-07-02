"""
异步工作流任务 - 使用Celery执行的工作流任务
"""
import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime
from pathlib import Path

from backend.tasks.celery_app import celery_app, task_with_retry, exponential_backoff
from backend.models.task import TaskStatus, TaskType, TaskUpdate
from backend.models.generation import WorkflowState
from backend.services.persistence_service import persistence_service
from backend.services.validation_service import validation_service
from backend.services.output_parser import output_parser
# from backend.services.enhanced_workflow_engine import enhanced_workflow_engine
from backend.services.workflow_engine import workflow_engine
from backend.services.document_parser import document_parser

logger = logging.getLogger(__name__)


@task_with_retry(
    name="run_full_workflow",
    queue="workflow_high",
    soft_time_limit=1800,  # 30分钟软超时
    time_limit=2400,       # 40分钟硬超时
)
def run_full_workflow(self, task_id: str, project_id: str, document_path: str, config: Dict[str, Any] = None):
    """运行完整的工作流"""
    logger.info(f"开始执行完整工作流任务: {task_id}")
    
    try:
        # 运行异步工作流
        result = asyncio.run(_run_full_workflow_async(task_id, project_id, document_path, config or {}))
        
        logger.info(f"完整工作流任务执行成功: {task_id}")
        return result
        
    except Exception as e:
        logger.error(f"完整工作流任务执行失败: {task_id}, 错误: {e}")
        
        # 更新任务状态为失败
        asyncio.run(persistence_service.update_task(task_id, TaskUpdate(
            status=TaskStatus.FAILED,
            error_message=str(e)
        )))
        
        # 重新抛出异常以触发重试
        raise


async def _run_full_workflow_async(task_id: str, project_id: str, document_path: str, config: Dict[str, Any]):
    """异步执行完整工作流"""
    try:
        # 更新任务状态为运行中
        await persistence_service.update_task(task_id, TaskUpdate(
            status=TaskStatus.RUNNING,
            progress=0,
            current_step="初始化"
        ))
        
        # 检查是否有之前的检查点可以恢复
        restored_state = await persistence_service.restore_workflow_state(task_id)
        
        if restored_state:
            logger.info(f"从检查点恢复工作流状态: {task_id}")
            initial_state = restored_state
        else:
            # 创建初始工作流状态
            logger.info(f"创建新的工作流状态: {task_id}")
            
            # 解析文档
            document_result = document_parser.parse_document(Path(document_path))
            document_content = "\n".join([doc.page_content for doc in document_result["documents"]])
            
            initial_state = WorkflowState(
                project_id=project_id,
                current_step="start",
                document_content=document_content,
                enable_differentiation=config.get("enable_differentiation", True),
                enable_validation=config.get("enable_validation", True)
            )
        
        # 运行增强版工作流引擎
        from backend.services.enhanced_workflow_engine import enhanced_workflow_engine
        final_state = await enhanced_workflow_engine.run_workflow_with_persistence(initial_state, task_id)
        
        # 检查工作流是否成功完成
        if hasattr(final_state, 'error') and final_state.error:
            raise Exception(f"工作流执行失败: {final_state.error}")
        
        # 生成最终的Word文档
        await _update_task_progress(task_id, 90, "生成Word文档")
        
        document_path = await _generate_final_document(final_state, project_id, config)
        
        # 更新任务状态为成功
        result = {
            "status": "success",
            "requirements_analysis": final_state.requirements_analysis,
            "outline": final_state.outline,
            "sections": final_state.sections,
            "document_path": str(document_path),
            "validation_reports": getattr(final_state, 'validation_reports', [])
        }

        await persistence_service.update_task(task_id, TaskUpdate(
            status=TaskStatus.SUCCESS,
            progress=100,
            current_step="完成",
            result=result
        ))
        
        logger.info(f"工作流执行成功: {task_id}")
        return result
        
    except Exception as e:
        logger.error(f"工作流执行失败: {task_id}, 错误: {e}")
        
        # 更新任务状态为失败
        await persistence_service.update_task(task_id, TaskUpdate(
            status=TaskStatus.FAILED,
            error_message=str(e),
            current_step="失败"
        ))
        
        raise


@task_with_retry(
    name="run_workflow_step",
    queue="workflow",
    soft_time_limit=600,   # 10分钟软超时
    time_limit=900,        # 15分钟硬超时
)
def run_workflow_step(self, task_id: str, step_name: str, state_data: Dict[str, Any]):
    """运行单个工作流步骤"""
    logger.info(f"开始执行工作流步骤: {task_id} - {step_name}")
    
    try:
        # 运行异步步骤
        result = asyncio.run(_run_workflow_step_async(task_id, step_name, state_data))
        
        logger.info(f"工作流步骤执行成功: {task_id} - {step_name}")
        return result
        
    except Exception as e:
        logger.error(f"工作流步骤执行失败: {task_id} - {step_name}, 错误: {e}")
        
        # 更新任务状态
        asyncio.run(persistence_service.update_task(task_id, TaskUpdate(
            error_message=f"步骤 {step_name} 执行失败: {str(e)}"
        )))
        
        raise


async def _run_workflow_step_async(task_id: str, step_name: str, state_data: Dict[str, Any]):
    """异步执行单个工作流步骤"""
    try:
        # 从状态数据恢复WorkflowState
        workflow_state = WorkflowState(**state_data)
        
        # 根据步骤名称执行相应的操作（暂时使用原版工作流引擎）
        if step_name == "parse_document":
            result = await workflow_engine._parse_document(workflow_state)
        elif step_name == "analyze_requirements":
            result = await workflow_engine._analyze_requirements(workflow_state)
        elif step_name == "generate_outline":
            result = await workflow_engine._generate_outline(workflow_state)
        elif step_name == "generate_content":
            result = await workflow_engine._generate_content(workflow_state)
        elif step_name == "differentiate_content":
            result = await workflow_engine._differentiate_content(workflow_state)
        else:
            raise ValueError(f"未知的工作流步骤: {step_name}")
        
        # 保存步骤结果
        await persistence_service.save_workflow_state(task_id, step_name, result)
        
        return {
            "status": "success",
            "step_name": step_name,
            "state": result.model_dump() if hasattr(result, 'model_dump') else result.__dict__
        }
        
    except Exception as e:
        logger.error(f"工作流步骤执行失败: {step_name}, 错误: {e}")
        raise


async def _update_task_progress(task_id: str, progress: int, current_step: str):
    """更新任务进度"""
    try:
        await persistence_service.update_task(task_id, {
            "progress": progress,
            "current_step": current_step
        })
    except Exception as e:
        logger.warning(f"更新任务进度失败: {e}")


async def _generate_final_document(state: WorkflowState, project_id: str, config: Dict[str, Any]) -> Path:
    """生成最终的Word文档"""
    try:
        # 解析内容为文档章节
        if hasattr(state, 'sections') and state.sections:
            # 从章节数据创建文档
            sections = []
            for section_data in state.sections:
                if isinstance(section_data, dict):
                    title = section_data.get('title', '未命名章节')
                    level = section_data.get('level', 1)
                    content = section_data.get('differentiated_content') or section_data.get('content', '')
                    
                    from backend.services.output_parser import DocumentSection
                    doc_section = DocumentSection(title=title, level=level, content=content)
                    sections.append(doc_section)
        else:
            # 从纯文本解析
            content = getattr(state, 'final_content', '') or str(state.sections)
            outline = getattr(state, 'outline', '')
            sections = output_parser.parse_plain_text_to_sections(content, outline)
        
        # 准备元数据
        metadata = {
            "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "项目ID": project_id,
            "启用差异化": config.get("enable_differentiation", True),
            "启用校验": config.get("enable_validation", True)
        }
        
        # 创建Word文档
        project_name = config.get("project_name", f"项目_{project_id[:8]}")
        document_path = output_parser.create_word_document(sections, project_name, metadata)
        
        return document_path
        
    except Exception as e:
        logger.error(f"生成最终文档失败: {e}")
        raise


# 健康检查任务
@celery_app.task(name="workflow_health_check")
def workflow_health_check():
    """工作流健康检查"""
    try:
        # 检查各个服务的健康状态
        health_status = {
            "timestamp": datetime.now().isoformat(),
            "services": {}
        }
        
        # 检查持久化服务
        try:
            asyncio.run(persistence_service.get_task("health_check"))
            health_status["services"]["persistence"] = "healthy"
        except Exception:
            health_status["services"]["persistence"] = "unhealthy"
        
        # 检查工作流引擎
        try:
            health_status["services"]["workflow_engine"] = "healthy"
        except Exception:
            health_status["services"]["workflow_engine"] = "unhealthy"
        
        return health_status
        
    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        return {"status": "error", "message": str(e)}


# 清理任务
@celery_app.task(name="cleanup_old_tasks")
def cleanup_old_tasks(days_old: int = 7):
    """清理旧的任务数据"""
    try:
        logger.info(f"开始清理 {days_old} 天前的任务数据")
        
        # 这里可以添加清理逻辑
        # 例如删除旧的检查点、任务记录等
        
        logger.info("任务数据清理完成")
        return {"status": "success", "message": f"清理了 {days_old} 天前的任务数据"}
        
    except Exception as e:
        logger.error(f"清理任务数据失败: {e}")
        return {"status": "error", "message": str(e)}
