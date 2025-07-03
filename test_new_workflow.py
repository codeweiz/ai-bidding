#!/usr/bin/env python3
"""
测试新的层次化LangGraph工作流
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).parent))

from backend.models.generation import WorkflowState
from backend.services.workflow_engine import WorkflowEngine, SectionNode
from backend.services.document_parser import document_parser


async def test_section_tree():
    """测试章节树构建"""
    print("🧪 测试章节树构建...")
    
    # 模拟提纲
    outline = """
# 技术方案
## 1. 系统架构设计
### 1.1 总体架构
### 1.2 技术架构
#### 1.2.1 前端架构
#### 1.2.2 后端架构
### 1.3 部署架构
## 2. 功能设计
### 2.1 核心功能
### 2.2 扩展功能
## 3. 实施方案
### 3.1 实施计划
### 3.2 风险控制
"""
    
    engine = WorkflowEngine()
    tree = engine._parse_outline_to_tree(outline)
    
    print(f"✅ 构建了{len(tree)}个根节点")
    
    # 打印树结构
    def print_tree(nodes, indent=0):
        for node in nodes:
            print("  " * indent + f"- {node.title} (Level {node.level}, Leaf: {node.is_leaf})")
            if node.children:
                print_tree(node.children, indent + 1)
    
    print_tree(tree)
    
    # 测试叶子节点获取
    all_leaves = []
    for root in tree:
        all_leaves.extend(root.get_all_leaf_nodes())
    
    print(f"\n🍃 找到{len(all_leaves)}个叶子节点:")
    for leaf in all_leaves:
        print(f"  - {leaf.get_path()}")
    
    return tree


async def test_document_parsing():
    """测试文档解析"""
    print("\n📄 测试文档解析...")
    
    test_file = Path("uploads/test_bidding_document.txt")
    if not test_file.exists():
        print("❌ 测试文件不存在，跳过文档解析测试")
        return None
    
    try:
        result = document_parser.parse_document(test_file)
        content = "\n".join([doc.page_content for doc in result["documents"]])
        print(f"✅ 文档解析成功，内容长度: {len(content)} 字符")
        print(f"📊 文档信息: {result['metadata']}")
        return content[:2000]  # 返回前2000字符用于测试
    except Exception as e:
        print(f"❌ 文档解析失败: {e}")
        return None


async def test_full_workflow():
    """测试完整工作流"""
    print("\n🚀 测试完整工作流...")
    
    # 准备测试数据
    document_content = await test_document_parsing()
    if not document_content:
        # 使用模拟数据
        document_content = """
        智慧城市IPTV系统建设项目招标文件
        
        一、项目概述
        本项目旨在建设一套完整的智慧城市IPTV管理系统，包括内容管理、用户管理、设备管理等功能。
        
        二、技术需求
        1. 系统架构要求
        - 采用微服务架构设计
        - 支持云原生部署
        - 具备高可用性和可扩展性
        
        2. 功能需求
        - 实时视频流处理
        - 用户权限管理
        - 内容分发网络
        - 数据统计分析
        
        三、性能指标
        - 系统响应时间：≤2秒
        - 并发用户数：≥10000
        - 视频质量：支持4K高清
        """
    
    # 创建工作流状态
    state = WorkflowState(
        project_id="test_project_001",
        current_step="start",
        document_content=document_content,
        enable_differentiation=True
    )
    
    # 创建工作流引擎
    engine = WorkflowEngine()
    
    try:
        print("⏳ 运行工作流...")
        final_state = await engine.run_workflow(state)
        
        if final_state.error:
            print(f"❌ 工作流执行失败: {final_state.error}")
            return
        
        print(f"✅ 工作流执行成功!")
        print(f"📋 当前步骤: {final_state.current_step}")
        print(f"📝 生成了{len(final_state.sections)}个章节")
        
        # 显示章节信息
        print("\n📚 章节列表:")
        for i, section in enumerate(final_state.sections[:5]):  # 只显示前5个
            print(f"  {i+1}. {section['title']} (Level {section['level']})")
            if section.get('is_leaf'):
                print(f"     🍃 叶子节点 - 已生成: {section.get('is_generated', False)}")
            else:
                print(f"     🌿 父节点 - 子节点数: {section.get('children_count', 0)}")
        
        if len(final_state.sections) > 5:
            print(f"     ... 还有{len(final_state.sections) - 5}个章节")
        
        # 显示生成的提纲
        if final_state.outline:
            print(f"\n📋 生成的提纲 (前500字符):")
            print(final_state.outline[:500] + "..." if len(final_state.outline) > 500 else final_state.outline)
        
        return final_state
        
    except Exception as e:
        print(f"❌ 工作流执行异常: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """主测试函数"""
    print("🤖 AI投标LangGraph工作流测试")
    print("=" * 50)
    
    # 测试章节树构建
    await test_section_tree()
    
    # 测试完整工作流
    await test_full_workflow()
    
    print("\n" + "=" * 50)
    print("✅ 测试完成!")


if __name__ == "__main__":
    asyncio.run(main())
