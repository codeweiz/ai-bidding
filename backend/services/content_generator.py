from typing import Dict, Any, List, Optional
import logging
import asyncio
from pathlib import Path
from datetime import datetime

from docx import Document
from docx.shared import Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH

from backend.models.project import Project, ProjectStatus
from backend.models.generation import WorkflowState
from backend.services.workflow_engine import workflow_engine
from backend.services.document_parser import document_parser

logger = logging.getLogger(__name__)


class ContentGenerator:
    """内容生成器，负责整个生成流程的协调"""
    
    def __init__(self):
        self.output_dir = Path("outputs")
        self.output_dir.mkdir(exist_ok=True)
    
    async def generate_proposal(self, project: Project, document_path: str) -> Dict[str, Any]:
        """生成完整的投标方案"""
        logger.info(f"开始生成投标方案，项目: {project.name}")
        
        try:
            # 1. 解析文档
            document_result = document_parser.parse_document(Path(document_path))
            document_content = "\n".join([doc.page_content for doc in document_result["documents"]])
            
            # 2. 创建工作流状态
            workflow_state = WorkflowState(
                project_id=project.id or "unknown",
                current_step="start",
                document_content=document_content,
                enable_differentiation=project.enable_differentiation
            )
            
            # 3. 运行工作流
            final_state = await workflow_engine.run_workflow(workflow_state)
            
            if final_state.error:
                return {
                    "status": "error",
                    "error": final_state.error
                }
            
            # 4. 生成Word文档
            word_doc_path = await self._generate_word_document(project, final_state)
            
            return {
                "status": "success",
                "requirements_analysis": final_state.requirements_analysis,
                "outline": final_state.outline,
                "sections": final_state.sections,
                "document_path": str(word_doc_path)
            }
            
        except Exception as e:
            logger.error(f"生成投标方案失败: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def _generate_word_document(self, project: Project, state: WorkflowState) -> Path:
        """生成Word文档"""
        logger.info(f"开始生成Word文档，项目: {project.name}")
        
        # 创建Word文档
        doc = Document()
        
        # 添加标题
        title = doc.add_heading(f'{project.name} - 技术方案', 0)
        title.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        # 添加目录占位符
        doc.add_heading('目录', level=1)
        doc.add_paragraph('（此处应插入自动生成的目录）')
        doc.add_page_break()
        
        # 添加章节内容
        for section in state.sections:
            if not section.get("is_generated"):
                continue
                
            # 添加章节标题
            if section["level"] == 1:
                doc.add_heading(section["title"], level=1)
            elif section["level"] == 2:
                doc.add_heading(section["title"], level=2)
            else:
                doc.add_heading(section["title"], level=3)
            
            # 添加章节内容
            content = section.get("differentiated_content") or section.get("content", "")
            if content:
                # 按段落分割内容
                paragraphs = content.split('\n\n')
                for para in paragraphs:
                    if para.strip():
                        doc.add_paragraph(para.strip())
            
            # 添加一些间距
            doc.add_paragraph()
        
        # 保存文档
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{project.name}_{timestamp}.docx"
        file_path = self.output_dir / filename
        
        doc.save(str(file_path))
        logger.info(f"Word文档生成完成: {file_path}")
        
        return file_path
    
    async def analyze_requirements_only(self, document_path: str) -> Dict[str, Any]:
        """仅分析需求，不生成完整方案"""
        logger.info(f"开始分析需求，文档: {document_path}")
        
        try:
            # 解析文档
            document_result = document_parser.parse_document(Path(document_path))
            document_content = "\n".join([doc.page_content for doc in document_result["documents"]])
            
            # 创建简化的工作流状态
            workflow_state = WorkflowState(
                project_id="temp",
                current_step="start",
                document_content=document_content
            )
            
            # 只运行需求分析步骤
            from backend.services.llm_service import llm_service
            result = await llm_service.analyze_requirements(document_content)
            
            if result["status"] == "success":
                return {
                    "status": "success",
                    "analysis": result["analysis"],
                    "document_info": {
                        "name": document_result["file_name"],
                        "type": document_result["file_type"],
                        "pages": document_result["metadata"]["total_pages"],
                        "chunks": document_result["metadata"]["total_chunks"]
                    }
                }
            else:
                return {
                    "status": "error",
                    "error": result.get("error", "需求分析失败")
                }
                
        except Exception as e:
            logger.error(f"需求分析失败: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def generate_outline_only(self, requirements_analysis: str) -> Dict[str, Any]:
        """仅生成提纲"""
        logger.info("开始生成提纲")
        
        try:
            from backend.services.llm_service import llm_service
            result = await llm_service.generate_outline(requirements_analysis)
            
            if result["status"] == "success":
                return {
                    "status": "success",
                    "outline": result["outline"]
                }
            else:
                return {
                    "status": "error",
                    "error": result.get("error", "提纲生成失败")
                }
                
        except Exception as e:
            logger.error(f"提纲生成失败: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def generate_section_content(self, section_title: str, requirements: str, 
                                     context: str = "") -> Dict[str, Any]:
        """生成单个章节内容"""
        logger.info(f"开始生成章节内容: {section_title}")
        
        try:
            from backend.services.llm_service import llm_service
            result = await llm_service.generate_content(section_title, requirements, context)
            
            if result["status"] == "success":
                return {
                    "status": "success",
                    "content": result["content"]
                }
            else:
                return {
                    "status": "error",
                    "error": result.get("error", "内容生成失败")
                }
                
        except Exception as e:
            logger.error(f"章节内容生成失败: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    def get_output_files(self) -> List[Dict[str, Any]]:
        """获取输出文件列表"""
        files = []
        
        if self.output_dir.exists():
            for file_path in self.output_dir.glob("*.docx"):
                stat = file_path.stat()
                files.append({
                    "name": file_path.name,
                    "path": str(file_path),
                    "size": stat.st_size,
                    "created_at": datetime.fromtimestamp(stat.st_ctime),
                    "modified_at": datetime.fromtimestamp(stat.st_mtime)
                })
        
        # 按修改时间倒序排列
        files.sort(key=lambda x: x["modified_at"], reverse=True)
        return files


# 全局实例
content_generator = ContentGenerator()
