from typing import Dict, Any, List, Optional
import logging
import asyncio
from datetime import datetime

from langgraph.graph import StateGraph, END
from langgraph.graph.state import CompiledStateGraph

from backend.models.generation import WorkflowState, GenerationTaskStatus
from backend.services.llm_service import llm_service
from backend.services.document_parser import document_parser

logger = logging.getLogger(__name__)


class WorkflowEngine:
    """工作流引擎，使用LangGraph管理生成流程"""
    
    def __init__(self):
        self.graph = self._build_workflow()
    
    def _build_workflow(self) -> CompiledStateGraph:
        """构建工作流图"""
        workflow = StateGraph(WorkflowState)
        
        # 添加节点
        workflow.add_node("parse_document", self._parse_document)
        workflow.add_node("analyze_requirements", self._analyze_requirements)
        workflow.add_node("generate_outline", self._generate_outline)
        workflow.add_node("generate_content", self._generate_content)
        workflow.add_node("differentiate_content", self._differentiate_content)
        workflow.add_node("finalize", self._finalize)
        
        # 设置入口点
        workflow.set_entry_point("parse_document")
        
        # 添加边
        workflow.add_edge("parse_document", "analyze_requirements")
        workflow.add_edge("analyze_requirements", "generate_outline")
        workflow.add_edge("generate_outline", "generate_content")
        
        # 条件边：是否需要差异化处理
        workflow.add_conditional_edges(
            "generate_content",
            self._should_differentiate,
            {
                "differentiate": "differentiate_content",
                "finalize": "finalize"
            }
        )
        
        workflow.add_edge("differentiate_content", "finalize")
        workflow.add_edge("finalize", END)
        
        return workflow.compile()
    
    async def _parse_document(self, state: WorkflowState) -> WorkflowState:
        """解析文档节点"""
        logger.info(f"开始解析文档，项目ID: {state.project_id}")
        
        try:
            # 这里假设文档路径已经在state中
            # 实际实现中需要从项目信息中获取文档路径
            if not state.document_content:
                state.error = "文档内容为空"
                return state
            
            state.current_step = "parse_document"
            state.updated_at = datetime.now()
            
            logger.info(f"文档解析完成，项目ID: {state.project_id}")
            return state
            
        except Exception as e:
            logger.error(f"文档解析失败: {e}")
            state.error = str(e)
            return state
    
    async def _analyze_requirements(self, state: WorkflowState) -> WorkflowState:
        """需求分析节点"""
        logger.info(f"开始需求分析，项目ID: {state.project_id}")
        
        try:
            result = await llm_service.analyze_requirements(state.document_content)
            
            if result["status"] == "success":
                state.requirements_analysis = result["analysis"]
                state.current_step = "analyze_requirements"
                state.updated_at = datetime.now()
                logger.info(f"需求分析完成，项目ID: {state.project_id}")
            else:
                state.error = result.get("error", "需求分析失败")
                logger.error(f"需求分析失败: {state.error}")
            
            return state
            
        except Exception as e:
            logger.error(f"需求分析异常: {e}")
            state.error = str(e)
            return state
    
    async def _generate_outline(self, state: WorkflowState) -> WorkflowState:
        """生成提纲节点"""
        logger.info(f"开始生成提纲，项目ID: {state.project_id}")
        
        try:
            result = await llm_service.generate_outline(state.requirements_analysis)
            
            if result["status"] == "success":
                state.outline = result["outline"]
                # 解析提纲，生成章节列表
                state.sections = self._parse_outline_to_sections(result["outline"])
                state.current_step = "generate_outline"
                state.updated_at = datetime.now()
                logger.info(f"提纲生成完成，项目ID: {state.project_id}")
            else:
                state.error = result.get("error", "提纲生成失败")
                logger.error(f"提纲生成失败: {state.error}")
            
            return state
            
        except Exception as e:
            logger.error(f"提纲生成异常: {e}")
            state.error = str(e)
            return state
    
    async def _generate_content(self, state: WorkflowState) -> WorkflowState:
        """生成内容节点"""
        logger.info(f"开始生成内容，项目ID: {state.project_id}")
        
        try:
            # 为每个章节生成内容
            for i, section in enumerate(state.sections):
                logger.info(f"生成章节内容: {section['title']}")
                
                result = await llm_service.generate_content(
                    section_title=section["title"],
                    section_requirements=section.get("requirements", ""),
                    context=state.requirements_analysis
                )
                
                if result["status"] == "success":
                    state.sections[i]["content"] = result["content"]
                    state.sections[i]["is_generated"] = True
                else:
                    logger.error(f"章节内容生成失败: {result.get('error')}")
                    state.sections[i]["content"] = ""
                    state.sections[i]["is_generated"] = False
            
            state.current_step = "generate_content"
            state.updated_at = datetime.now()
            logger.info(f"内容生成完成，项目ID: {state.project_id}")
            
            return state
            
        except Exception as e:
            logger.error(f"内容生成异常: {e}")
            state.error = str(e)
            return state
    
    async def _differentiate_content(self, state: WorkflowState) -> WorkflowState:
        """差异化处理节点"""
        logger.info(f"开始差异化处理，项目ID: {state.project_id}")
        
        try:
            # 对每个章节进行差异化处理
            for i, section in enumerate(state.sections):
                if section.get("content") and section.get("is_generated"):
                    logger.info(f"差异化处理章节: {section['title']}")
                    
                    result = await llm_service.differentiate_content(section["content"])
                    
                    if result["status"] == "success":
                        state.sections[i]["differentiated_content"] = result["differentiated_content"]
                    else:
                        logger.error(f"章节差异化失败: {result.get('error')}")
                        state.sections[i]["differentiated_content"] = section["content"]
            
            state.current_step = "differentiate_content"
            state.updated_at = datetime.now()
            logger.info(f"差异化处理完成，项目ID: {state.project_id}")
            
            return state
            
        except Exception as e:
            logger.error(f"差异化处理异常: {e}")
            state.error = str(e)
            return state
    
    async def _finalize(self, state: WorkflowState) -> WorkflowState:
        """完成节点"""
        logger.info(f"工作流完成，项目ID: {state.project_id}")
        
        state.current_step = "completed"
        state.updated_at = datetime.now()
        
        return state
    
    def _should_differentiate(self, state: WorkflowState) -> str:
        """判断是否需要差异化处理"""
        if state.enable_differentiation:
            return "differentiate"
        else:
            return "finalize"
    
    def _parse_outline_to_sections(self, outline: str) -> List[Dict[str, Any]]:
        """解析提纲为章节列表"""
        sections = []
        lines = outline.split('\n')
        
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
                
            # 简单的章节解析逻辑
            if line.startswith('##'):
                level = 2
                title = line.replace('##', '').strip()
            elif line.startswith('#'):
                level = 1
                title = line.replace('#', '').strip()
            elif line.startswith('###'):
                level = 3
                title = line.replace('###', '').strip()
            else:
                continue
            
            sections.append({
                "title": title,
                "level": level,
                "order": len(sections) + 1,
                "requirements": "",
                "content": "",
                "differentiated_content": "",
                "is_generated": False,
                "is_approved": False
            })
        
        return sections
    
    async def run_workflow(self, initial_state: WorkflowState) -> WorkflowState:
        """运行工作流"""
        logger.info(f"启动工作流，项目ID: {initial_state.project_id}")
        
        try:
            # 运行工作流
            final_state = await self.graph.ainvoke(initial_state)
            return final_state
            
        except Exception as e:
            logger.error(f"工作流执行失败: {e}")
            initial_state.error = str(e)
            return initial_state


# 全局实例
workflow_engine = WorkflowEngine()
