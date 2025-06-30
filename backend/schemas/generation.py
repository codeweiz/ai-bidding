from typing import Optional
from pydantic import BaseModel, Field


class GenerationRequest(BaseModel):
    """完整生成请求"""
    project_id: str = Field(..., description="项目ID")
    document_path: str = Field(..., description="招标文档路径")


class OutlineGenerationRequest(BaseModel):
    """提纲生成请求"""
    requirements_analysis: str = Field(..., description="需求分析结果")


class SectionGenerationRequest(BaseModel):
    """章节生成请求"""
    section_title: str = Field(..., description="章节标题")
    requirements: str = Field(..., description="相关需求")
    context: Optional[str] = Field("", description="上下文信息")


class AnalysisRequest(BaseModel):
    """需求分析请求"""
    document_path: str = Field(..., description="文档路径")


class DifferentiationRequest(BaseModel):
    """差异化处理请求"""
    original_content: str = Field(..., description="原始内容")


class TaskStatusResponse(BaseModel):
    """任务状态响应"""
    task_id: str = Field(..., description="任务ID")
    status: str = Field(..., description="任务状态")
    progress: int = Field(..., description="进度百分比")
    current_step: Optional[str] = Field(None, description="当前步骤")
    error: Optional[str] = Field(None, description="错误信息")
    started_at: Optional[str] = Field(None, description="开始时间")
    completed_at: Optional[str] = Field(None, description="完成时间")
