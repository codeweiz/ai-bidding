from typing import List, Dict, Any
import logging
from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
import uuid
from pathlib import Path

from backend.models.project import Project, ProjectStatus
from backend.schemas.project import ProjectCreate, ProjectResponse, ProjectUpdate

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/projects", tags=["projects"])

# 简单的内存存储（实际项目中应使用数据库）
projects_db: Dict[str, Project] = {}


@router.post("/", response_model=ProjectResponse)
async def create_project(project_data: ProjectCreate) -> ProjectResponse:
    """创建新项目"""
    try:
        project_id = str(uuid.uuid4())
        project = Project(
            id=project_id,
            name=project_data.name,
            description=project_data.description,
            enable_differentiation=project_data.enable_differentiation
        )
        
        projects_db[project_id] = project
        
        logger.info(f"创建项目成功: {project.name} (ID: {project_id})")
        
        return ProjectResponse(
            id=project.id,
            name=project.name,
            description=project.description,
            status=project.status,
            enable_differentiation=project.enable_differentiation,
            created_at=project.created_at,
            updated_at=project.updated_at
        )
        
    except Exception as e:
        logger.error(f"创建项目失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=List[ProjectResponse])
async def list_projects() -> List[ProjectResponse]:
    """获取项目列表"""
    try:
        projects = []
        for project in projects_db.values():
            projects.append(ProjectResponse(
                id=project.id,
                name=project.name,
                description=project.description,
                status=project.status,
                enable_differentiation=project.enable_differentiation,
                created_at=project.created_at,
                updated_at=project.updated_at
            ))
        
        # 按创建时间倒序排列
        projects.sort(key=lambda x: x.created_at, reverse=True)
        return projects
        
    except Exception as e:
        logger.error(f"获取项目列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(project_id: str) -> ProjectResponse:
    """获取项目详情"""
    try:
        if project_id not in projects_db:
            raise HTTPException(status_code=404, detail="项目不存在")
        
        project = projects_db[project_id]
        
        return ProjectResponse(
            id=project.id,
            name=project.name,
            description=project.description,
            status=project.status,
            document_name=project.document_name,
            requirements_analysis=project.requirements_analysis,
            outline=project.outline,
            sections=project.sections,
            final_document_path=project.final_document_path,
            enable_differentiation=project.enable_differentiation,
            created_at=project.created_at,
            updated_at=project.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取项目详情失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(project_id: str, project_data: ProjectUpdate) -> ProjectResponse:
    """更新项目"""
    try:
        if project_id not in projects_db:
            raise HTTPException(status_code=404, detail="项目不存在")
        
        project = projects_db[project_id]
        
        # 更新字段
        if project_data.name is not None:
            project.name = project_data.name
        if project_data.description is not None:
            project.description = project_data.description
        if project_data.enable_differentiation is not None:
            project.enable_differentiation = project_data.enable_differentiation
        
        from datetime import datetime
        project.updated_at = datetime.now()
        
        logger.info(f"更新项目成功: {project.name} (ID: {project_id})")
        
        return ProjectResponse(
            id=project.id,
            name=project.name,
            description=project.description,
            status=project.status,
            enable_differentiation=project.enable_differentiation,
            created_at=project.created_at,
            updated_at=project.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新项目失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{project_id}")
async def delete_project(project_id: str) -> Dict[str, str]:
    """删除项目"""
    try:
        if project_id not in projects_db:
            raise HTTPException(status_code=404, detail="项目不存在")
        
        project = projects_db[project_id]
        del projects_db[project_id]
        
        logger.info(f"删除项目成功: {project.name} (ID: {project_id})")
        
        return {"message": "项目删除成功"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除项目失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{project_id}/download")
async def download_project_document(project_id: str):
    """下载项目生成的文档"""
    try:
        if project_id not in projects_db:
            raise HTTPException(status_code=404, detail="项目不存在")
        
        project = projects_db[project_id]
        
        if not project.final_document_path:
            raise HTTPException(status_code=404, detail="项目文档尚未生成")
        
        file_path = Path(project.final_document_path)
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="文档文件不存在")
        
        return FileResponse(
            path=str(file_path),
            filename=f"{project.name}_技术方案.docx",
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"下载项目文档失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
