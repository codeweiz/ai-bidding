import logging
from typing import Dict, Any

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_deepseek import ChatDeepSeek

from backend.core.toml_config import toml_config

logger = logging.getLogger(__name__)


class LLMService:
    """LLM服务类，负责与AI模型交互"""

    def __init__(self):
        self.llm = ChatDeepSeek(
            model=toml_config.llm.model_name,
            api_key=toml_config.llm.api_key,
            temperature=0.7,
            max_tokens=4000,
        )

    async def analyze_requirements(self, document_content: str) -> Dict[str, Any]:
        """分析招标文档需求"""
        system_prompt = """
        你是一位资深的投标专家，精通招投标业务。请分析以下招标文档，提取关键需求信息。
        请按照以下结构输出分析结果：
        1. 技术需求：列出所有技术要求和规格
        2. 功能需求：列出系统功能要求
        3. 性能指标：列出性能相关要求
        4. 资质要求：列出投标人资质要求
        5. 评分标准：列出评分标准和权重
        6. 关键风险点：标记可能的风险点
        
        请确保：
        - 不遗漏任何强制性要求
        - 准确理解技术术语
        - 标记重要程度（高/中/低）
        """

        user_prompt = f"请分析以下招标文档内容：\n\n{document_content}"

        try:
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ]

            response = await self.llm.ainvoke(messages)

            return {
                "analysis": response.content,
                "status": "success"
            }
        except Exception as e:
            logger.error(f"需求分析失败: {e}")
            return {
                "analysis": "",
                "status": "error",
                "error": str(e)
            }

    async def generate_outline(self, requirements: str) -> Dict[str, Any]:
        """基于需求生成方案提纲"""
        system_prompt = """
        你是一位资深的技术方案编写专家。请根据招标需求分析结果，生成一份完整的技术方案提纲。
        提纲要求：
        1. 章节结构清晰，逻辑合理
        2. 确保覆盖所有需求点
        3. 符合投标文件规范
        4. 包含必要的技术架构、实施方案、保障措施等章节
        
        请按照以下格式输出：
        # 技术方案提纲
        
        ## 1. 项目概述
        ### 1.1 项目背景
        ### 1.2 建设目标
        ...
        
        ## 2. 需求分析
        ### 2.1 业务需求分析
        ### 2.2 技术需求分析
        ...
        
        请确保每个章节都有明确的目的和内容要点。
        """

        user_prompt = f"请基于以下需求分析结果生成技术方案提纲：\n\n{requirements}"

        try:
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ]

            response = await self.llm.ainvoke(messages)

            return {
                "outline": response.content,
                "status": "success"
            }
        except Exception as e:
            logger.error(f"提纲生成失败: {e}")
            return {
                "outline": "",
                "status": "error",
                "error": str(e)
            }

    async def generate_content(self, section_title: str, section_requirements: str,
                               context: str = "") -> Dict[str, Any]:
        """生成章节内容"""
        system_prompt = """
        你是一位资深的技术方案编写专家，精通各类技术领域。请根据章节标题和需求，生成专业的技术方案内容。
        内容要求：
        1. 专业性强，术语使用准确
        2. 逻辑清晰，结构合理
        3. 针对性强，紧扣需求
        4. 可操作性强，具有实施价值
        5. 字数适中，一般1000-2000字
        
        请确保：
        - 引用具体的需求进行响应
        - 避免空洞的表述
        - 包含必要的技术细节
        - 保持内容的原创性
        """

        user_prompt = f"""
        请为以下章节生成内容：

        章节标题：{section_title}
        
        相关需求：
        {section_requirements}
        
        上下文信息：
        {context}
        
        请生成专业的技术方案内容。
        """

        try:
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ]

            response = await self.llm.ainvoke(messages)

            return {
                "content": response.content,
                "status": "success"
            }
        except Exception as e:
            logger.error(f"内容生成失败: {e}")
            return {
                "content": "",
                "status": "error",
                "error": str(e)
            }

    async def differentiate_content(self, original_content: str) -> Dict[str, Any]:
        """对内容进行差异化处理"""
        system_prompt = """
        你是一位专业的文档编辑专家。请对以下技术方案内容进行差异化改写，确保：

        1. 保持原意不变
        2. 改变表述方式和句式结构
        3. 使用同义词替换
        4. 调整段落组织方式
        5. 保持专业性和逻辑性
        6. 差异化程度控制在30-40%
        
        改写要求：
        - 不能改变技术方案的核心内容
        - 保持专业术语的准确性
        - 确保改写后内容仍然符合投标要求
        - 避免产生歧义或错误理解
        """

        user_prompt = f"请对以下内容进行差异化改写：\n\n{original_content}"

        try:
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ]

            response = await self.llm.ainvoke(messages)

            return {
                "differentiated_content": response.content,
                "status": "success"
            }
        except Exception as e:
            logger.error(f"差异化处理失败: {e}")
            return {
                "differentiated_content": original_content,
                "status": "error",
                "error": str(e)
            }


# 全局实例
llm_service = LLMService()
