"""
文档格式化API路由
"""
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel

from backend.services.document_formatter import document_formatter

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/formatting", tags=["文档格式化"])


class RawTextFormatRequest(BaseModel):
    """原始文本格式化请求"""
    raw_text: str
    project_name: str = "格式化文档"
    template_path: Optional[str] = None


class SectionsFormatRequest(BaseModel):
    """章节数据格式化请求"""
    sections: List[Dict[str, Any]]
    project_name: str = "格式化文档"
    template_path: Optional[str] = None


@router.post("/raw-text")
async def format_raw_text(request: RawTextFormatRequest) -> Dict[str, Any]:
    """格式化原始文本为docx文档"""
    try:
        logger.info(f"开始格式化原始文本: {request.project_name}")
        
        # 验证输入
        if not request.raw_text.strip():
            raise HTTPException(status_code=400, detail="原始文本不能为空")
        
        # 执行格式化
        doc_path = await document_formatter.format_raw_text(
            raw_text=request.raw_text,
            project_name=request.project_name,
            template_path=request.template_path
        )
        
        return {
            "status": "success",
            "message": "原始文本格式化完成",
            "file_path": str(doc_path),
            "file_name": doc_path.name
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"格式化原始文本失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sections")
async def format_sections(request: SectionsFormatRequest) -> Dict[str, Any]:
    """格式化章节数据为docx文档"""
    try:
        logger.info(f"开始格式化章节数据: {request.project_name}")
        
        # 验证输入
        if not request.sections:
            raise HTTPException(status_code=400, detail="章节数据不能为空")
        
        # 执行格式化
        doc_path = await document_formatter.format_sections_data(
            sections_data=request.sections,
            project_name=request.project_name,
            template_path=request.template_path
        )
        
        return {
            "status": "success",
            "message": "章节数据格式化完成",
            "file_path": str(doc_path),
            "file_name": doc_path.name
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"格式化章节数据失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/upload-text")
async def format_uploaded_text(
    file: UploadFile = File(...),
    project_name: str = Form("格式化文档"),
    template_path: Optional[str] = Form(None)
) -> Dict[str, Any]:
    """上传文本文件并格式化"""
    try:
        logger.info(f"开始处理上传的文本文件: {file.filename}")
        
        # 验证文件类型
        if not file.filename.endswith(('.txt', '.md')):
            raise HTTPException(status_code=400, detail="只支持.txt和.md文件")
        
        # 读取文件内容
        content = await file.read()
        try:
            raw_text = content.decode('utf-8')
        except UnicodeDecodeError:
            try:
                raw_text = content.decode('gbk')
            except UnicodeDecodeError:
                raise HTTPException(status_code=400, detail="文件编码不支持，请使用UTF-8或GBK编码")
        
        # 验证内容
        if not raw_text.strip():
            raise HTTPException(status_code=400, detail="文件内容为空")
        
        # 执行格式化
        doc_path = await document_formatter.format_raw_text(
            raw_text=raw_text,
            project_name=project_name,
            template_path=template_path
        )
        
        return {
            "status": "success",
            "message": f"文件 {file.filename} 格式化完成",
            "file_path": str(doc_path),
            "file_name": doc_path.name,
            "original_filename": file.filename
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"处理上传文件失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/config")
async def get_format_config() -> Dict[str, Any]:
    """获取格式化配置"""
    try:
        return {
            "status": "success",
            "config": {
                "format_config": document_formatter.format_config,
                "style_mapping": document_formatter.style_mapping
            }
        }
    except Exception as e:
        logger.error(f"获取格式化配置失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/config")
async def update_format_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """更新格式化配置"""
    try:
        # 分离格式化配置和样式映射
        format_config = config.get("format_config", {})
        style_mapping = config.get("style_mapping", {})
        
        if format_config:
            document_formatter.update_format_config(format_config)
        
        if style_mapping:
            document_formatter.update_style_mapping(style_mapping)
        
        return {
            "status": "success",
            "message": "格式化配置更新成功"
        }
    except Exception as e:
        logger.error(f"更新格式化配置失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/templates")
async def list_templates() -> Dict[str, Any]:
    """列出可用的模板文件"""
    try:
        template_dir = Path("tests/data")
        templates = []
        
        if template_dir.exists():
            for file_path in template_dir.glob("*.docx"):
                if "template" in file_path.name.lower():
                    templates.append({
                        "name": file_path.name,
                        "path": str(file_path),
                        "size": file_path.stat().st_size
                    })
        
        return {
            "status": "success",
            "templates": templates,
            "total": len(templates)
        }
    except Exception as e:
        logger.error(f"列出模板文件失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/upload-template")
async def upload_template(file: UploadFile = File(...)) -> Dict[str, Any]:
    """上传新的模板文件"""
    try:
        logger.info(f"开始上传模板文件: {file.filename}")
        
        # 验证文件类型
        if not file.filename.endswith('.docx'):
            raise HTTPException(status_code=400, detail="只支持.docx模板文件")
        
        # 保存文件
        template_dir = Path("tests/data")
        template_dir.mkdir(exist_ok=True)
        
        file_path = template_dir / file.filename
        
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        return {
            "status": "success",
            "message": f"模板文件 {file.filename} 上传成功",
            "file_path": str(file_path),
            "file_name": file.filename
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"上传模板文件失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/outputs")
async def list_output_files() -> Dict[str, Any]:
    """列出输出文件"""
    try:
        output_dir = Path("outputs")
        files = []
        
        if output_dir.exists():
            for file_path in output_dir.glob("*.docx"):
                files.append({
                    "name": file_path.name,
                    "path": str(file_path),
                    "size": file_path.stat().st_size,
                    "created_time": file_path.stat().st_ctime
                })
        
        # 按创建时间倒序排列
        files.sort(key=lambda x: x["created_time"], reverse=True)
        
        return {
            "status": "success",
            "files": files,
            "total": len(files)
        }
    except Exception as e:
        logger.error(f"列出输出文件失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/outputs/{filename}")
async def delete_output_file(filename: str) -> Dict[str, Any]:
    """删除输出文件"""
    try:
        output_dir = Path("outputs")
        file_path = output_dir / filename
        
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="文件不存在")
        
        if not file_path.is_file():
            raise HTTPException(status_code=400, detail="不是有效的文件")
        
        file_path.unlink()
        
        return {
            "status": "success",
            "message": f"文件 {filename} 删除成功"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除文件失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
