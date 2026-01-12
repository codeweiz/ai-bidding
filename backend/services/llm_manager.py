"""
LLM管理器 - 支持多Provider和动态配置
"""
import logging
from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod
import asyncio
import re

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_deepseek import ChatDeepSeek

from backend.core.toml_config import toml_config

# 可选依赖的延迟导入
try:
    from langchain_openai import ChatOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    from langchain_anthropic import ChatAnthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

logger = logging.getLogger(__name__)


class LLMProvider(ABC):
    """LLM Provider抽象基类"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.client = None
        self._initialize_client()
    
    @abstractmethod
    def _initialize_client(self):
        """初始化LLM客户端"""
        pass
    
    @abstractmethod
    async def generate(self, messages: List[Any], **kwargs) -> Dict[str, Any]:
        """生成内容"""
        pass


class DeepSeekProvider(LLMProvider):
    """DeepSeek Provider"""
    
    def _initialize_client(self):
        self.client = ChatDeepSeek(
            model=self.config.get("model_name", "deepseek-chat"),
            api_key=self.config.get("api_key"),
            temperature=self.config.get("temperature", 0.2),
            max_tokens=self.config.get("max_tokens", 4000),
        )
    
    async def generate(self, messages: List[Any], **kwargs) -> Dict[str, Any]:
        try:
            response = await self.client.ainvoke(messages)
            return {
                "content": response.content,
                "status": "success"
            }
        except Exception as e:
            logger.error(f"DeepSeek生成失败: {e}")
            return {
                "content": "",
                "status": "error",
                "error": str(e)
            }


class OpenAIProvider(LLMProvider):
    """OpenAI Provider"""

    def _initialize_client(self):
        if not OPENAI_AVAILABLE:
            raise ImportError("langchain_openai not available. Install with: pip install langchain-openai")

        self.client = ChatOpenAI(
            model=self.config.get("model_name", "gpt-3.5-turbo"),
            api_key=self.config.get("api_key"),
            temperature=self.config.get("temperature", 0.2),
            max_tokens=self.config.get("max_tokens", 4000),
            base_url=self.config.get("base_url"),
        )
    
    async def generate(self, messages: List[Any], **kwargs) -> Dict[str, Any]:
        try:
            response = await self.client.ainvoke(messages)
            return {
                "content": response.content,
                "status": "success"
            }
        except Exception as e:
            logger.error(f"OpenAI生成失败: {e}")
            return {
                "content": "",
                "status": "error",
                "error": str(e)
            }


class AnthropicProvider(LLMProvider):
    """Anthropic Provider"""

    def _initialize_client(self):
        if not ANTHROPIC_AVAILABLE:
            raise ImportError("langchain_anthropic not available. Install with: pip install langchain-anthropic")

        self.client = ChatAnthropic(
            model=self.config.get("model_name", "claude-3-sonnet-20240229"),
            api_key=self.config.get("api_key"),
            temperature=self.config.get("temperature", 0.2),
            max_tokens=self.config.get("max_tokens", 4000),
        )
    
    async def generate(self, messages: List[Any], **kwargs) -> Dict[str, Any]:
        try:
            response = await self.client.ainvoke(messages)
            return {
                "content": response.content,
                "status": "success"
            }
        except Exception as e:
            logger.error(f"Anthropic生成失败: {e}")
            return {
                "content": "",
                "status": "error",
                "error": str(e)
            }


class LLMManager:
    """LLM管理器 - 支持多Provider和动态配置"""
    
    def __init__(self):
        self.providers = {}
        self.current_provider = None
        self.retry_config = {
            "max_retries": 3,
            "retry_delay": 1.0,
            "enable_format_validation": True
        }
        self.dynamic_config = {
            "temperature": 0.2,
            "max_tokens": 4000,
            "custom_prompts": {}
        }
        self._initialize_providers()
    
    def _initialize_providers(self):
        """初始化所有Provider"""
        # DeepSeek
        deepseek_config = {
            "model_name": toml_config.llm.model_name,
            "api_key": toml_config.llm.api_key,
            "temperature": self.dynamic_config["temperature"],
            "max_tokens": self.dynamic_config["max_tokens"],
            "base_url": toml_config.llm.base_url
        }
        self.providers["openai"] = OpenAIProvider(deepseek_config)
        self.providers["deepseek"] = DeepSeekProvider(deepseek_config)
        
        # 设置默认Provider
        self.current_provider = toml_config.llm.provider
    
    def add_provider(self, name: str, provider_type: str, config: Dict[str, Any]):
        """动态添加Provider"""
        try:
            config.update({
                "temperature": self.dynamic_config["temperature"],
                "max_tokens": self.dynamic_config["max_tokens"]
            })

            if provider_type == "openai":
                if not OPENAI_AVAILABLE:
                    raise ImportError("OpenAI provider not available. Install with: pip install langchain-openai")
                self.providers[name] = OpenAIProvider(config)
            elif provider_type == "anthropic":
                if not ANTHROPIC_AVAILABLE:
                    raise ImportError("Anthropic provider not available. Install with: pip install langchain-anthropic")
                self.providers[name] = AnthropicProvider(config)
            elif provider_type == "deepseek":
                self.providers[name] = DeepSeekProvider(config)
            else:
                raise ValueError(f"不支持的Provider类型: {provider_type}")

            logger.info(f"成功添加Provider: {name}")
            return True
        except Exception as e:
            logger.error(f"添加Provider失败: {e}")
            return False
    
    def switch_provider(self, provider_name: str) -> bool:
        """切换Provider"""
        if provider_name in self.providers:
            self.current_provider = provider_name
            logger.info(f"切换到Provider: {provider_name}")
            return True
        else:
            logger.error(f"Provider不存在: {provider_name}")
            return False
    
    def update_config(self, config: Dict[str, Any]):
        """更新动态配置"""
        self.dynamic_config.update(config)
        
        # 更新所有Provider的配置
        for provider in self.providers.values():
            if hasattr(provider, 'client'):
                if hasattr(provider.client, 'temperature'):
                    provider.client.temperature = self.dynamic_config.get("temperature", 0.2)
                if hasattr(provider.client, 'max_tokens'):
                    provider.client.max_tokens = self.dynamic_config.get("max_tokens", 4000)
        
        logger.info(f"配置已更新: {config}")
    
    def get_custom_prompt(self, prompt_key: str, default: str = "") -> str:
        """获取自定义Prompt"""
        return self.dynamic_config["custom_prompts"].get(prompt_key, default)
    
    def set_custom_prompt(self, prompt_key: str, prompt_value: str):
        """设置自定义Prompt"""
        self.dynamic_config["custom_prompts"][prompt_key] = prompt_value
        logger.info(f"设置自定义Prompt: {prompt_key}")
    
    async def generate_with_retry(self, messages: List[Any], **kwargs) -> Dict[str, Any]:
        """带重试机制的生成"""
        max_retries = self.retry_config["max_retries"]
        retry_delay = self.retry_config["retry_delay"]
        
        for attempt in range(max_retries):
            try:
                provider = self.providers[self.current_provider]
                result = await provider.generate(messages, **kwargs)
                
                if result["status"] == "success":
                    # 格式验证
                    if self.retry_config["enable_format_validation"]:
                        if self._validate_format(result["content"]):
                            return result
                        else:
                            logger.warning(f"格式验证失败，重试 {attempt + 1}/{max_retries}")
                            if attempt < max_retries - 1:
                                await asyncio.sleep(retry_delay)
                                continue
                    else:
                        return result
                else:
                    logger.warning(f"生成失败，重试 {attempt + 1}/{max_retries}: {result.get('error')}")
                    if attempt < max_retries - 1:
                        await asyncio.sleep(retry_delay)
                        continue
                        
            except Exception as e:
                logger.error(f"生成异常，重试 {attempt + 1}/{max_retries}: {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay)
                    continue
        
        return {
            "content": "",
            "status": "error",
            "error": f"重试{max_retries}次后仍然失败"
        }
    
    def _validate_format(self, content: str) -> bool:
        """验证内容格式"""
        try:
            # 检查是否包含markdown格式（如果不希望）
            if "```" in content and "markdown" in content.lower():
                logger.warning("检测到markdown格式，可能需要重新生成")
                return False
            
            # 检查内容长度
            if len(content.strip()) < 100:
                logger.warning("内容过短，可能生成不完整")
                return False
            
            return True
        except Exception as e:
            logger.error(f"格式验证异常: {e}")
            return True  # 验证失败时默认通过


# 全局实例
llm_manager = LLMManager()
