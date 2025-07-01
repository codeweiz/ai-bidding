"""
增强的工作流引擎 - 集成持久化、校验和错误恢复功能
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from langgraph.graph import StateGraph, END
from langgraph.graph.state import CompiledStateGraph

from backend.models.generation import WorkflowState, GenerationTaskStatus
from backend.services.llm_service import llm_service
from backend.services.document_parser import document_parser
from backend.services.persistence_service import persistence_service
from backend.services.validation_service import validation_service, ValidationResult

logger = logging.getLogger(__name__)


class EnhancedWorkflowEngine:
    """增强的工作流引擎，支持持久化、校验和错误恢复"""
    
    def __init__(self):
        self.graph = self._build_enhanced_workflow()
    
    def _build_enhanced_workflow(self) -> CompiledStateGraph:
        """构建增强的工作流图"""
        workflow = StateGraph(WorkflowState)
        
        # 添加节点
        workflow.add_node("parse_document", self._parse_document)
        workflow.add_node("analyze_requirements", self._analyze_requirements)
        workflow.add_node("validate_requirements", self._validate_requirements)
        workflow.add_node("generate_outline", self._generate_outline)
        workflow.add_node("validate_outline", self._validate_outline)
        workflow.add_node("generate_content", self._generate_content)
        workflow.add_node("validate_content", self._validate_content)
        workflow.add_node("differentiate_content", self._differentiate_content)
        workflow.add_node("finalize", self._finalize)
        
        # 设置入口点
        workflow.set_entry_point("parse_document")
        
        # 添加边 - 包含校验步骤
        workflow.add_edge("parse_document", "analyze_requirements")
        workflow.add_edge("analyze_requirements", "validate_requirements")
        
        # 需求分析校验后的条件边
        workflow.add_conditional_edges(
            "validate_requirements",
            self._should_retry_requirements,
            {
                "retry": "analyze_requirements",
                "continue": "generate_outline"
            }
        )
        
        workflow.add_edge("generate_outline", "validate_outline")
        
        # 提纲校验后的条件边
        workflow.add_conditional_edges(
            "validate_outline",
            self._should_retry_outline,
            {
                "retry": "generate_outline",
                "continue": "generate_content"
            }
        )
        
        workflow.add_edge("generate_content", "validate_content")
        
        # 内容校验后的条件边
        workflow.add_conditional_edges(
            "validate_content",
            self._should_retry_content,
            {
                "retry": "generate_content",
                "continue_with_diff": "differentiate_content",
                "continue_without_diff": "finalize"
            }
        )
        
        workflow.add_edge("differentiate_content", "finalize")
        workflow.add_edge("finalize", END)
        
        return workflow.compile()
    
    async def run_workflow_with_persistence(self, initial_state: WorkflowState, task_id: str) -> WorkflowState:
        """运行带持久化的工作流"""
        logger.info(f"启动增强工作流，任务ID: {task_id}")
        
        try:
            # 设置任务ID到状态中
            initial_state.task_id = task_id
            
            # 运行工作流
            final_state = await self.graph.ainvoke(initial_state)
            
            logger.info(f"增强工作流执行完成，任务ID: {task_id}")
            return final_state
            
        except Exception as e:
            logger.error(f"增强工作流执行失败: {e}")
            initial_state.error = str(e)
            return initial_state
    
    async def _parse_document(self, state: WorkflowState) -> WorkflowState:
        """解析文档节点"""
        logger.info(f"开始解析文档，项目ID: {state.project_id}")
        
        try:
            # 保存检查点
            await self._save_checkpoint(state, "parse_document_start")
            
            if not state.document_content:
                state.error = "文档内容为空"
                return state
            
            state.current_step = "parse_document"
            state.updated_at = datetime.now()
            
            # 保存完成检查点
            await self._save_checkpoint(state, "parse_document_complete")
            
            logger.info(f"文档解析完成，项目ID: {state.project_id}")
            return state
            
        except Exception as e:
            logger.error(f"文档解析失败: {e}")
            state.error = str(e)
            return state
    
    async def _analyze_requirements(self, state: WorkflowState) -> WorkflowState:
        """分析需求节点"""
        logger.info(f"开始分析需求，项目ID: {state.project_id}")
        
        try:
            # 保存检查点
            await self._save_checkpoint(state, "analyze_requirements_start")
            
            result = await llm_service.analyze_requirements(state.document_content)
            
            if result["status"] == "success":
                state.requirements_analysis = result["analysis"]
                state.current_step = "analyze_requirements"
                state.updated_at = datetime.now()
                
                # 保存完成检查点
                await self._save_checkpoint(state, "analyze_requirements_complete")
                
                logger.info(f"需求分析完成，项目ID: {state.project_id}")
            else:
                state.error = result.get("error", "需求分析失败")
                logger.error(f"需求分析失败: {state.error}")
            
            return state
            
        except Exception as e:
            logger.error(f"需求分析异常: {e}")
            state.error = str(e)
            return state
    
    async def _validate_requirements(self, state: WorkflowState) -> WorkflowState:
        """校验需求分析"""
        logger.info(f"开始校验需求分析，项目ID: {state.project_id}")
        
        try:
            # 保存检查点
            await self._save_checkpoint(state, "validate_requirements_start")
            
            if not getattr(state, 'enable_validation', True):
                logger.info("跳过需求分析校验")
                return state
            
            validation_report = await validation_service.validate_requirements_analysis(
                state.requirements_analysis,
                state.document_content
            )
            
            # 保存校验报告
            if not hasattr(state, 'validation_reports'):
                state.validation_reports = []
            
            state.validation_reports.append({
                "step": "requirements_analysis",
                "report": validation_report.__dict__
            })
            
            # 如果校验失败且有修正内容，使用修正内容
            if (validation_report.overall_result == ValidationResult.FAIL and 
                validation_report.corrected_content):
                
                logger.info("使用修正后的需求分析内容")
                state.requirements_analysis = validation_report.corrected_content
                
                # 增加重试计数
                retry_count = getattr(state, 'requirements_retry_count', 0)
                state.requirements_retry_count = retry_count + 1
            
            state.current_step = "validate_requirements"
            state.updated_at = datetime.now()
            
            # 保存完成检查点
            await self._save_checkpoint(state, "validate_requirements_complete")
            
            logger.info(f"需求分析校验完成，项目ID: {state.project_id}")
            return state
            
        except Exception as e:
            logger.error(f"需求分析校验异常: {e}")
            state.error = str(e)
            return state
    
    async def _generate_outline(self, state: WorkflowState) -> WorkflowState:
        """生成提纲节点"""
        logger.info(f"开始生成提纲，项目ID: {state.project_id}")
        
        try:
            # 保存检查点
            await self._save_checkpoint(state, "generate_outline_start")
            
            result = await llm_service.generate_outline(state.requirements_analysis)
            
            if result["status"] == "success":
                state.outline = result["outline"]
                # 解析提纲，生成章节列表
                state.sections = self._parse_outline_to_sections(result["outline"])
                state.current_step = "generate_outline"
                state.updated_at = datetime.now()
                
                # 保存完成检查点
                await self._save_checkpoint(state, "generate_outline_complete")
                
                logger.info(f"提纲生成完成，项目ID: {state.project_id}")
            else:
                state.error = result.get("error", "提纲生成失败")
                logger.error(f"提纲生成失败: {state.error}")
            
            return state
            
        except Exception as e:
            logger.error(f"提纲生成异常: {e}")
            state.error = str(e)
            return state
    
    async def _validate_outline(self, state: WorkflowState) -> WorkflowState:
        """校验提纲"""
        logger.info(f"开始校验提纲，项目ID: {state.project_id}")
        
        try:
            # 保存检查点
            await self._save_checkpoint(state, "validate_outline_start")
            
            if not getattr(state, 'enable_validation', True):
                logger.info("跳过提纲校验")
                return state
            
            validation_report = await validation_service.validate_outline(
                state.outline,
                state.requirements_analysis
            )
            
            # 保存校验报告
            state.validation_reports.append({
                "step": "outline",
                "report": validation_report.__dict__
            })
            
            # 如果校验失败且有修正内容，使用修正内容
            if (validation_report.overall_result == ValidationResult.FAIL and 
                validation_report.corrected_content):
                
                logger.info("使用修正后的提纲内容")
                state.outline = validation_report.corrected_content
                state.sections = self._parse_outline_to_sections(validation_report.corrected_content)
                
                # 增加重试计数
                retry_count = getattr(state, 'outline_retry_count', 0)
                state.outline_retry_count = retry_count + 1
            
            state.current_step = "validate_outline"
            state.updated_at = datetime.now()
            
            # 保存完成检查点
            await self._save_checkpoint(state, "validate_outline_complete")
            
            logger.info(f"提纲校验完成，项目ID: {state.project_id}")
            return state
            
        except Exception as e:
            logger.error(f"提纲校验异常: {e}")
            state.error = str(e)
            return state
    
    async def _save_checkpoint(self, state: WorkflowState, checkpoint_name: str):
        """保存检查点"""
        try:
            if hasattr(state, 'task_id') and state.task_id:
                await persistence_service.save_workflow_state(
                    state.task_id, 
                    checkpoint_name, 
                    state
                )
        except Exception as e:
            logger.warning(f"保存检查点失败: {e}")
    
    def _should_retry_requirements(self, state: WorkflowState) -> str:
        """判断是否需要重试需求分析"""
        retry_count = getattr(state, 'requirements_retry_count', 0)
        max_retries = 2
        
        if retry_count < max_retries and hasattr(state, 'validation_reports'):
            last_report = state.validation_reports[-1] if state.validation_reports else None
            if (last_report and 
                last_report.get("step") == "requirements_analysis" and
                last_report.get("report", {}).get("overall_result") == ValidationResult.FAIL):
                return "retry"
        
        return "continue"
    
    def _should_retry_outline(self, state: WorkflowState) -> str:
        """判断是否需要重试提纲生成"""
        retry_count = getattr(state, 'outline_retry_count', 0)
        max_retries = 2
        
        if retry_count < max_retries and hasattr(state, 'validation_reports'):
            last_report = state.validation_reports[-1] if state.validation_reports else None
            if (last_report and 
                last_report.get("step") == "outline" and
                last_report.get("report", {}).get("overall_result") == ValidationResult.FAIL):
                return "retry"
        
        return "continue"
    
    def _should_retry_content(self, state: WorkflowState) -> str:
        """判断是否需要重试内容生成"""
        retry_count = getattr(state, 'content_retry_count', 0)
        max_retries = 2
        
        if retry_count < max_retries and hasattr(state, 'validation_reports'):
            # 检查最近的内容校验报告
            content_reports = [r for r in state.validation_reports if r.get("step", "").startswith("content_")]
            if content_reports:
                last_report = content_reports[-1]
                if last_report.get("report", {}).get("overall_result") == ValidationResult.FAIL:
                    return "retry"
        
        # 判断是否需要差异化处理
        if getattr(state, 'enable_differentiation', True):
            return "continue_with_diff"
        else:
            return "continue_without_diff"


    async def _generate_content(self, state: WorkflowState) -> WorkflowState:
        """生成内容节点"""
        logger.info(f"开始生成内容，项目ID: {state.project_id}")

        try:
            # 保存检查点
            await self._save_checkpoint(state, "generate_content_start")

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

            # 保存完成检查点
            await self._save_checkpoint(state, "generate_content_complete")

            logger.info(f"内容生成完成，项目ID: {state.project_id}")
            return state

        except Exception as e:
            logger.error(f"内容生成异常: {e}")
            state.error = str(e)
            return state

    async def _validate_content(self, state: WorkflowState) -> WorkflowState:
        """校验内容"""
        logger.info(f"开始校验内容，项目ID: {state.project_id}")

        try:
            # 保存检查点
            await self._save_checkpoint(state, "validate_content_start")

            if not getattr(state, 'enable_validation', True):
                logger.info("跳过内容校验")
                return state

            # 校验每个章节的内容
            for i, section in enumerate(state.sections):
                if not section.get("is_generated"):
                    continue

                validation_report = await validation_service.validate_section_content(
                    section["content"],
                    section["title"],
                    state.requirements_analysis
                )

                # 保存校验报告
                state.validation_reports.append({
                    "step": f"content_section_{i}",
                    "section_title": section["title"],
                    "report": validation_report.__dict__
                })

                # 如果校验失败且有修正内容，使用修正内容
                if (validation_report.overall_result == ValidationResult.FAIL and
                    validation_report.corrected_content):

                    logger.info(f"使用修正后的章节内容: {section['title']}")
                    state.sections[i]["content"] = validation_report.corrected_content

                    # 增加重试计数
                    retry_count = getattr(state, 'content_retry_count', 0)
                    state.content_retry_count = retry_count + 1

            state.current_step = "validate_content"
            state.updated_at = datetime.now()

            # 保存完成检查点
            await self._save_checkpoint(state, "validate_content_complete")

            logger.info(f"内容校验完成，项目ID: {state.project_id}")
            return state

        except Exception as e:
            logger.error(f"内容校验异常: {e}")
            state.error = str(e)
            return state

    async def _differentiate_content(self, state: WorkflowState) -> WorkflowState:
        """差异化内容节点"""
        logger.info(f"开始差异化处理，项目ID: {state.project_id}")

        try:
            # 保存检查点
            await self._save_checkpoint(state, "differentiate_content_start")

            # 为每个章节进行差异化处理
            for i, section in enumerate(state.sections):
                if not section.get("is_generated"):
                    continue

                logger.info(f"差异化处理章节: {section['title']}")

                result = await llm_service.differentiate_content(
                    section["content"],
                    section["title"]
                )

                if result["status"] == "success":
                    state.sections[i]["differentiated_content"] = result["content"]
                else:
                    logger.error(f"章节差异化失败: {result.get('error')}")
                    # 如果差异化失败，使用原内容
                    state.sections[i]["differentiated_content"] = section["content"]

            state.current_step = "differentiate_content"
            state.updated_at = datetime.now()

            # 保存完成检查点
            await self._save_checkpoint(state, "differentiate_content_complete")

            logger.info(f"差异化处理完成，项目ID: {state.project_id}")
            return state

        except Exception as e:
            logger.error(f"差异化处理异常: {e}")
            state.error = str(e)
            return state

    async def _finalize(self, state: WorkflowState) -> WorkflowState:
        """最终化节点"""
        logger.info(f"开始最终化处理，项目ID: {state.project_id}")

        try:
            # 保存检查点
            await self._save_checkpoint(state, "finalize_start")

            state.current_step = "finalize"
            state.updated_at = datetime.now()

            # 保存完成检查点
            await self._save_checkpoint(state, "finalize_complete")

            logger.info(f"最终化处理完成，项目ID: {state.project_id}")
            return state

        except Exception as e:
            logger.error(f"最终化处理异常: {e}")
            state.error = str(e)
            return state

    def _parse_outline_to_sections(self, outline: str) -> List[Dict[str, Any]]:
        """解析提纲为章节列表"""
        sections = []
        lines = outline.split('\n')

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # 匹配不同的标题格式
            patterns = [
                (r'^([1-9]\d*)\.\s*(.+)$', 1),           # 1. 标题
                (r'^([1-9]\d*\.[1-9]\d*)\s*(.+)$', 2),   # 1.1 标题
                (r'^([1-9]\d*\.[1-9]\d*\.[1-9]\d*)\s*(.+)$', 3),  # 1.1.1 标题
                (r'^([一二三四五六七八九十]+)、\s*(.+)$', 1),      # 一、标题
                (r'^（([一二三四五六七八九十]+)）\s*(.+)$', 2),    # （一）标题
            ]

            for pattern, level in patterns:
                import re
                match = re.match(pattern, line)
                if match:
                    title = match.group(2) if len(match.groups()) > 1 else match.group(1)
                    sections.append({
                        "title": title,
                        "level": level,
                        "order": len(sections) + 1,
                        "requirements": "",
                        "content": "",
                        "is_generated": False
                    })
                    break

        return sections


# 全局实例
enhanced_workflow_engine = EnhancedWorkflowEngine()
