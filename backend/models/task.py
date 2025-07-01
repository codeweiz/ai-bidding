"""
任务相关数据模型
"""
from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum
from sqlalchemy import Column, String, DateTime, Text, JSON, Integer, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from pydantic import BaseModel, Field

from backend.core.database import Base


class TaskStatus(str, Enum):
    """任务状态枚举"""
    PENDING = "pending"          # 等待执行
    RUNNING = "running"          # 正在执行
    SUCCESS = "success"          # 执行成功
    FAILED = "failed"            # 执行失败
    RETRY = "retry"              # 重试中
    CANCELLED = "cancelled"      # 已取消


class TaskType(str, Enum):
    """任务类型枚举"""
    FULL_WORKFLOW = "full_workflow"           # 完整工作流
    PARSE_DOCUMENT = "parse_document"         # 文档解析
    ANALYZE_REQUIREMENTS = "analyze_requirements"  # 需求分析
    GENERATE_OUTLINE = "generate_outline"     # 生成提纲
    GENERATE_CONTENT = "generate_content"     # 生成内容
    DIFFERENTIATE_CONTENT = "differentiate_content"  # 差异化处理
    VALIDATE_CONTENT = "validate_content"     # 内容校验
    GENERATE_DOCUMENT = "generate_document"   # 生成文档


# SQLAlchemy 数据库模型
class TaskDB(Base):
    """任务数据库模型"""
    __tablename__ = "tasks"
    
    id = Column(String, primary_key=True)
    project_id = Column(String, ForeignKey("projects.id"), nullable=False)
    task_type = Column(String, nullable=False)
    status = Column(String, default=TaskStatus.PENDING)
    
    # 任务配置
    config = Column(JSON, default=dict)
    
    # 执行信息
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    
    # 结果和错误
    result = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    error_traceback = Column(Text, nullable=True)
    
    # 进度信息
    progress = Column(Integer, default=0)  # 0-100
    current_step = Column(String, nullable=True)
    total_steps = Column(Integer, default=1)
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    project = relationship("ProjectDB", back_populates="tasks")
    checkpoints = relationship("TaskCheckpointDB", back_populates="task", cascade="all, delete-orphan")


class TaskCheckpointDB(Base):
    """任务检查点数据库模型"""
    __tablename__ = "task_checkpoints"
    
    id = Column(String, primary_key=True)
    task_id = Column(String, ForeignKey("tasks.id"), nullable=False)
    step_name = Column(String, nullable=False)
    step_order = Column(Integer, nullable=False)
    
    # 状态数据
    state_data = Column(JSON, nullable=False)
    
    # 执行信息
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    duration_seconds = Column(Integer, nullable=True)
    
    # 状态
    is_completed = Column(Boolean, default=False)
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    task = relationship("TaskDB", back_populates="checkpoints")


# Pydantic 模型用于API
class TaskCreate(BaseModel):
    """创建任务请求模型"""
    project_id: str = Field(..., description="项目ID")
    task_type: TaskType = Field(..., description="任务类型")
    config: Dict[str, Any] = Field(default_factory=dict, description="任务配置")
    max_retries: int = Field(default=3, description="最大重试次数")


class TaskUpdate(BaseModel):
    """更新任务请求模型"""
    status: Optional[TaskStatus] = Field(None, description="任务状态")
    progress: Optional[int] = Field(None, description="进度百分比")
    current_step: Optional[str] = Field(None, description="当前步骤")
    result: Optional[Dict[str, Any]] = Field(None, description="执行结果")
    error_message: Optional[str] = Field(None, description="错误信息")


class TaskResponse(BaseModel):
    """任务响应模型"""
    id: str
    project_id: str
    task_type: TaskType
    status: TaskStatus
    
    config: Dict[str, Any]
    
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    retry_count: int
    max_retries: int
    
    result: Optional[Dict[str, Any]]
    error_message: Optional[str]
    
    progress: int
    current_step: Optional[str]
    total_steps: int
    
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class TaskCheckpointCreate(BaseModel):
    """创建检查点请求模型"""
    task_id: str = Field(..., description="任务ID")
    step_name: str = Field(..., description="步骤名称")
    step_order: int = Field(..., description="步骤顺序")
    state_data: Dict[str, Any] = Field(..., description="状态数据")


class TaskCheckpointResponse(BaseModel):
    """检查点响应模型"""
    id: str
    task_id: str
    step_name: str
    step_order: int
    
    state_data: Dict[str, Any]
    
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    duration_seconds: Optional[int]
    
    is_completed: bool
    
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
