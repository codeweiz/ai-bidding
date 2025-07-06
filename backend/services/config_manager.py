"""
配置管理服务 - 动态配置管理
"""
import logging
import json
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class ConfigManager:
    """配置管理器 - 支持动态配置和持久化"""
    
    def __init__(self):
        self.config_file = Path("config/dynamic_config.json")
        self.config_file.parent.mkdir(exist_ok=True)
        
        # 默认配置
        self.default_config = {
            "llm": {
                "temperature": 0.2,
                "max_tokens": 4000,
                "retry_config": {
                    "max_retries": 3,
                    "retry_delay": 1.0,
                    "enable_format_validation": True
                }
            },
            "prompts": {
                "system_prompt_prefix": "",
                "iptv_expert_prompt": """你是一位资深的IPTV系统专家，具有15年以上的广电行业经验。请基于招标文档要求，生成专业的技术方案内容。

要求：
1. 紧扣招标需求，不要自由发挥
2. 使用专业术语，体现技术深度
3. 避免输出售后、验收、质量保障等通用内容
4. 可以包含PlantUML或Mermaid技术架构图代码
5. 内容要有针对性和差异化
6. 字数控制在800-1500字

请确保内容专业、准确、有针对性。""",
                "outline_generation_prompt": """请基于招标文档生成IPTV系统技术方案提纲。

要求：
1. 使用数字编号格式（1. 1.1 1.1.1）
2. 层次清晰，逻辑合理
3. 覆盖所有技术需求点
4. 避免通用性章节
5. 突出IPTV专业特色

输出格式示例：
1. 系统总体设计
1.1 设计原则
1.2 总体架构
2. 核心功能设计
2.1 内容管理系统
2.1.1 内容采集
2.1.2 内容处理""",
                "differentiation_prompt": """请对以下技术方案内容进行差异化改写：

要求：
1. 保持原意和技术准确性
2. 改变表述方式和句式结构
3. 使用同义词替换
4. 调整段落组织方式
5. 差异化程度30-40%
6. 保持专业性"""
            },
            "workflow": {
                "enable_concurrent_generation": True,
                "max_concurrent_tasks": 5,
                "enable_vector_retrieval": True,
                "chunk_size": 2000,
                "enable_differentiation": True
            },
            "formatting": {
                "auto_numbering": True,
                "include_toc": True,
                "page_break_after_toc": True,
                "center_title": True,
                "process_diagrams": True,
                "style_mapping": {
                    "1": "标书1级",
                    "2": "标书2级",
                    "3": "标书3级",
                    "4": "标书4级",
                    "5": "标书5级",
                    "content": "标书正文",
                    "title": "标书1级"
                }
            },
            "providers": {
                "default": "deepseek",
                "available": {
                    "deepseek": {
                        "type": "deepseek",
                        "model_name": "deepseek-chat",
                        "api_key": "",
                        "base_url": ""
                    },
                    "openai": {
                        "type": "openai", 
                        "model_name": "gpt-3.5-turbo",
                        "api_key": "",
                        "base_url": ""
                    },
                    "gemini": {
                        "type": "openai",  # 使用OpenAI兼容接口
                        "model_name": "gemini-pro-2.5",
                        "api_key": "",
                        "base_url": "https://api.monica.im/v1"  # Monica平台示例
                    }
                }
            }
        }
        
        # 加载配置
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """加载配置"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                
                # 合并默认配置和加载的配置
                config = self._deep_merge(self.default_config.copy(), loaded_config)
                logger.info("配置加载成功")
                return config
            else:
                logger.info("配置文件不存在，使用默认配置")
                return self.default_config.copy()
        except Exception as e:
            logger.error(f"加载配置失败: {e}，使用默认配置")
            return self.default_config.copy()
    
    def _save_config(self):
        """保存配置"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
            logger.info("配置保存成功")
        except Exception as e:
            logger.error(f"保存配置失败: {e}")
    
    def _deep_merge(self, base: Dict, update: Dict) -> Dict:
        """深度合并字典"""
        for key, value in update.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                base[key] = self._deep_merge(base[key], value)
            else:
                base[key] = value
        return base
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """获取配置值（支持点号路径）"""
        try:
            keys = key_path.split('.')
            value = self.config
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key_path: str, value: Any, save: bool = True):
        """设置配置值（支持点号路径）"""
        try:
            keys = key_path.split('.')
            config = self.config
            
            # 导航到目标位置
            for key in keys[:-1]:
                if key not in config:
                    config[key] = {}
                config = config[key]
            
            # 设置值
            config[keys[-1]] = value
            
            if save:
                self._save_config()
            
            logger.info(f"配置已更新: {key_path} = {value}")
        except Exception as e:
            logger.error(f"设置配置失败: {e}")
    
    def update(self, updates: Dict[str, Any], save: bool = True):
        """批量更新配置"""
        try:
            for key_path, value in updates.items():
                self.set(key_path, value, save=False)
            
            if save:
                self._save_config()
            
            logger.info(f"批量配置更新完成: {list(updates.keys())}")
        except Exception as e:
            logger.error(f"批量更新配置失败: {e}")
    
    def get_llm_config(self) -> Dict[str, Any]:
        """获取LLM配置"""
        return self.get("llm", {})
    
    def get_prompt(self, prompt_key: str, default: str = "") -> str:
        """获取Prompt配置"""
        return self.get(f"prompts.{prompt_key}", default)
    
    def set_prompt(self, prompt_key: str, prompt_value: str):
        """设置Prompt配置"""
        self.set(f"prompts.{prompt_key}", prompt_value)
    
    def get_workflow_config(self) -> Dict[str, Any]:
        """获取工作流配置"""
        return self.get("workflow", {})
    
    def get_formatting_config(self) -> Dict[str, Any]:
        """获取格式化配置"""
        return self.get("formatting", {})
    
    def get_provider_config(self, provider_name: str = None) -> Dict[str, Any]:
        """获取Provider配置"""
        if provider_name:
            return self.get(f"providers.available.{provider_name}", {})
        else:
            return self.get("providers", {})
    
    def add_provider(self, name: str, config: Dict[str, Any]):
        """添加新的Provider配置"""
        self.set(f"providers.available.{name}", config)
    
    def set_default_provider(self, provider_name: str):
        """设置默认Provider"""
        if provider_name in self.get("providers.available", {}):
            self.set("providers.default", provider_name)
        else:
            raise ValueError(f"Provider不存在: {provider_name}")
    
    def export_config(self, file_path: str = None) -> str:
        """导出配置"""
        if not file_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_path = f"config/config_backup_{timestamp}.json"
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
            logger.info(f"配置导出成功: {file_path}")
            return file_path
        except Exception as e:
            logger.error(f"导出配置失败: {e}")
            raise
    
    def import_config(self, file_path: str):
        """导入配置"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                imported_config = json.load(f)
            
            self.config = self._deep_merge(self.default_config.copy(), imported_config)
            self._save_config()
            logger.info(f"配置导入成功: {file_path}")
        except Exception as e:
            logger.error(f"导入配置失败: {e}")
            raise
    
    def reset_to_default(self):
        """重置为默认配置"""
        self.config = self.default_config.copy()
        self._save_config()
        logger.info("配置已重置为默认值")
    
    def get_all_config(self) -> Dict[str, Any]:
        """获取所有配置"""
        return self.config.copy()


# 全局实例
config_manager = ConfigManager()
