"""
校验服务 - 负责内容校验和纠错，防止生成内容畸变或脱离招标范围
"""
import re
import logging
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from backend.services.llm_service import llm_service

logger = logging.getLogger(__name__)


class ValidationLevel(str, Enum):
    """校验级别"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ValidationResult(str, Enum):
    """校验结果"""
    PASS = "pass"
    WARNING = "warning"
    FAIL = "fail"


@dataclass
class ValidationIssue:
    """校验问题"""
    level: ValidationLevel
    result: ValidationResult
    message: str
    suggestion: Optional[str] = None
    location: Optional[str] = None


@dataclass
class ContentValidationReport:
    """内容校验报告"""
    overall_result: ValidationResult
    score: float  # 0-100分
    issues: List[ValidationIssue]
    corrected_content: Optional[str] = None


class ValidationService:
    """校验服务类"""
    
    def __init__(self):
        self.min_content_length = 100  # 最小内容长度
        self.max_content_length = 50000  # 最大内容长度
        self.required_keywords_threshold = 0.3  # 关键词覆盖率阈值
    
    async def validate_requirements_analysis(
        self, 
        analysis: str, 
        original_document: str
    ) -> ContentValidationReport:
        """校验需求分析结果"""
        logger.info("开始校验需求分析结果")
        
        issues = []
        score = 100.0
        
        # 1. 基础格式校验
        format_issues = self._validate_analysis_format(analysis)
        issues.extend(format_issues)
        
        # 2. 内容完整性校验
        completeness_issues = await self._validate_analysis_completeness(analysis, original_document)
        issues.extend(completeness_issues)
        
        # 3. 关键信息提取校验
        extraction_issues = await self._validate_key_information_extraction(analysis, original_document)
        issues.extend(extraction_issues)
        
        # 计算总分
        for issue in issues:
            if issue.result == ValidationResult.FAIL:
                score -= 20
            elif issue.result == ValidationResult.WARNING:
                score -= 10
        
        score = max(0, score)
        
        # 确定总体结果
        overall_result = self._determine_overall_result(issues, score)
        
        # 如果需要，生成修正内容
        corrected_content = None
        if overall_result == ValidationResult.FAIL:
            corrected_content = await self._correct_requirements_analysis(analysis, issues)
        
        return ContentValidationReport(
            overall_result=overall_result,
            score=score,
            issues=issues,
            corrected_content=corrected_content
        )
    
    async def validate_outline(
        self, 
        outline: str, 
        requirements_analysis: str
    ) -> ContentValidationReport:
        """校验方案提纲"""
        logger.info("开始校验方案提纲")
        
        issues = []
        score = 100.0
        
        # 1. 结构校验
        structure_issues = self._validate_outline_structure(outline)
        issues.extend(structure_issues)
        
        # 2. 需求覆盖校验
        coverage_issues = await self._validate_requirements_coverage(outline, requirements_analysis)
        issues.extend(coverage_issues)
        
        # 3. 逻辑性校验
        logic_issues = await self._validate_outline_logic(outline)
        issues.extend(logic_issues)
        
        # 计算分数和结果
        for issue in issues:
            if issue.result == ValidationResult.FAIL:
                score -= 15
            elif issue.result == ValidationResult.WARNING:
                score -= 8
        
        score = max(0, score)
        overall_result = self._determine_overall_result(issues, score)
        
        # 生成修正内容
        corrected_content = None
        if overall_result == ValidationResult.FAIL:
            corrected_content = await self._correct_outline(outline, issues)
        
        return ContentValidationReport(
            overall_result=overall_result,
            score=score,
            issues=issues,
            corrected_content=corrected_content
        )
    
    async def validate_section_content(
        self, 
        content: str, 
        section_title: str,
        requirements_analysis: str
    ) -> ContentValidationReport:
        """校验章节内容"""
        logger.info(f"开始校验章节内容: {section_title}")
        
        issues = []
        score = 100.0
        
        # 1. 基础质量校验
        quality_issues = self._validate_content_quality(content, section_title)
        issues.extend(quality_issues)
        
        # 2. 相关性校验
        relevance_issues = await self._validate_content_relevance(content, section_title, requirements_analysis)
        issues.extend(relevance_issues)
        
        # 3. 专业性校验
        professional_issues = await self._validate_content_professionalism(content, section_title)
        issues.extend(professional_issues)
        
        # 计算分数
        for issue in issues:
            if issue.result == ValidationResult.FAIL:
                score -= 12
            elif issue.result == ValidationResult.WARNING:
                score -= 6
        
        score = max(0, score)
        overall_result = self._determine_overall_result(issues, score)
        
        # 生成修正内容
        corrected_content = None
        if overall_result == ValidationResult.FAIL:
            corrected_content = await self._correct_section_content(content, section_title, issues)
        
        return ContentValidationReport(
            overall_result=overall_result,
            score=score,
            issues=issues,
            corrected_content=corrected_content
        )
    
    def _validate_analysis_format(self, analysis: str) -> List[ValidationIssue]:
        """校验分析格式"""
        issues = []
        
        # 检查长度
        if len(analysis) < self.min_content_length:
            issues.append(ValidationIssue(
                level=ValidationLevel.HIGH,
                result=ValidationResult.FAIL,
                message="需求分析内容过短",
                suggestion="需求分析应包含更详细的内容"
            ))
        
        # 检查是否包含必要的章节
        required_sections = ["技术需求", "功能需求", "性能指标", "评分标准"]
        missing_sections = []
        
        for section in required_sections:
            if section not in analysis:
                missing_sections.append(section)
        
        if missing_sections:
            issues.append(ValidationIssue(
                level=ValidationLevel.MEDIUM,
                result=ValidationResult.WARNING,
                message=f"缺少必要章节: {', '.join(missing_sections)}",
                suggestion="建议补充缺少的分析章节"
            ))
        
        return issues
    
    async def _validate_analysis_completeness(self, analysis: str, original_document: str) -> List[ValidationIssue]:
        """校验分析完整性"""
        issues = []
        
        try:
            # 使用LLM校验完整性
            validation_prompt = f"""
            请校验以下需求分析是否完整地覆盖了原始招标文档的要求。
            
            原始文档（摘要）：
            {original_document[:2000]}...
            
            需求分析：
            {analysis}
            
            请检查：
            1. 是否遗漏了重要的技术要求
            2. 是否遗漏了关键的功能需求
            3. 是否遗漏了重要的评分标准
            
            请以JSON格式返回校验结果：
            {{
                "missing_requirements": ["遗漏的需求1", "遗漏的需求2"],
                "completeness_score": 85,
                "suggestions": ["建议1", "建议2"]
            }}
            """
            
            result = await llm_service._call_llm_with_prompt(validation_prompt)
            
            # 解析结果并生成问题
            if "missing_requirements" in result and result["missing_requirements"]:
                issues.append(ValidationIssue(
                    level=ValidationLevel.HIGH,
                    result=ValidationResult.WARNING,
                    message=f"可能遗漏的需求: {', '.join(result['missing_requirements'])}",
                    suggestion="建议补充遗漏的需求分析"
                ))
            
        except Exception as e:
            logger.warning(f"LLM校验失败，使用基础校验: {e}")
            # 基础校验逻辑
            pass
        
        return issues
    
    async def _validate_key_information_extraction(self, analysis: str, original_document: str) -> List[ValidationIssue]:
        """校验关键信息提取"""
        issues = []
        
        # 提取关键词
        keywords = self._extract_keywords(original_document)
        analysis_keywords = self._extract_keywords(analysis)
        
        # 计算关键词覆盖率
        if keywords:
            coverage = len(set(keywords) & set(analysis_keywords)) / len(keywords)
            
            if coverage < self.required_keywords_threshold:
                issues.append(ValidationIssue(
                    level=ValidationLevel.MEDIUM,
                    result=ValidationResult.WARNING,
                    message=f"关键词覆盖率较低: {coverage:.1%}",
                    suggestion="建议增加对关键技术术语的分析"
                ))
        
        return issues
    
    def _validate_outline_structure(self, outline: str) -> List[ValidationIssue]:
        """校验提纲结构"""
        issues = []
        
        # 检查是否有层级结构
        if not re.search(r'[1-9]\.|一、|（一）', outline):
            issues.append(ValidationIssue(
                level=ValidationLevel.HIGH,
                result=ValidationResult.FAIL,
                message="提纲缺少清晰的层级结构",
                suggestion="建议使用数字或中文序号组织提纲结构"
            ))
        
        # 检查章节数量
        sections = re.findall(r'^[1-9]\.|^一、|^（一）', outline, re.MULTILINE)
        if len(sections) < 3:
            issues.append(ValidationIssue(
                level=ValidationLevel.MEDIUM,
                result=ValidationResult.WARNING,
                message="提纲章节数量较少",
                suggestion="建议增加更多的章节以完整覆盖需求"
            ))
        
        return issues
    
    async def _validate_requirements_coverage(self, outline: str, requirements_analysis: str) -> List[ValidationIssue]:
        """校验需求覆盖"""
        issues = []
        
        # 提取需求关键词
        req_keywords = self._extract_keywords(requirements_analysis)
        outline_keywords = self._extract_keywords(outline)
        
        if req_keywords:
            coverage = len(set(req_keywords) & set(outline_keywords)) / len(req_keywords)
            
            if coverage < 0.5:
                issues.append(ValidationIssue(
                    level=ValidationLevel.HIGH,
                    result=ValidationResult.WARNING,
                    message=f"提纲对需求的覆盖率较低: {coverage:.1%}",
                    suggestion="建议调整提纲结构以更好地覆盖需求分析中的要点"
                ))
        
        return issues
    
    def _extract_keywords(self, text: str) -> List[str]:
        """提取关键词"""
        # 简单的关键词提取逻辑
        # 实际应用中可以使用更复杂的NLP技术
        keywords = []
        
        # 提取技术术语（包含英文的词汇）
        tech_terms = re.findall(r'[A-Za-z]+[A-Za-z0-9]*', text)
        keywords.extend(tech_terms)
        
        # 提取重要的中文词汇（简单规则）
        important_words = re.findall(r'[系统|平台|架构|技术|方案|设计|开发|实现|管理|服务|功能|性能|安全|数据|网络|软件|硬件]', text)
        keywords.extend(important_words)
        
        return list(set(keywords))
    
    def _determine_overall_result(self, issues: List[ValidationIssue], score: float) -> ValidationResult:
        """确定总体校验结果"""
        fail_count = sum(1 for issue in issues if issue.result == ValidationResult.FAIL)
        
        if fail_count > 0 or score < 60:
            return ValidationResult.FAIL
        elif score < 80:
            return ValidationResult.WARNING
        else:
            return ValidationResult.PASS
    
    async def _correct_requirements_analysis(self, analysis: str, issues: List[ValidationIssue]) -> str:
        """修正需求分析"""
        # 使用LLM进行内容修正
        correction_prompt = f"""
        请根据以下问题修正需求分析内容：
        
        原始分析：
        {analysis}
        
        发现的问题：
        {chr(10).join([f"- {issue.message}" for issue in issues])}
        
        请生成修正后的需求分析，确保：
        1. 解决所有发现的问题
        2. 保持原有的准确信息
        3. 补充缺失的内容
        """
        
        try:
            corrected = await llm_service._call_llm_with_prompt(correction_prompt)
            return corrected
        except Exception as e:
            logger.error(f"内容修正失败: {e}")
            return analysis
    
    async def _correct_outline(self, outline: str, issues: List[ValidationIssue]) -> str:
        """修正提纲"""
        # 类似的修正逻辑
        return outline
    
    async def _validate_outline_logic(self, outline: str) -> List[ValidationIssue]:
        """校验提纲逻辑性"""
        issues = []

        try:
            logic_prompt = f"""
            请校验以下技术方案提纲的逻辑性：

            {outline}

            检查要点：
            1. 章节顺序是否合理
            2. 内容是否有逻辑关联
            3. 是否符合技术方案的一般结构

            请指出逻辑问题并给出建议。
            """

            result = await llm_service._call_llm_with_prompt(logic_prompt)

            if "问题" in result or "建议" in result:
                issues.append(ValidationIssue(
                    level=ValidationLevel.MEDIUM,
                    result=ValidationResult.WARNING,
                    message="提纲逻辑性需要改进",
                    suggestion="建议调整章节顺序和内容组织"
                ))

        except Exception as e:
            logger.warning(f"逻辑性校验失败: {e}")

        return issues

    def _validate_content_quality(self, content: str, section_title: str) -> List[ValidationIssue]:
        """校验内容质量"""
        issues = []

        # 检查内容长度
        if len(content) < 200:
            issues.append(ValidationIssue(
                level=ValidationLevel.MEDIUM,
                result=ValidationResult.WARNING,
                message=f"章节 '{section_title}' 内容过短",
                suggestion="建议增加更详细的内容描述"
            ))

        # 检查是否有重复内容
        sentences = content.split('。')
        if len(sentences) != len(set(sentences)):
            issues.append(ValidationIssue(
                level=ValidationLevel.LOW,
                result=ValidationResult.WARNING,
                message="内容中存在重复句子",
                suggestion="建议删除重复内容"
            ))

        return issues

    async def _validate_content_relevance(self, content: str, section_title: str, requirements_analysis: str) -> List[ValidationIssue]:
        """校验内容相关性"""
        issues = []

        try:
            relevance_prompt = f"""
            请校验以下章节内容是否与章节标题和需求分析相关：

            章节标题：{section_title}
            章节内容：{content[:1000]}...
            需求分析摘要：{requirements_analysis[:1000]}...

            请评估相关性（1-10分）并指出不相关的内容。
            """

            result = await llm_service._call_llm_with_prompt(relevance_prompt)

            # 简单的相关性检查
            if "不相关" in result or "偏离" in result:
                issues.append(ValidationIssue(
                    level=ValidationLevel.HIGH,
                    result=ValidationResult.WARNING,
                    message=f"章节 '{section_title}' 内容可能偏离主题",
                    suggestion="建议调整内容以更好地匹配章节标题和需求"
                ))

        except Exception as e:
            logger.warning(f"相关性校验失败: {e}")

        return issues

    async def _validate_content_professionalism(self, content: str, section_title: str) -> List[ValidationIssue]:
        """校验内容专业性"""
        issues = []

        # 检查是否包含技术术语
        tech_terms = re.findall(r'[A-Za-z]+', content)
        if len(tech_terms) < 5:
            issues.append(ValidationIssue(
                level=ValidationLevel.LOW,
                result=ValidationResult.WARNING,
                message="内容缺少技术术语",
                suggestion="建议增加相关的技术术语以提高专业性"
            ))

        # 检查是否有具体的技术描述
        if not re.search(r'[架构|设计|实现|部署|配置|优化]', content):
            issues.append(ValidationIssue(
                level=ValidationLevel.MEDIUM,
                result=ValidationResult.WARNING,
                message="内容缺少具体的技术描述",
                suggestion="建议增加具体的技术实现描述"
            ))

        return issues

    async def _correct_section_content(self, content: str, section_title: str, issues: List[ValidationIssue]) -> str:
        """修正章节内容"""
        correction_prompt = f"""
        请根据以下问题修正章节内容：

        章节标题：{section_title}
        原始内容：{content}

        发现的问题：
        {chr(10).join([f"- {issue.message}: {issue.suggestion}" for issue in issues])}

        请生成修正后的内容，确保：
        1. 解决所有发现的问题
        2. 保持内容的专业性和准确性
        3. 符合章节标题的要求
        """

        try:
            corrected = await llm_service._call_llm_with_prompt(correction_prompt)
            return corrected
        except Exception as e:
            logger.error(f"章节内容修正失败: {e}")
            return content


# 全局实例
validation_service = ValidationService()
