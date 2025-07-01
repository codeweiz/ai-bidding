from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field


class GenerationTaskType(str, Enum):
    """生成任务类型枚举"""
    REQUIREMENTS_ANALYSIS = "requirements_analysis"
    OUTLINE_GENERATION = "outline_generation"
    CONTENT_GENERATION = "content_generation"
    DIFFERENTIATION = "differentiation"
    FULL_GENERATION = "full_generation"


class GenerationTaskStatus(str, Enum):
    """生成任务状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class GenerationTask(BaseModel):
    """生成任务模型"""
    id: Optional[str] = None
    project_id: str = Field(..., description="所属项目ID")
    task_type: GenerationTaskType = Field(..., description="任务类型")
    status: GenerationTaskStatus = Field(default=GenerationTaskStatus.PENDING, description="任务状态")
    
    # 输入参数
    input_data: Dict[str, Any] = Field(default_factory=dict, description="输入数据")
    
    # 输出结果
    output_data: Optional[Dict[str, Any]] = Field(None, description="输出数据")
    
    # 错误信息
    error_message: Optional[str] = Field(None, description="错误信息")
    
    # 进度信息
    progress: int = Field(default=0, description="进度百分比")
    current_step: Optional[str] = Field(None, description="当前步骤")
    
    # 时间戳
    created_at: datetime = Field(default_factory=datetime.now)
    started_at: Optional[datetime] = Field(None, description="开始时间")
    completed_at: Optional[datetime] = Field(None, description="完成时间")
    
    class Config:
        use_enum_values = True


class WorkflowState(BaseModel):
    """工作流状态模型"""
    project_id: str = Field(..., description="项目ID")
    current_step: str = Field(..., description="当前步骤")

    # 数据状态
    document_content: Optional[str] = Field(None, description="文档内容")
    requirements_analysis: Optional[str] = Field(None, description="需求分析")
    outline: Optional[str] = Field(None, description="方案提纲")
    sections: List[Dict[str, Any]] = Field(default_factory=list, description="章节列表")

    # 配置
    enable_differentiation: bool = Field(default=True, description="启用差异化")
    enable_validation: bool = Field(default=True, description="启用校验")

    # 新增字段 - 任务和校验相关
    task_id: Optional[str] = Field(None, description="关联的任务ID")
    validation_reports: List[Dict[str, Any]] = Field(default_factory=list, description="校验报告")

    # 重试计数
    requirements_retry_count: int = Field(default=0, description="需求分析重试次数")
    outline_retry_count: int = Field(default=0, description="提纲生成重试次数")
    content_retry_count: int = Field(default=0, description="内容生成重试次数")

    # 错误信息
    error: Optional[str] = Field(None, description="错误信息")

    # 时间戳
    updated_at: datetime = Field(default_factory=datetime.now)
