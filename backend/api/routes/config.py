"""
配置管理API路由
"""
import logging
from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.services.config_manager import config_manager
from backend.services.llm_manager import llm_manager
from backend.services.document_formatter import document_formatter

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/config", tags=["配置管理"])


class ConfigUpdateRequest(BaseModel):
    """配置更新请求"""
    updates: Dict[str, Any]


class ProviderConfigRequest(BaseModel):
    """Provider配置请求"""
    name: str
    provider_type: str
    config: Dict[str, Any]


class PromptUpdateRequest(BaseModel):
    """Prompt更新请求"""
    prompt_key: str
    prompt_value: str


class FormatConfigRequest(BaseModel):
    """格式化配置请求"""
    config: Dict[str, Any]


@router.get("/")
async def get_all_config() -> Dict[str, Any]:
    """获取所有配置"""
    try:
        return {
            "status": "success",
            "config": config_manager.get_all_config()
        }
    except Exception as e:
        logger.error(f"获取配置失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/llm")
async def get_llm_config() -> Dict[str, Any]:
    """获取LLM配置"""
    try:
        return {
            "status": "success",
            "config": config_manager.get_llm_config()
        }
    except Exception as e:
        logger.error(f"获取LLM配置失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/llm")
async def update_llm_config(request: ConfigUpdateRequest) -> Dict[str, Any]:
    """更新LLM配置"""
    try:
        # 更新配置
        for key, value in request.updates.items():
            config_manager.set(f"llm.{key}", value)
        
        # 同步到LLM管理器
        llm_manager.update_config(request.updates)
        
        return {
            "status": "success",
            "message": "LLM配置更新成功"
        }
    except Exception as e:
        logger.error(f"更新LLM配置失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/prompts")
async def get_all_prompts() -> Dict[str, Any]:
    """获取所有Prompt配置"""
    try:
        prompts = config_manager.get("prompts", {})
        return {
            "status": "success",
            "prompts": prompts
        }
    except Exception as e:
        logger.error(f"获取Prompt配置失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/prompts/{prompt_key}")
async def get_prompt(prompt_key: str) -> Dict[str, Any]:
    """获取指定Prompt"""
    try:
        prompt_value = config_manager.get_prompt(prompt_key)
        return {
            "status": "success",
            "prompt_key": prompt_key,
            "prompt_value": prompt_value
        }
    except Exception as e:
        logger.error(f"获取Prompt失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/prompts")
async def update_prompt(request: PromptUpdateRequest) -> Dict[str, Any]:
    """更新Prompt配置"""
    try:
        config_manager.set_prompt(request.prompt_key, request.prompt_value)
        
        # 同步到LLM管理器
        llm_manager.set_custom_prompt(request.prompt_key, request.prompt_value)
        
        return {
            "status": "success",
            "message": f"Prompt '{request.prompt_key}' 更新成功"
        }
    except Exception as e:
        logger.error(f"更新Prompt失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/providers")
async def get_providers() -> Dict[str, Any]:
    """获取所有Provider配置"""
    try:
        providers = config_manager.get_provider_config()
        return {
            "status": "success",
            "providers": providers
        }
    except Exception as e:
        logger.error(f"获取Provider配置失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/providers")
async def add_provider(request: ProviderConfigRequest) -> Dict[str, Any]:
    """添加新的Provider"""
    try:
        # 添加到配置管理器
        config_manager.add_provider(request.name, {
            "type": request.provider_type,
            **request.config
        })
        
        # 添加到LLM管理器
        success = llm_manager.add_provider(request.name, request.provider_type, request.config)
        
        if success:
            return {
                "status": "success",
                "message": f"Provider '{request.name}' 添加成功"
            }
        else:
            raise HTTPException(status_code=400, detail="添加Provider失败")
            
    except Exception as e:
        logger.error(f"添加Provider失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/providers/{provider_name}/switch")
async def switch_provider(provider_name: str) -> Dict[str, Any]:
    """切换Provider"""
    try:
        # 切换LLM管理器的Provider
        success = llm_manager.switch_provider(provider_name)
        
        if success:
            # 更新默认配置
            config_manager.set_default_provider(provider_name)
            
            return {
                "status": "success",
                "message": f"已切换到Provider: {provider_name}"
            }
        else:
            raise HTTPException(status_code=404, detail=f"Provider不存在: {provider_name}")
            
    except Exception as e:
        logger.error(f"切换Provider失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/formatting")
async def get_formatting_config() -> Dict[str, Any]:
    """获取格式化配置"""
    try:
        formatting_config = config_manager.get_formatting_config()
        return {
            "status": "success",
            "config": formatting_config
        }
    except Exception as e:
        logger.error(f"获取格式化配置失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/formatting")
async def update_formatting_config(request: FormatConfigRequest) -> Dict[str, Any]:
    """更新格式化配置"""
    try:
        # 更新配置管理器
        for key, value in request.config.items():
            config_manager.set(f"formatting.{key}", value)
        
        # 同步到文档格式化器
        document_formatter.update_format_config(request.config)
        
        return {
            "status": "success",
            "message": "格式化配置更新成功"
        }
    except Exception as e:
        logger.error(f"更新格式化配置失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/workflow")
async def get_workflow_config() -> Dict[str, Any]:
    """获取工作流配置"""
    try:
        workflow_config = config_manager.get_workflow_config()
        return {
            "status": "success",
            "config": workflow_config
        }
    except Exception as e:
        logger.error(f"获取工作流配置失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/workflow")
async def update_workflow_config(request: ConfigUpdateRequest) -> Dict[str, Any]:
    """更新工作流配置"""
    try:
        for key, value in request.updates.items():
            config_manager.set(f"workflow.{key}", value)
        
        return {
            "status": "success",
            "message": "工作流配置更新成功"
        }
    except Exception as e:
        logger.error(f"更新工作流配置失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/export")
async def export_config() -> Dict[str, Any]:
    """导出配置"""
    try:
        file_path = config_manager.export_config()
        return {
            "status": "success",
            "message": "配置导出成功",
            "file_path": file_path
        }
    except Exception as e:
        logger.error(f"导出配置失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reset")
async def reset_config() -> Dict[str, Any]:
    """重置配置为默认值"""
    try:
        config_manager.reset_to_default()
        return {
            "status": "success",
            "message": "配置已重置为默认值"
        }
    except Exception as e:
        logger.error(f"重置配置失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
