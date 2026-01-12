from pathlib import Path

import toml
from pydantic import BaseModel, Field

# 项目根目录
ROOT_DIR = Path(__file__).parent.parent.parent

# 加载环境变量
try:
    with open(ROOT_DIR / "config.toml") as f:
        _toml_config = toml.load(f)
except FileNotFoundError:
    _toml_config = {}


# LLM 配置
class LLMConfig(BaseModel):
    # LLM 提供商
    provider: str = Field(
        default=_toml_config.get("llm", {}).get("provider", "deepseek"),
        description="LLM 提供商"
    )

    # LLM 模型名
    model_name: str = Field(
        default=_toml_config.get("llm", {}).get("model_name", "deepseek-chat"),
        description="LLM 模型名称"
    )

    # LLM API Key
    api_key: str = Field(
        default=_toml_config.get("llm", {}).get("api_key", ""),
        description="LLM API Key"
    )

    # LLM Base URL
    base_url: str = Field(
        default=_toml_config.get("llm", {}).get("base_url", ""),
        description="LLM Base URL"
    )


# Embedding 配置
class EmbeddingConfig(BaseModel):
    # LLM 提供商
    provider: str = Field(
        default=_toml_config.get("embedding", {}).get("provider", "huggingface"),
        description="Embedding 提供商"
    )

    # LLM 模型名
    model_name: str = Field(
        default=_toml_config.get("embedding", {}).get("model_name", "sentence-transformers/all-mpnet-base-v2"),
        description="Embedding 模型名称"
    )


# LangSmith 配置
class LangSmithConfig(BaseModel):
    # LangSmith Tracing
    tracing: bool = Field(
        default=_toml_config.get("langsmith", {}).get("tracing", False),
        description="LangSmith Tracing"
    )

    # LangSmith Project
    project: str = Field(
        default=_toml_config.get("langsmith", {}).get("project", "default"),
        description="LangSmith Project"
    )

    # LangSmith API Key
    api_key: str = Field(
        default=_toml_config.get("langsmith", {}).get("api_key", ""),
        description="LangSmith API Key"
    )


# 应用配置
class TomlConfig(BaseModel):
    llm: LLMConfig = Field(default_factory=LLMConfig)
    embedding: EmbeddingConfig = Field(default_factory=EmbeddingConfig)
    langsmith: LangSmithConfig = Field(default_factory=LangSmithConfig)


# 全局配置实例
toml_config = TomlConfig()

# 设置 LangSmith 环境变量
if toml_config.langsmith.tracing:
    import os

    os.environ["LANGCHAIN_TRACING"] = "true"
    os.environ["LANGCHAIN_API_KEY"] = toml_config.langsmith.api_key
    os.environ["LANGCHAIN_PROJECT"] = toml_config.langsmith.project
