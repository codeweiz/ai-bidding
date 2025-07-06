from typing import Dict, Any, List, Optional, Tuple
import logging
import asyncio
from datetime import datetime
import re

from langgraph.graph import StateGraph, END
from langgraph.graph.state import CompiledStateGraph

from backend.models.generation import WorkflowState, GenerationTaskStatus
from backend.services.llm_service import llm_service
from backend.services.document_parser import document_parser

logger = logging.getLogger(__name__)


class SectionNode:
    """章节节点类，用于构建层次化目录树"""

    def __init__(self, title: str, level: int, order: int):
        self.title = title
        self.level = level
        self.order = order
        self.children: List['SectionNode'] = []
        self.parent: Optional['SectionNode'] = None
        self.content = ""
        self.is_generated = False
        self.is_leaf = True

    def add_child(self, child: 'SectionNode'):
        """添加子节点"""
        child.parent = self
        self.children.append(child)
        self.is_leaf = False

    def get_all_leaf_nodes(self) -> List['SectionNode']:
        """获取所有叶子节点"""
        if self.is_leaf:
            return [self]

        leaf_nodes = []
        for child in self.children:
            leaf_nodes.extend(child.get_all_leaf_nodes())
        return leaf_nodes

    def get_path(self) -> str:
        """获取节点路径"""
        path = []
        current = self
        while current:
            path.append(current.title)
            current = current.parent
        return " > ".join(reversed(path))


