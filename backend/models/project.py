from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field


class ProjectStatus(str, Enum):
    """项目状态枚举"""
    CREATED = "created"
    ANALYZING = "analyzing"
    OUTLINE_GENERATED = "outline_generated"
    CONTENT_GENERATING = "content_generating"
    COMPLETED = "completed"
    FAILED = "failed"


class Project(BaseModel):
    """项目模型"""
    id: Optional[str] = None
    name: str = Field(..., description="项目名称")
    description: Optional[str] = Field(None, description="项目描述")
    status: ProjectStatus = Field(default=ProjectStatus.CREATED, description="项目状态")
    
    # 文档信息
    document_path: Optional[str] = Field(None, description="招标文档路径")
    document_name: Optional[str] = Field(None, description="招标文档名称")
    
    # 分析结果
    requirements_analysis: Optional[str] = Field(None, description="需求分析结果")
    outline: Optional[str] = Field(None, description="方案提纲")
    
    # 生成内容
    sections: List[Dict[str, Any]] = Field(default_factory=list, description="章节内容")
    final_document_path: Optional[str] = Field(None, description="最终文档路径")
    
    # 时间戳
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    # 配置选项
    enable_differentiation: bool = Field(default=True, description="是否启用差异化处理")
    
    class Config:
        use_enum_values = True


class Section(BaseModel):
    """章节模型"""
    id: Optional[str] = None
    project_id: str = Field(..., description="所属项目ID")
    title: str = Field(..., description="章节标题")
    level: int = Field(..., description="章节层级")
    order: int = Field(..., description="章节顺序")
    
    # 内容
    requirements: Optional[str] = Field(None, description="相关需求")
    content: Optional[str] = Field(None, description="章节内容")
    differentiated_content: Optional[str] = Field(None, description="差异化内容")
    
    # 状态
    is_generated: bool = Field(default=False, description="是否已生成")
    is_approved: bool = Field(default=False, description="是否已审核通过")
    
    # 时间戳
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
