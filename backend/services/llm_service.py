import logging
from typing import Dict, Any

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from backend.core.toml_config import toml_config
from backend.services.config_manager import config_manager
from backend.services.llm_manager import llm_manager

logger = logging.getLogger(__name__)


class LLMService:
    """LLM服务类，负责与AI模型交互 - 集成新的管理器"""

    def __init__(self):
        # 保持向后兼容的直接LLM实例
        self.llm = ChatOpenAI(
            model=toml_config.llm.model_name,
            api_key=toml_config.llm.api_key,
            base_url=toml_config.llm.base_url,
            temperature=config_manager.get("llm.temperature", 0.2),
            max_tokens=config_manager.get("llm.max_tokens", 4000),
        )

        # 集成新的LLM管理器
        self.llm_manager = llm_manager

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

    async def generate_iptv_outline(self, document_content: str) -> Dict[str, Any]:
        """生成IPTV领域的投标方案提纲 - 使用优化的prompt"""
        # 从配置管理器获取优化后的prompt
        system_prompt = config_manager.get_prompt("outline_generation_prompt", """
        请基于招标文档生成IPTV系统技术方案提纲。

        要求：
        1. 使用规范的数字编号格式（1. 1.1 1.1.1）
        2. 层次清晰，逻辑合理，深度不超过4级
        3. 全面覆盖招标文档中的技术需求点
        4. 避免通用性章节，突出项目特色
        5. 体现IPTV专业特色和技术创新
        6. 章节标题简洁明了，避免冗长表述

        输出格式示例：
        1. 项目概述
        1.1 项目背景
        1.2 建设目标
        1.3 建设依据
        2. 需求理解与分析
        2.1 功能需求分析
        2.2 性能需求分析
        2.3 安全需求分析
        3. 技术方案设计
        3.1 总体架构设计
        3.2 核心功能实现
        3.3 关键技术选型
        """)

        user_prompt = f"请基于以下招标文档生成IPTV技术方案提纲：\n\n{document_content}"

        try:
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ]

            # 使用新的LLM管理器生成（支持重试和格式验证）
            result = await self.llm_manager.generate_with_retry(messages)

            if result["status"] == "success":
                return {
                    "outline": result["content"],
                    "status": "success"
                }
            else:
                # 回退到直接调用
                response = await self.llm.ainvoke(messages)
                return {
                    "outline": response.content,
                    "status": "success"
                }
        except Exception as e:
            logger.error(f"IPTV提纲生成失败: {e}")
            return {
                "outline": "",
                "status": "error",
                "error": str(e)
            }

    async def generate_iptv_section_content(self, section_title: str, section_path: str,
                                          document_content: str) -> Dict[str, Any]:
        """生成IPTV领域的章节内容 - 使用优化的prompt"""
        # 从配置管理器获取优化后的prompt
        system_prompt = config_manager.get_prompt("iptv_expert_prompt", """
        你是一位资深的广电IPTV领域技术专家，具有15年以上的行业经验和丰富的投标方案编写经验。

        核心要求：
        1. 严格基于招标文档要求，紧扣具体需求点，避免泛泛而谈
        2. 使用行业专业术语，体现技术深度和专业水准
        3. 避免涉及具体技术栈名称（如Vue、Spring等），采用通用技术描述
        4. 避免输出售后、验收、质量保障等通用内容
        5. 内容要有针对性，体现对招标需求的深度理解
        6. 语言表达要简洁明了，逻辑清晰
        7. 字数控制在1000-1800字

        表达要求：
        - 使用"基于先进的前端框架"而非"基于Vue3.0"
        - 使用"采用微服务架构"而非"采用Spring Cloud"
        - 使用"分布式缓存技术"而非"Redis集群"
        - 重点描述技术方案的优势和创新点
        - 确保内容专业、准确、有说服力
        """)

        # 添加输出格式要求
        format_requirements = """
        输出格式要求（严格遵循）：
        - 严格输出纯文本格式，绝对不要使用markdown格式
        - 不要使用*号、#号、-号、```等任何markdown标记
        - 不要使用列表符号（如• - *）
        - 段落之间用空行分隔
        - 重点内容用数字编号或中文序号
        - 确保内容专业、准确、有深度
        """

        full_system_prompt = system_prompt + "\n\n" + format_requirements

        user_prompt = f"""
        请为以下章节生成专业的IPTV技术方案内容：

        章节标题：{section_title}
        章节路径：{section_path}

        招标文档完整内容：
        {document_content}

        请基于招标文档的具体要求，生成该章节的详细技术方案内容。
        要求：
        1. 内容专业详实，逻辑清晰
        2. 紧扣招标需求，体现技术实力
        3. 严格使用纯文本格式，不要任何markdown标记
        4. 确保内容阅读流畅，能够无缝融入完整投标方案
        """

        try:
            messages = [
                SystemMessage(content=full_system_prompt),
                HumanMessage(content=user_prompt)
            ]

            response = await self.llm.ainvoke(messages)

            return {
                "content": response.content,
                "status": "success"
            }
        except Exception as e:
            logger.error(f"IPTV章节内容生成失败: {e}")
            return {
                "content": "",
                "status": "error",
                "error": str(e)
            }

    async def generate_parent_summary(self, parent_title: str, parent_path: str,
                                    children_content: str, document_content: str) -> Dict[str, Any]:
        """生成父节点总结内容"""
        # 从配置管理器获取优化后的prompt
        system_prompt = config_manager.get_prompt("parent_summary_prompt", """
        你是一位资深的技术方案编写专家，精通广电IPTV领域。请为父级章节生成高质量的总结性内容。

        核心要求：
        1. 基于子章节内容进行高度概括和总结
        2. 体现章节间的逻辑关系和技术关联
        3. 突出技术方案的重点和创新亮点
        4. 确保内容承上启下，增强整体连贯性
        5. 避免简单重复子章节内容
        6. 语言简洁专业，逻辑清晰
        7. 字数控制在500-800字

        表达要求：
        - 使用总结性语言，如"综上所述"、"通过以上分析"
        - 突出技术方案的整体性和系统性
        - 体现对招标需求的深度理解和响应
        - 确保内容专业、准确、有说服力
        """)

        # 添加输出格式要求
        format_requirements = """
        输出格式要求（严格遵循）：
        - 严格输出纯文本格式，绝对不要使用markdown格式
        - 不要使用*号、#号、-号、```等任何markdown标记
        - 不要使用列表符号（如• - *）
        - 段落之间用空行分隔
        - 重点内容用数字编号或中文序号
        - 确保内容专业、准确、有深度
        """

        full_system_prompt = system_prompt + "\n\n" + format_requirements

        user_prompt = f"""
        请为以下父章节生成高质量的过渡性内容：

        父章节标题：{parent_title}
        章节路径：{parent_path}

        子章节详细内容：
        {children_content}

        招标文档要求：
        {document_content}

        请生成该父章节的总结性和过渡性内容，要求：
        1. 对子章节内容进行高质量总结
        2. 体现技术方案的整体性和逻辑性
        3. 突出技术亮点和竞争优势
        4. 确保与招标需求紧密结合
        5. 严格使用纯文本格式，保证阅读流畅
        """

        try:
            messages = [
                SystemMessage(content=full_system_prompt),
                HumanMessage(content=user_prompt)
            ]

            response = await self.llm.ainvoke(messages)

            return {
                "content": response.content,
                "status": "success"
            }
        except Exception as e:
            logger.error(f"父节点总结生成失败: {e}")
            return {
                "content": "",
                "status": "error",
                "error": str(e)
            }


# 全局实例
llm_service = LLMService()