class WorkflowEngine:
    """工作流引擎，使用LangGraph管理生成流程"""

    def __init__(self):
        self.graph = self._build_workflow()
    
    def _build_workflow(self) -> CompiledStateGraph:
        """构建优化后的层次化工作流图"""
        workflow = StateGraph(WorkflowState)

        # 添加节点
        workflow.add_node("parse_document", self._parse_document)
        workflow.add_node("generate_outline", self._generate_outline)
        workflow.add_node("build_section_tree", self._build_section_tree)
        workflow.add_node("generate_leaf_content", self._generate_leaf_content)
        workflow.add_node("generate_parent_summaries", self._generate_parent_summaries)
        workflow.add_node("differentiate_content", self._differentiate_content)
        workflow.add_node("finalize", self._finalize)

        # 设置入口点
        workflow.set_entry_point("parse_document")

        # 添加边 - 新的层次化流程
        workflow.add_edge("parse_document", "generate_outline")
        workflow.add_edge("generate_outline", "build_section_tree")
        workflow.add_edge("build_section_tree", "generate_leaf_content")
        workflow.add_edge("generate_leaf_content", "generate_parent_summaries")

        # 条件边：是否需要差异化处理
        workflow.add_conditional_edges(
            "generate_parent_summaries",
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
        """解析文档节点 - 提取招标文档内容"""
        logger.info(f"开始解析文档，项目ID: {state.project_id}")

        try:
            if not state.document_content:
                state.error = "文档内容为空"
                return state

            # 清理和预处理文档内容
            cleaned_content = self._clean_document_content(state.document_content)
            state.document_content = cleaned_content

            state.current_step = "parse_document"
            state.updated_at = datetime.now()

            logger.info(f"文档解析完成，项目ID: {state.project_id}")
            return state

        except Exception as e:
            logger.error(f"文档解析失败: {e}")
            state.error = str(e)
            return state

    def _clean_document_content(self, content: str) -> str:
        """清理文档内容"""
        # 移除多余的空行
        content = re.sub(r'\n\s*\n', '\n\n', content)
        # 移除行首行尾空格
        lines = [line.strip() for line in content.split('\n')]
        return '\n'.join(lines)
    
    async def _generate_outline(self, state: WorkflowState) -> WorkflowState:
        """生成提纲节点 - 使用优化的IPTV领域prompt"""
        logger.info(f"开始生成提纲，项目ID: {state.project_id}")

        try:
            # 使用您提供的专业prompt生成提纲
            result = await llm_service.generate_iptv_outline(state.document_content)

            if result["status"] == "success":
                state.outline = result["outline"]
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
    
    async def _build_section_tree(self, state: WorkflowState) -> WorkflowState:
        """构建章节树结构"""
        logger.info(f"开始构建章节树，项目ID: {state.project_id}")

        try:
            if not state.outline:
                state.error = "提纲为空，无法构建章节树"
                return state

            # 解析提纲为层次化的章节树
            section_tree = self._parse_outline_to_tree(state.outline)

            # 将树结构转换为扁平的章节列表（保持层次信息）
            state.sections = self._tree_to_sections_list(section_tree)

            # 存储树结构到状态中（用于后续处理）
            state.section_tree = section_tree

            state.current_step = "build_section_tree"
            state.updated_at = datetime.now()

            logger.info(f"章节树构建完成，共{len(state.sections)}个章节，项目ID: {state.project_id}")
            return state

        except Exception as e:
            logger.error(f"构建章节树失败: {e}")
            state.error = str(e)
            return state
    
    async def _generate_leaf_content(self, state: WorkflowState) -> WorkflowState:
        """生成叶子节点内容 - 并行生成所有叶子节点"""
        logger.info(f"开始生成叶子节点内容，项目ID: {state.project_id}")

        try:
            if not hasattr(state, 'section_tree') or not state.section_tree:
                state.error = "章节树未构建，无法生成叶子节点内容"
                return state

            # 获取所有叶子节点
            leaf_nodes = []
            for root_node in state.section_tree:
                leaf_nodes.extend(root_node.get_all_leaf_nodes())

            logger.info(f"找到{len(leaf_nodes)}个叶子节点，开始并发生成")

            # 并发生成所有叶子节点内容
            tasks = []
            for leaf_node in leaf_nodes:
                task = self._generate_single_leaf_content(leaf_node, state.document_content)
                tasks.append(task)

            # 等待所有任务完成
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # 处理结果
            success_count = 0
            for i, (leaf_node, result) in enumerate(zip(leaf_nodes, results)):
                if isinstance(result, Exception):
                    logger.error(f"叶子节点内容生成异常: {leaf_node.title}, 错误: {result}")
                    leaf_node.content = ""
                    leaf_node.is_generated = False
                elif result["status"] == "success":
                    # 清理内容中的markdown格式
                    cleaned_content = self._clean_markdown_format(result["content"])
                    leaf_node.content = cleaned_content
                    leaf_node.is_generated = True
                    success_count += 1
                    logger.info(f"叶子节点内容生成成功: {leaf_node.title}")
                else:
                    logger.error(f"叶子节点内容生成失败: {leaf_node.title}, 错误: {result.get('error')}")
                    leaf_node.content = ""
                    leaf_node.is_generated = False

            state.current_step = "generate_leaf_content"
            state.updated_at = datetime.now()
            logger.info(f"叶子节点内容生成完成，项目ID: {state.project_id}, 成功: {success_count}/{len(leaf_nodes)}")

            return state

        except Exception as e:
            logger.error(f"叶子节点内容生成异常: {e}")
            state.error = str(e)
            return state

    async def _generate_single_leaf_content(self, leaf_node: 'SectionNode', document_content: str) -> Dict[str, Any]:
        """生成单个叶子节点内容"""
        try:
            # 使用完整文档内容以确保内容质量
            # 注释掉相关性筛选，直接使用完整内容
            # relevant_content = await self._get_relevant_content(leaf_node, document_content)

            result = await llm_service.generate_iptv_section_content(
                section_title=leaf_node.title,
                section_path=leaf_node.get_path(),
                document_content=document_content  # 使用完整文档内容
            )
            return result
        except Exception as e:
            logger.error(f"生成单个叶子节点内容失败: {leaf_node.title}, 错误: {e}")
            return {"status": "error", "error": str(e)}
    
    async def _generate_parent_summaries(self, state: WorkflowState) -> WorkflowState:
        """生成父节点总结 - 并行生成父节点总结"""
        logger.info(f"开始生成父节点总结，项目ID: {state.project_id}")

        try:
            if not hasattr(state, 'section_tree') or not state.section_tree:
                state.error = "章节树未构建，无法生成父节点总结"
                return state

            # 收集所有需要生成总结的父节点
            parent_nodes = []
            for root_node in state.section_tree:
                parent_nodes.extend(self._collect_parent_nodes(root_node))

            logger.info(f"找到{len(parent_nodes)}个父节点，开始并行生成总结")

            # 并行生成所有父节点总结
            tasks = []
            for parent_node in parent_nodes:
                task = self._generate_single_parent_summary(parent_node, state.document_content)
                tasks.append(task)

            # 等待所有任务完成
            if tasks:
                results = await asyncio.gather(*tasks, return_exceptions=True)

                # 处理结果
                success_count = 0
                for i, (parent_node, result) in enumerate(zip(parent_nodes, results)):
                    if isinstance(result, Exception):
                        logger.error(f"父节点总结生成异常: {parent_node.title}, 错误: {result}")
                    elif result["status"] == "success":
                        # 清理内容中的markdown格式
                        cleaned_content = self._clean_markdown_format(result["content"])
                        parent_node.content = cleaned_content
                        parent_node.is_generated = True
                        success_count += 1
                        logger.info(f"父节点总结生成成功: {parent_node.title}")
                    else:
                        logger.error(f"父节点总结生成失败: {parent_node.title}, 错误: {result.get('error')}")

                logger.info(f"父节点总结生成完成，成功: {success_count}/{len(parent_nodes)}")

            # 更新sections列表
            state.sections = self._tree_to_sections_list(state.section_tree)

            state.current_step = "generate_parent_summaries"
            state.updated_at = datetime.now()
            logger.info(f"父节点总结生成完成，项目ID: {state.project_id}")

            return state

        except Exception as e:
            logger.error(f"父节点总结生成异常: {e}")
            state.error = str(e)
            return state

    async def _generate_node_summary_recursive(self, node: SectionNode, document_content: str):
        """递归生成节点总结"""
        # 如果是叶子节点，已经有内容了，直接返回
        if node.is_leaf:
            return

        # 先确保所有子节点都有内容
        for child in node.children:
            await self._generate_node_summary_recursive(child, document_content)

        # 收集所有子节点的内容
        children_content = []
        for child in node.children:
            if child.content:
                children_content.append(f"### {child.title}\n{child.content}")

        if children_content:
            # 生成父节点总结
            logger.info(f"生成父节点总结: {node.get_path()}")

            result = await llm_service.generate_parent_summary(
                parent_title=node.title,
                parent_path=node.get_path(),
                children_content="\n\n".join(children_content),
                document_content=document_content
            )

            if result["status"] == "success":
                node.content = result["content"]
                node.is_generated = True
                logger.info(f"父节点总结生成成功: {node.title}")
            else:
                logger.error(f"父节点总结生成失败: {result.get('error')}")
                node.content = ""
                node.is_generated = False
    
    async def _differentiate_content(self, state: WorkflowState) -> WorkflowState:
        """差异化处理节点 - 对所有生成的内容进行差异化"""
        logger.info(f"开始差异化处理，项目ID: {state.project_id}")

        try:
            if not hasattr(state, 'section_tree') or not state.section_tree:
                state.error = "章节树未构建，无法进行差异化处理"
                return state

            # 对所有节点进行差异化处理
            for root_node in state.section_tree:
                await self._differentiate_node_recursive(root_node)

            # 更新sections列表
            state.sections = self._tree_to_sections_list(state.section_tree)

            state.current_step = "differentiate_content"
            state.updated_at = datetime.now()
            logger.info(f"差异化处理完成，项目ID: {state.project_id}")

            return state

        except Exception as e:
            logger.error(f"差异化处理异常: {e}")
            state.error = str(e)
            return state

    async def _differentiate_node_recursive(self, node: SectionNode):
        """递归对节点进行差异化处理"""
        # 处理当前节点
        if node.content and node.is_generated:
            logger.info(f"差异化处理节点: {node.title}")

            result = await llm_service.differentiate_content(node.content)

            if result["status"] == "success":
                node.differentiated_content = result["differentiated_content"]
            else:
                logger.error(f"节点差异化失败: {result.get('error')}")
                node.differentiated_content = node.content

        # 递归处理子节点
        for child in node.children:
            await self._differentiate_node_recursive(child)

    async def _finalize(self, state: WorkflowState) -> WorkflowState:
        """完成节点"""
        logger.info(f"工作流完成，项目ID: {state.project_id}")

        state.current_step = "completed"
        state.updated_at = datetime.now()

        return state
    
    def _should_differentiate(self, state: WorkflowState) -> str:
        """判断是否需要差异化处理"""
        # if state.enable_differentiation:
        #     return "differentiate"
        # else:
        #     return "finalize"
        return "finalize"

    def _parse_outline_to_tree(self, outline: str) -> List[SectionNode]:
        """解析提纲为层次化的章节树 - 专门处理数字编号格式"""
        lines = outline.split('\n')
        root_nodes = []
        node_stack = []  # 用于跟踪当前层级的节点栈
        order_counter = 0

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # 解析数字编号格式的标题
            level, title = self._parse_numbered_title(line)

            if level == 0 or not title:
                continue  # 跳过无法解析的行

            order_counter += 1
            node = SectionNode(title, level, order_counter)

            # 调整节点栈，移除比当前级别高或相等的节点
            while node_stack and node_stack[-1].level >= level:
                node_stack.pop()

            # 如果栈为空，这是根节点
            if not node_stack:
                root_nodes.append(node)
            else:
                # 添加到父节点
                parent = node_stack[-1]
                parent.add_child(node)

            # 将当前节点加入栈
            node_stack.append(node)

        return root_nodes

    def _parse_numbered_title(self, line: str) -> tuple[int, str]:
        """解析数字编号格式的标题，返回(级别, 标题)"""
        line = line.strip()

        # 匹配各种数字编号格式 - 按照从复杂到简单的顺序匹配
        patterns = [
            (r'^(\d+)\.(\d+)\.(\d+)\.(\d+)\.(\d+)\s+(.+)$', 5),  # 1.1.1.1.1 标题
            (r'^(\d+)\.(\d+)\.(\d+)\.(\d+)\s+(.+)$', 4),         # 1.1.1.1 标题
            (r'^(\d+)\.(\d+)\.(\d+)\s+(.+)$', 3),                # 1.1.1 标题
            (r'^(\d+)\.(\d+)\s+(.+)$', 2),                       # 1.1 标题
            (r'^(\d+)\.\s+(.+)$', 1),                            # 1. 标题
        ]

        for pattern, level in patterns:
            match = re.match(pattern, line)
            if match:
                # 提取标题部分（最后一个捕获组）
                title = match.groups()[-1].strip()
                return level, title

        # 如果没有匹配到数字编号格式，检查是否是纯文本标题
        if line and not line.startswith('#') and not line.startswith('-') and not line.startswith('*'):
            # 可能是没有编号的标题，默认为1级
            return 1, line

        return 0, ""  # 无法解析
    
    def _tree_to_sections_list(self, tree: List[SectionNode]) -> List[Dict[str, Any]]:
        """将章节树转换为扁平的章节列表"""
        sections = []

        def traverse_node(node: SectionNode):
            # 添加当前节点
            sections.append({
                "title": node.title,
                "level": node.level,
                "order": node.order,
                "path": node.get_path(),
                "content": node.content,
                "differentiated_content": getattr(node, 'differentiated_content', ''),
                "is_generated": node.is_generated,
                "is_leaf": node.is_leaf,
                "children_count": len(node.children)
            })

            # 递归遍历子节点
            for child in node.children:
                traverse_node(child)

        # 遍历所有根节点
        for root_node in tree:
            traverse_node(root_node)

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

    async def _get_relevant_content(self, leaf_node: 'SectionNode', document_content: str) -> str:
        """获取与章节相关的文档内容（向量检索优化）"""
        try:
            # 如果文档内容较短，直接返回全部内容
            if len(document_content) <= 2000:
                return document_content

            # 构建查询关键词
            query_keywords = [
                leaf_node.title,
                leaf_node.get_path(),
            ]

            # 添加父节点标题作为上下文
            if leaf_node.parent:
                query_keywords.append(leaf_node.parent.title)

            query = " ".join(query_keywords)

            # 简单的关键词匹配（后续可以升级为向量检索）
            relevant_chunks = self._extract_relevant_chunks(query, document_content)

            # 如果找到相关内容，返回相关部分；否则返回前2000字符
            if relevant_chunks:
                return "\n".join(relevant_chunks)
            else:
                return document_content[:2000] + "..."

        except Exception as e:
            logger.warning(f"获取相关内容失败: {e}，使用原始内容")
            return document_content[:2000] + "..."

    def _extract_relevant_chunks(self, query: str, content: str, max_chunks: int = 3) -> List[str]:
        """提取相关文档片段"""
        try:
            # 将文档分割为段落
            paragraphs = content.split('\n\n')

            # 计算每个段落的相关性得分
            scored_paragraphs = []
            query_words = set(query.lower().split())

            for para in paragraphs:
                if len(para.strip()) < 50:  # 跳过太短的段落
                    continue

                para_words = set(para.lower().split())
                # 计算关键词重叠度
                overlap = len(query_words.intersection(para_words))
                if overlap > 0:
                    score = overlap / len(query_words)
                    scored_paragraphs.append((score, para))

            # 按得分排序，取前N个
            scored_paragraphs.sort(key=lambda x: x[0], reverse=True)
            relevant_chunks = [para for score, para in scored_paragraphs[:max_chunks]]

            return relevant_chunks

        except Exception as e:
            logger.warning(f"提取相关片段失败: {e}")
            return []

    def _collect_parent_nodes(self, node: SectionNode) -> List[SectionNode]:
        """收集所有父节点（非叶子节点）"""
        parent_nodes = []

        # 如果不是叶子节点，则是父节点
        if not node.is_leaf:
            parent_nodes.append(node)

        # 递归收集子节点中的父节点
        for child in node.children:
            parent_nodes.extend(self._collect_parent_nodes(child))

        return parent_nodes

    async def _generate_single_parent_summary(self, parent_node: SectionNode, document_content: str) -> Dict[str, Any]:
        """生成单个父节点总结"""
        try:
            # 收集所有子节点的内容
            children_content = []
            for child in parent_node.children:
                if child.content:
                    children_content.append(f"章节：{child.title}\n{child.content}")

            if not children_content:
                return {"status": "error", "error": "子节点内容为空"}

            combined_content = "\n\n".join(children_content)

            # 生成父节点总结
            result = await llm_service.generate_parent_summary(
                parent_title=parent_node.title,
                parent_path=parent_node.get_path(),
                children_content=combined_content,
                document_content=document_content
            )

            return result
        except Exception as e:
            logger.error(f"生成单个父节点总结失败: {parent_node.title}, 错误: {e}")
            return {"status": "error", "error": str(e)}

    def _clean_markdown_format(self, content: str) -> str:
        """清理内容中的markdown格式标记"""
        if not content:
            return content

        try:
            # 移除markdown标题标记
            content = re.sub(r'^#{1,6}\s+', '', content, flags=re.MULTILINE)

            # 移除粗体和斜体标记
            content = re.sub(r'\*\*([^*]+)\*\*', r'\1', content)  # 粗体
            content = re.sub(r'\*([^*]+)\*', r'\1', content)      # 斜体
            content = re.sub(r'__([^_]+)__', r'\1', content)      # 粗体
            content = re.sub(r'_([^_]+)_', r'\1', content)        # 斜体

            # 移除列表标记
            content = re.sub(r'^[\s]*[-*+]\s+', '', content, flags=re.MULTILINE)
            content = re.sub(r'^[\s]*\d+\.\s+', '', content, flags=re.MULTILINE)

            # 移除代码块标记
            content = re.sub(r'```[\s\S]*?```', '', content)  # 代码块
            content = re.sub(r'`([^`]+)`', r'\1', content)    # 行内代码

            # 移除链接标记
            content = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', content)

            # 移除引用标记
            content = re.sub(r'^>\s+', '', content, flags=re.MULTILINE)

            # 移除水平分割线
            content = re.sub(r'^[-*_]{3,}$', '', content, flags=re.MULTILINE)

            # 清理多余的空行
            content = re.sub(r'\n{3,}', '\n\n', content)

            # 清理首尾空白
            content = content.strip()

            return content

        except Exception as e:
            logger.warning(f"清理markdown格式失败: {e}")
            return content


# 全局实例
workflow_engine = WorkflowEngine()
