from typing import Dict, Any
import logging
from fastapi import APIRouter, HTTPException, BackgroundTasks
from datetime import datetime

from backend.models.project import ProjectStatus
from backend.services.content_generator import content_generator
from backend.schemas.generation import (
    GenerationRequest,
    OutlineGenerationRequest,
    SectionGenerationRequest
)

# 进度跟踪回调函数
def update_task_progress(task_id: str, progress: int, step: str, error: str = None):
    """更新任务进度"""
    if task_id in generation_tasks:
        generation_tasks[task_id]["progress"] = progress
        generation_tasks[task_id]["current_step"] = step
        if error:
            generation_tasks[task_id]["status"] = "failed"
            generation_tasks[task_id]["error"] = error
        generation_tasks[task_id]["updated_at"] = datetime.now()

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/generation", tags=["generation"])

# 简单的任务状态存储
generation_tasks: Dict[str, Dict[str, Any]] = {}


@router.post("/full")
async def generate_full_proposal(
    request: GenerationRequest,
    background_tasks: BackgroundTasks
) -> Dict[str, Any]:
    """生成完整投标方案"""
    try:
        # 获取项目信息
        from backend.api.routes.projects import projects_db
        
        if request.project_id not in projects_db:
            raise HTTPException(status_code=404, detail="项目不存在")
        
        project = projects_db[request.project_id]
        
        # 更新项目状态
        project.status = ProjectStatus.ANALYZING
        project.updated_at = datetime.now()
        
        # 创建任务ID
        import uuid
        task_id = str(uuid.uuid4())
        
        # 记录任务状态
        generation_tasks[task_id] = {
            "status": "running",
            "project_id": request.project_id,
            "started_at": datetime.now(),
            "progress": 0
        }
        
        # 在后台执行生成任务
        background_tasks.add_task(
            _run_full_generation_task,
            task_id,
            project,
            request.document_path,
            request.template_path
        )
        
        return {
            "status": "success",
            "message": "生成任务已启动",
            "task_id": task_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"启动生成任务失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/outline")
async def generate_outline(request: OutlineGenerationRequest) -> Dict[str, Any]:
    """生成方案提纲"""
    try:
        result = await content_generator.generate_outline_only(request.requirements_analysis)
        
        if result["status"] == "success":
            return {
                "status": "success",
                "outline": result["outline"]
            }
        else:
            raise HTTPException(status_code=500, detail=result["error"])
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"生成提纲失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/section")
async def generate_section(request: SectionGenerationRequest) -> Dict[str, Any]:
    """生成章节内容"""
    try:
        result = await content_generator.generate_section_content(
            section_title=request.section_title,
            requirements=request.requirements,
            context=request.context
        )
        
        if result["status"] == "success":
            return {
                "status": "success",
                "content": result["content"]
            }
        else:
            raise HTTPException(status_code=500, detail=result["error"])
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"生成章节内容失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/task/{task_id}")
async def get_task_status(task_id: str) -> Dict[str, Any]:
    """获取生成任务状态"""
    try:
        if task_id not in generation_tasks:
            raise HTTPException(status_code=404, detail="任务不存在")
        
        task = generation_tasks[task_id]
        
        return {
            "status": "success",
            "task": task
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取任务状态失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/outputs")
async def list_output_files() -> Dict[str, Any]:
    """获取输出文件列表"""
    try:
        files = content_generator.get_output_files()
        
        return {
            "status": "success",
            "files": files,
            "total": len(files)
        }
        
    except Exception as e:
        logger.error(f"获取输出文件列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def _run_full_generation_task(task_id: str, project, document_path: str, template_path: str = None):
    """运行完整生成任务（后台任务）"""
    try:
        logger.info(f"开始执行生成任务: {task_id}")

        # 更新任务状态
        update_task_progress(task_id, 10, "解析招标文档")

        # 执行生成
        result = await content_generator.generate_proposal(project, document_path, template_path)
        
        if result["status"] == "success":
            # 更新项目信息
            project.status = ProjectStatus.COMPLETED
            project.requirements_analysis = result["requirements_analysis"]
            project.outline = result["outline"]
            project.sections = result["sections"]
            project.final_document_path = result["document_path"]
            project.updated_at = datetime.now()
            
            # 更新任务状态
            generation_tasks[task_id].update({
                "status": "completed",
                "progress": 100,
                "completed_at": datetime.now(),
                "result": {
                    "document_path": result["document_path"]
                }
            })
            
            logger.info(f"生成任务完成: {task_id}")
            
        else:
            # 更新项目状态为失败
            project.status = ProjectStatus.FAILED
            project.updated_at = datetime.now()
            
            # 更新任务状态
            generation_tasks[task_id].update({
                "status": "failed",
                "error": result["error"],
                "completed_at": datetime.now()
            })
            
            logger.error(f"生成任务失败: {task_id}, 错误: {result['error']}")
            
    except Exception as e:
        logger.error(f"生成任务异常: {task_id}, 错误: {e}")
        
        # 更新项目状态为失败
        project.status = ProjectStatus.FAILED
        project.updated_at = datetime.now()
        
        # 更新任务状态
        generation_tasks[task_id].update({
            "status": "failed",
            "error": str(e),
            "completed_at": datetime.now()
        })
