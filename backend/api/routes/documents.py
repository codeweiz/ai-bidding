from typing import Dict, Any
import logging
import shutil
from pathlib import Path
from fastapi import APIRouter, HTTPException, UploadFile, File

from backend.services.content_generator import content_generator
from backend.schemas.generation import AnalysisRequest

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/documents", tags=["documents"])

# 上传文件存储目录
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


@router.post("/upload")
async def upload_document(file: UploadFile = File(...)) -> Dict[str, Any]:
    """上传招标文档"""
    try:
        # 检查文件类型
        allowed_types = [".pdf", ".docx", ".doc"]
        file_suffix = Path(file.filename).suffix.lower()
        
        if file_suffix not in allowed_types:
            raise HTTPException(
                status_code=400, 
                detail=f"不支持的文件类型: {file_suffix}。支持的类型: {', '.join(allowed_types)}"
            )
        
        # 保存文件
        file_path = UPLOAD_DIR / file.filename
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        logger.info(f"文档上传成功: {file.filename}")
        
        return {
            "status": "success",
            "message": "文档上传成功",
            "file_path": str(file_path),
            "file_name": file.filename,
            "file_size": file_path.stat().st_size
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"文档上传失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze")
async def analyze_document(request: AnalysisRequest) -> Dict[str, Any]:
    """分析招标文档需求"""
    try:
        if not Path(request.file_path).exists():
            raise HTTPException(status_code=404, detail="文件不存在")

        result = await content_generator.analyze_requirements_only(request.file_path)

        if result["status"] == "success":
            return {
                "status": "success",
                "analysis": result["analysis"],
                "document_info": result["document_info"]
            }
        else:
            raise HTTPException(status_code=500, detail=result["error"])

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"文档分析失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/parse")
async def parse_document(request: AnalysisRequest) -> Dict[str, Any]:
    """解析文档结构"""
    try:
        if not Path(request.file_path).exists():
            raise HTTPException(status_code=404, detail="文件不存在")

        from backend.services.document_parser import document_parser
        result = document_parser.parse_document(Path(request.file_path))
        
        # 提取文档内容预览（前1000字符）
        content_preview = ""
        if result["documents"]:
            full_content = "\n".join([doc.page_content for doc in result["documents"]])
            content_preview = full_content[:1000] + "..." if len(full_content) > 1000 else full_content
        
        return {
            "status": "success",
            "file_name": result["file_name"],
            "file_type": result["file_type"],
            "metadata": result["metadata"],
            "content_preview": content_preview,
            "total_chunks": len(result["chunks"])
        }
        
    except Exception as e:
        logger.error(f"文档解析失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/uploads")
async def list_uploaded_files() -> Dict[str, Any]:
    """获取已上传文件列表"""
    try:
        files = []
        
        if UPLOAD_DIR.exists():
            for file_path in UPLOAD_DIR.iterdir():
                if file_path.is_file():
                    stat = file_path.stat()
                    files.append({
                        "name": file_path.name,
                        "path": str(file_path),
                        "size": stat.st_size,
                        "created_at": stat.st_ctime,
                        "modified_at": stat.st_mtime
                    })
        
        # 按修改时间倒序排列
        files.sort(key=lambda x: x["modified_at"], reverse=True)
        
        return {
            "status": "success",
            "files": files,
            "total": len(files)
        }
        
    except Exception as e:
        logger.error(f"获取文件列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
