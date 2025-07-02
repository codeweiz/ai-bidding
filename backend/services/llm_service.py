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
        你是一位资深的投标专家，精通招投标业务和技术方案编写。请深度分析以下招标文档，提取关键需求信息。

        **分析重点：**
        1. 仔细识别所有标记为"★"的强制性条款（实质性要求）
        2. 重点关注标记为"▲"的重要技术参数
        3. 深度理解项目背景、建设目标和业务需求
        4. 准确提取技术架构、性能指标、安全要求
        5. 详细分析评分标准和权重分配

        **输出结构：**
        ## 1. 项目基本信息
        - 项目名称、招标人、预算、交付期等

        ## 2. 强制性要求（★条款）
        - 逐条列出所有★标记的实质性要求
        - 标注违反后果（如废标处理）

        ## 3. 重要技术参数（▲条款）
        - 详细列出所有▲标记的技术参数
        - 分析对评分的影响

        ## 4. 核心技术需求
        - 系统架构要求
        - 功能模块需求
        - 技术标准和规范
        - 接口和集成要求

        ## 5. 性能与安全指标
        - 性能指标（用户数、并发数、响应时间等）
        - 安全要求（等保级别、加密要求等）
        - 可用性和可靠性要求

        ## 6. 评分标准分析
        - 技术评分标准和权重
        - 商务评分标准和权重
        - 价格评分方法
        - 关键得分点分析

        ## 7. 交付和服务要求
        - 交付物清单和格式要求
        - 售后服务和质保要求
        - 培训和技术支持要求

        ## 8. 风险点识别
        - 技术实现风险
        - 合规性风险
        - 商务风险
        - 建议应对策略

        **分析要求：**
        - 确保不遗漏任何强制性要求
        - 准确理解专业技术术语
        - 深度分析评分标准的得分策略
        - 识别潜在的技术难点和风险
        - 为后续技术方案编写提供精准指导
        """

        user_prompt = f"""请深度分析以下招标文档，按照上述结构提供详细的需求分析：

{document_content}

