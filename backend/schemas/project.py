from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

from backend.models.project import ProjectStatus


class ProjectCreate(BaseModel):
    """创建项目请求"""
    name: str = Field(..., description="项目名称", min_length=1, max_length=100)
    description: Optional[str] = Field(None, description="项目描述", max_length=500)
    enable_differentiation: bool = Field(default=True, description="是否启用差异化处理")


class ProjectUpdate(BaseModel):
    """更新项目请求"""
    name: Optional[str] = Field(None, description="项目名称", min_length=1, max_length=100)
    description: Optional[str] = Field(None, description="项目描述", max_length=500)
    enable_differentiation: Optional[bool] = Field(None, description="是否启用差异化处理")


class ProjectResponse(BaseModel):
    """项目响应"""
    id: str = Field(..., description="项目ID")
    name: str = Field(..., description="项目名称")
    description: Optional[str] = Field(None, description="项目描述")
    status: ProjectStatus = Field(..., description="项目状态")
    
    # 文档信息
    document_name: Optional[str] = Field(None, description="招标文档名称")
    
    # 分析结果
    requirements_analysis: Optional[str] = Field(None, description="需求分析结果")
    outline: Optional[str] = Field(None, description="方案提纲")
    
    # 生成内容
    sections: Optional[List[Dict[str, Any]]] = Field(None, description="章节内容")
    final_document_path: Optional[str] = Field(None, description="最终文档路径")
    
    # 配置选项
    enable_differentiation: bool = Field(..., description="是否启用差异化处理")
    
    # 时间戳
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    
    class Config:
        use_enum_values = True


class SectionResponse(BaseModel):
    """章节响应"""
    title: str = Field(..., description="章节标题")
    level: int = Field(..., description="章节层级")
    order: int = Field(..., description="章节顺序")
    requirements: Optional[str] = Field(None, description="相关需求")
    content: Optional[str] = Field(None, description="章节内容")
    differentiated_content: Optional[str] = Field(None, description="差异化内容")
    is_generated: bool = Field(..., description="是否已生成")
    is_approved: bool = Field(..., description="是否已审核通过")
