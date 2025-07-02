"""
增强的文档解析器 - 专门用于招标文档的结构化解析
"""
import re
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_unstructured import UnstructuredLoader

logger = logging.getLogger(__name__)


@dataclass
class RequirementClause:
    """需求条款"""
    clause_type: str  # "mandatory" (★), "important" (▲), "normal"
    content: str
    section: str
    importance: str  # "high", "medium", "low"


@dataclass
class ScoringCriteria:
    """评分标准"""
    category: str  # "technical", "commercial", "price"
    weight: float
    criteria: str
    max_score: float


@dataclass
class ProjectInfo:
    """项目基本信息"""
    name: str
    budget: Optional[str] = None
    deadline: Optional[str] = None
    client: Optional[str] = None
    project_id: Optional[str] = None


class EnhancedDocumentParser:
    """增强的文档解析器，专门用于招标文档分析"""
    
    def __init__(self, chunk_size: int = 3000, chunk_overlap: int = 300):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )
        
        # 招标文档关键词模式
        self.mandatory_patterns = [
            r'★.*?(?=\n|$)',  # ★号标记的强制性条款
            r'实质性.*?条款',
            r'强制性.*?要求',
            r'废标.*?条件'
        ]
        
        self.important_patterns = [
            r'▲.*?(?=\n|$)',  # ▲号标记的重要参数
            r'重要.*?参数',
            r'关键.*?指标'
        ]
        
        self.scoring_patterns = [
            r'评分.*?标准',
            r'技术.*?评分',
            r'商务.*?评分',
            r'价格.*?评分',
            r'权重.*?分配'
        ]

    def parse_tender_document(self, file_path: Path) -> Dict[str, Any]:
        """解析招标文档，提取结构化信息"""
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        try:
            # 基础文档解析
            loader = UnstructuredLoader(
                file_path=str(file_path),
                languages=["chi_sim", "eng"],
                separators=["\n\n", "\n", ".", "。", "!", "?", " "]
            )
            documents = loader.load()
            chunks = self.text_splitter.split_documents(documents)
            
            # 获取完整文本内容
            full_content = "\n".join([doc.page_content for doc in documents])
            
            # 结构化解析
            project_info = self._extract_project_info(full_content)
            mandatory_clauses = self._extract_mandatory_clauses(full_content)
            important_clauses = self._extract_important_clauses(full_content)
            scoring_criteria = self._extract_scoring_criteria(full_content)
            technical_requirements = self._extract_technical_requirements(full_content)
            
            return {
                "file_name": file_path.name,
                "file_type": file_path.suffix,
                "documents": documents,
                "chunks": chunks,
                "full_content": full_content,
                "structured_data": {
                    "project_info": project_info,
                    "mandatory_clauses": mandatory_clauses,
                    "important_clauses": important_clauses,
                    "scoring_criteria": scoring_criteria,
                    "technical_requirements": technical_requirements
                },
                "metadata": {
                    "total_pages": len(documents),
                    "total_chunks": len(chunks),
                    "mandatory_clauses_count": len(mandatory_clauses),
                    "important_clauses_count": len(important_clauses),
                    "scoring_criteria_count": len(scoring_criteria)
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to parse tender document: {e}")
            raise ValueError(f"Failed to parse document: {e}")

    def _extract_project_info(self, content: str) -> ProjectInfo:
        """提取项目基本信息"""
        project_info = ProjectInfo(name="未知项目")
        
        # 提取项目名称
        name_patterns = [
            r'项目名称[：:]\s*(.+?)(?=\n|招标)',
            r'(?:项目|工程).*?名称.*?[：:]\s*(.+?)(?=\n)',
            r'(\d{4}年.*?项目)'
        ]
        
        for pattern in name_patterns:
            match = re.search(pattern, content)
            if match:
                project_info.name = match.group(1).strip()
                break
        
        # 提取预算信息
        budget_patterns = [
            r'最高限价.*?[：:].*?(\d+.*?万?元)',
            r'预算.*?[：:].*?(\d+.*?万?元)',
            r'投资.*?总额.*?[：:].*?(\d+.*?万?元)'
        ]
        
        for pattern in budget_patterns:
            match = re.search(pattern, content)
            if match:
                project_info.budget = match.group(1).strip()
                break
        
        # 提取交付期限
        deadline_patterns = [
            r'交付期.*?[：:].*?(\d+.*?(?:个月|天|日))',
            r'工期.*?[：:].*?(\d+.*?(?:个月|天|日))',
            r'完成时间.*?[：:].*?(\d+.*?(?:个月|天|日))'
        ]
        
        for pattern in deadline_patterns:
            match = re.search(pattern, content)
            if match:
                project_info.deadline = match.group(1).strip()
                break
        
        # 提取招标人信息
        client_patterns = [
            r'招标人.*?[：:].*?(.+?)(?=\n|地址)',
            r'采购人.*?[：:].*?(.+?)(?=\n|地址)'
        ]
        
        for pattern in client_patterns:
            match = re.search(pattern, content)
            if match:
                project_info.client = match.group(1).strip()
                break
        
        return project_info

    def _extract_mandatory_clauses(self, content: str) -> List[RequirementClause]:
        """提取强制性条款（★标记）"""
        clauses = []
        
        for pattern in self.mandatory_patterns:
            matches = re.finditer(pattern, content, re.MULTILINE | re.DOTALL)
            for match in matches:
                clause_content = match.group(0).strip()
                if clause_content:
                    clauses.append(RequirementClause(
                        clause_type="mandatory",
                        content=clause_content,
                        section=self._find_section_context(content, match.start()),
                        importance="high"
                    ))
        
        return clauses

    def _extract_important_clauses(self, content: str) -> List[RequirementClause]:
        """提取重要条款（▲标记）"""
        clauses = []
        
        for pattern in self.important_patterns:
            matches = re.finditer(pattern, content, re.MULTILINE | re.DOTALL)
            for match in matches:
                clause_content = match.group(0).strip()
                if clause_content:
                    clauses.append(RequirementClause(
                        clause_type="important",
                        content=clause_content,
                        section=self._find_section_context(content, match.start()),
                        importance="medium"
                    ))
        
        return clauses

    def _extract_scoring_criteria(self, content: str) -> List[ScoringCriteria]:
        """提取评分标准"""
        criteria = []
        
        # 查找评分表格或评分标准部分
        scoring_section_pattern = r'评分.*?(?:标准|方法|细则).*?(?=\n\n|\n[一二三四五六七八九十]|\n\d+\.)'
        scoring_matches = re.finditer(scoring_section_pattern, content, re.MULTILINE | re.DOTALL)
        
        for match in scoring_matches:
            section_content = match.group(0)
            
            # 提取技术评分
            tech_pattern = r'技术.*?评分.*?(\d+).*?分'
            tech_match = re.search(tech_pattern, section_content)
            if tech_match:
                criteria.append(ScoringCriteria(
                    category="technical",
                    weight=float(tech_match.group(1)),
                    criteria="技术方案评分",
                    max_score=float(tech_match.group(1))
                ))
            
            # 提取商务评分
            commercial_pattern = r'商务.*?评分.*?(\d+).*?分'
            commercial_match = re.search(commercial_pattern, section_content)
            if commercial_match:
                criteria.append(ScoringCriteria(
                    category="commercial",
                    weight=float(commercial_match.group(1)),
                    criteria="商务方案评分",
                    max_score=float(commercial_match.group(1))
                ))
            
            # 提取价格评分
            price_pattern = r'价格.*?评分.*?(\d+).*?分'
            price_match = re.search(price_pattern, section_content)
            if price_match:
                criteria.append(ScoringCriteria(
                    category="price",
                    weight=float(price_match.group(1)),
                    criteria="价格评分",
                    max_score=float(price_match.group(1))
                ))
        
        return criteria

    def _extract_technical_requirements(self, content: str) -> Dict[str, List[str]]:
        """提取技术需求分类"""
        requirements = {
            "functional": [],
            "performance": [],
            "security": [],
            "compatibility": [],
            "delivery": []
        }
        
        # 功能需求
        functional_patterns = [
            r'功能.*?需求.*?[：:].*?(.+?)(?=\n\d+\.|\n[一二三四五六七八九十]|\n\n)',
            r'业务.*?需求.*?[：:].*?(.+?)(?=\n\d+\.|\n[一二三四五六七八九十]|\n\n)'
        ]
        
        # 性能需求
        performance_patterns = [
            r'性能.*?指标.*?[：:].*?(.+?)(?=\n\d+\.|\n[一二三四五六七八九十]|\n\n)',
            r'并发.*?用户.*?(\d+.*?万?)',
            r'响应.*?时间.*?(\d+.*?毫秒|秒)'
        ]
        
        # 安全需求
        security_patterns = [
            r'安全.*?要求.*?[：:].*?(.+?)(?=\n\d+\.|\n[一二三四五六七八九十]|\n\n)',
            r'等保.*?三级',
            r'信息.*?安全.*?(.+?)(?=\n\d+\.|\n[一二三四五六七八九十]|\n\n)'
        ]
        
        # 提取各类需求
        for category, patterns in [
            ("functional", functional_patterns),
            ("performance", performance_patterns),
            ("security", security_patterns)
        ]:
            for pattern in patterns:
                matches = re.finditer(pattern, content, re.MULTILINE | re.DOTALL)
                for match in matches:
                    req_content = match.group(1).strip() if match.lastindex else match.group(0).strip()
                    if req_content and len(req_content) > 10:
                        requirements[category].append(req_content)
        
        return requirements

    def _find_section_context(self, content: str, position: int) -> str:
        """查找条款所在的章节上下文"""
        # 向前查找最近的章节标题
        before_content = content[:position]
        section_patterns = [
            r'第[一二三四五六七八九十\d]+章.*?(?=\n)',
            r'\d+\..*?(?=\n)',
            r'[一二三四五六七八九十]+、.*?(?=\n)'
        ]
        
        for pattern in section_patterns:
            matches = list(re.finditer(pattern, before_content))
            if matches:
                return matches[-1].group(0).strip()
        
        return "未知章节"


# 全局实例
enhanced_document_parser = EnhancedDocumentParser()