请特别注意：
1. 仔细查找并标记所有"★"和"▲"符号标记的条款
2. 深度理解项目的技术背景和业务场景
3. 准确提取评分标准，为投标策略提供依据
4. 识别可能的技术实现难点和风险点"""

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
        你是一位资深的技术方案架构师和投标专家。请根据招标需求分析结果，生成一份专业、完整的投标技术方案提纲。

        **提纲设计原则：**
        1. 严格对应招标文件的所有要求，确保100%覆盖
        2. 突出技术优势和创新点，提升竞争力
        3. 逻辑清晰，层次分明，符合投标文件规范
        4. 针对评分标准进行章节优化布局
        5. 体现专业性和可操作性

        **标准投标技术方案结构：**

        # 投标技术方案

        ## 1. 项目概述
        ### 1.1 项目背景与理解
        ### 1.2 建设目标与意义
        ### 1.3 招标内容理解与范围确认
        ### 1.4 投标响应承诺

        ## 2. 总体设计思路与技术架构
        ### 2.1 设计原则与理念
        ### 2.2 总体系统架构设计
        ### 2.3 技术路线选型
        ### 2.4 关键技术方案

        ## 3. 详细技术方案设计
        ### 3.1 [根据具体需求定制章节]
        ### 3.2 [核心功能模块设计]
        ### 3.3 [系统集成方案]
        ### 3.4 [数据处理方案]

        ## 4. 系统安全设计
        ### 4.1 安全体系架构
        ### 4.2 安全防护措施
        ### 4.3 等保合规设计
        ### 4.4 数据安全保障

        ## 5. 系统性能与可靠性设计
        ### 5.1 性能指标保障
        ### 5.2 高可用性设计
        ### 5.3 容灾备份方案
        ### 5.4 性能优化策略

        ## 6. 项目实施与管理
        ### 6.1 项目组织架构
        ### 6.2 实施计划与里程碑
        ### 6.3 质量保障措施
        ### 6.4 风险管控方案

        ## 7. 测试与验收方案
        ### 7.1 测试策略与计划
        ### 7.2 验收标准与流程
        ### 7.3 试运行方案
        ### 7.4 上线部署方案

        ## 8. 运维与售后服务
        ### 8.1 运维服务体系
        ### 8.2 技术支持方案
        ### 8.3 培训服务计划
        ### 8.4 质保与维护承诺

        ## 9. 项目保障措施
        ### 9.1 技术保障
        ### 9.2 人员保障
        ### 9.3 资源保障
        ### 9.4 进度保障

        **提纲优化要求：**
        - 根据具体项目需求调整章节内容和重点
        - 确保每个章节都能响应相应的评分标准
        - 突出技术创新点和差异化优势
        - 体现对招标方业务的深度理解
        - 展现完整的解决方案能力
        """

        user_prompt = f"""请基于以下需求分析结果，生成专业的投标技术方案提纲：

{requirements}

**特别要求：**
1. 根据需求分析中的具体技术要求，调整和细化相关章节
2. 确保所有强制性要求（★条款）都有对应的响应章节
3. 针对重要技术参数（▲条款）设计专门的技术方案章节
4. 考虑评分标准，优化章节布局以最大化得分潜力
5. 体现对项目背景和业务场景的深度理解

请生成详细的章节提纲，包含每个章节的主要内容要点。"""

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
        你是一位资深的技术方案编写专家，精通软件开发、系统架构、项目管理等多个技术领域。请根据章节标题和需求，生成高质量的投标技术方案内容。

        **内容编写原则：**
        1. **专业性**：使用准确的技术术语，体现深厚的专业功底
        2. **针对性**：精准响应招标需求，避免泛泛而谈
        3. **可操作性**：提供具体的实施方案和技术路径
        4. **创新性**：体现技术优势和创新点，提升竞争力
        5. **完整性**：内容完整，逻辑清晰，结构合理

        **内容结构要求：**
        - 开篇简要说明本章节的目标和重要性
        - 主体部分详细阐述技术方案和实施策略
        - 结尾总结关键要点和预期效果
        - 适当使用小标题组织内容结构

        **技术深度要求：**
        - 提供具体的技术架构和设计方案
        - 包含关键技术选型的理由和优势
        - 详细说明实施步骤和关键节点
        - 分析可能的技术风险和应对措施

        **响应策略：**
        - 明确响应招标文件中的具体要求
        - 突出我方的技术优势和成功经验
        - 体现对招标方业务场景的深度理解
        - 展现完整的问题解决能力

        **格式要求：**
        - 使用Markdown格式组织内容
        - 适当使用列表、表格等形式提升可读性
        - 重要信息使用加粗或其他格式突出
        - 保持专业的文档风格

        **字数要求：**
        - 根据章节重要性控制篇幅，一般1500-3000字
        - 核心技术章节可适当增加篇幅
        - 确保内容充实，避免冗余
        """

        user_prompt = f"""
        请为以下章节生成高质量的技术方案内容：

        **章节标题：** {section_title}

        **相关需求：**
        {section_requirements}

        **项目背景和上下文：**
        {context}

        **特别要求：**
        1. 请根据章节标题的特点，采用相应的编写策略
        2. 确保内容与招标需求高度匹配
        3. 体现专业的技术水平和丰富的项目经验
        4. 突出我方的技术优势和创新能力
        5. 提供具体可行的实施方案

        请生成专业、详细的技术方案内容。
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

    async def differentiate_content(self, original_content: str, section_title: str = "") -> Dict[str, Any]:
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
                "content": response.content,  # 修改为content以保持一致性
                "status": "success"
            }
        except Exception as e:
            logger.error(f"差异化处理失败: {e}")
            return {
                "content": original_content,
                "status": "error",
                "error": str(e)
            }

    async def _call_llm_with_prompt(self, prompt: str) -> str:
        """通用的LLM调用方法"""
        try:
            messages = [HumanMessage(content=prompt)]
            response = await self.llm.ainvoke(messages)
            return response.content
        except Exception as e:
            logger.error(f"LLM调用失败: {e}")
            raise


# 全局实例
llm_service = LLMService()
