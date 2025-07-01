from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field


class DocumentType(str, Enum):
    """文档类型枚举"""
    TENDER = "tender"  # 招标文档
    PROPOSAL = "proposal"  # 投标方案
    TEMPLATE = "template"  # 模板文档


class DocumentStatus(str, Enum):
    """文档状态枚举"""
    UPLOADED = "uploaded"
    PARSING = "parsing"
    PARSED = "parsed"
    FAILED = "failed"


class Document(BaseModel):
    """文档模型"""
    id: Optional[str] = None
    name: str = Field(..., description="文档名称")
    file_path: str = Field(..., description="文件路径")
    file_type: str = Field(..., description="文件类型")
    file_size: int = Field(..., description="文件大小（字节）")
    
    document_type: DocumentType = Field(..., description="文档类型")
    status: DocumentStatus = Field(default=DocumentStatus.UPLOADED, description="文档状态")
    
    # 解析结果
    total_pages: Optional[int] = Field(None, description="总页数")
    total_chunks: Optional[int] = Field(None, description="总块数")
    content: Optional[str] = Field(None, description="文档内容")
    structured_content: Optional[Dict[str, Any]] = Field(None, description="结构化内容")
    
    # 元数据
    metadata: Dict[str, Any] = Field(default_factory=dict, description="文档元数据")
    
    # 时间戳
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    class Config:
        use_enum_values = True


class DocumentChunk(BaseModel):
    """文档块模型"""
    id: Optional[str] = None
    document_id: str = Field(..., description="所属文档ID")
    content: str = Field(..., description="块内容")
    chunk_index: int = Field(..., description="块索引")
    
    # 元数据
    metadata: Dict[str, Any] = Field(default_factory=dict, description="块元数据")
    
    # 时间戳
    created_at: datetime = Field(default_factory=datetime.now)
