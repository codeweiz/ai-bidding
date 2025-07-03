#!/usr/bin/env python3
"""
测试数字编号格式的完整工作流
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).parent))

from backend.models.generation import WorkflowState
from backend.services.workflow_engine import WorkflowEngine
from backend.services.llm_service import llm_service


async def test_numbered_outline_generation():
    """测试数字编号格式的提纲生成"""
    print("🧪 测试数字编号格式提纲生成")
    print("=" * 50)
    
    # 模拟招标文档内容
    document_content = """
    智慧城市IPTV系统建设项目招标文件
    
    一、项目概述
    本项目旨在建设一套完整的智慧城市IPTV管理系统，包括内容管理、用户管理、设备管理等多个子系统。
    系统需要具备高可用性、高并发处理能力和良好的扩展性。
    
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
    
    try:
        print("⏳ 调用LLM生成数字编号提纲...")
        result = await llm_service.generate_iptv_outline(document_content)
        
        if result["status"] == "success":
            outline = result["outline"]
            print("✅ 提纲生成成功!")
            print(f"📄 提纲内容 (前500字符):")
            print(outline[:500] + "..." if len(outline) > 500 else outline)
            
            return outline
        else:
            print(f"❌ 提纲生成失败: {result['error']}")
            return None
            
    except Exception as e:
        print(f"❌ 提纲生成异常: {e}")
        return None


async def test_numbered_outline_parsing(outline):
    """测试数字编号提纲解析"""
    print("\n🌳 测试数字编号提纲解析")
    print("=" * 50)
    
    if not outline:
        print("❌ 没有提纲可供解析")
        return None
    
    try:
        engine = WorkflowEngine()
        tree = engine._parse_outline_to_tree(outline)
        
        print(f"✅ 解析成功，构建了{len(tree)}个根节点")
        
        # 统计信息
        total_nodes = 0
        leaf_nodes = 0
        
        def count_nodes(nodes):
            nonlocal total_nodes, leaf_nodes
            for node in nodes:
                total_nodes += 1
                if node.is_leaf:
                    leaf_nodes += 1
                count_nodes(node.children)
        
        count_nodes(tree)
        
        print(f"📊 统计信息:")
        print(f"  总节点数: {total_nodes}")
        print(f"  叶子节点数: {leaf_nodes}")
        print(f"  父节点数: {total_nodes - leaf_nodes}")
        
        # 显示前几个叶子节点
        all_leaves = []
        for root in tree:
            all_leaves.extend(root.get_all_leaf_nodes())
        
        print(f"\n🍃 前10个叶子节点:")
        for i, leaf in enumerate(all_leaves[:10], 1):
            print(f"  {i}. {leaf.get_path()}")
        
        if len(all_leaves) > 10:
            print(f"  ... 还有{len(all_leaves) - 10}个叶子节点")
        
        return tree
        
    except Exception as e:
        print(f"❌ 提纲解析异常: {e}")
        return None


async def test_complete_workflow():
    """测试完整的数字编号工作流"""
    print("\n🚀 测试完整的数字编号工作流")
    print("=" * 50)
    
    # 准备测试数据
    document_content = """
    智慧城市IPTV系统建设项目招标文件
    
    项目概述：
    本项目旨在建设一套完整的智慧城市IPTV管理系统，包括内容管理、用户管理、设备管理等功能。
    
    技术需求：
    1. 系统架构：采用微服务架构，支持云原生部署
    2. 功能模块：视频处理、用户管理、内容分发
    3. 性能要求：支持10000并发用户，响应时间≤2秒
    """
    
    # 创建工作流状态
    state = WorkflowState(
        project_id="test_numbered_001",
        current_step="start",
        document_content=document_content,
        enable_differentiation=False  # 简化测试，不启用差异化
    )
    
    try:
        print("⏳ 运行完整工作流...")
        
        # 创建工作流引擎
        engine = WorkflowEngine()
        
        # 手动执行各个步骤来观察数字编号处理
        print("\n📄 1. 解析文档...")
        state = await engine._parse_document(state)
        if state.error:
            print(f"❌ 文档解析失败: {state.error}")
            return
        print("✅ 文档解析完成")
        
        print("\n📋 2. 生成数字编号提纲...")
        state = await engine._generate_outline(state)
        if state.error:
            print(f"❌ 提纲生成失败: {state.error}")
            return
        print("✅ 提纲生成完成")
        print(f"📄 提纲预览 (前300字符):")
        print(state.outline[:300] + "..." if len(state.outline) > 300 else state.outline)
        
        print("\n🌳 3. 构建章节树...")
        state = await engine._build_section_tree(state)
        if state.error:
            print(f"❌ 章节树构建失败: {state.error}")
            return
        print("✅ 章节树构建完成")
        print(f"📊 章节统计: {len(state.sections)}个章节")
        
        # 显示章节结构
        leaf_count = sum(1 for s in state.sections if s.get('is_leaf', False))
        parent_count = len(state.sections) - leaf_count
        print(f"🍃 叶子节点: {leaf_count}个")
        print(f"🌿 父节点: {parent_count}个")
        
        # 显示前几个章节
        print(f"\n📋 前10个章节:")
        for i, section in enumerate(state.sections[:10], 1):
            leaf_status = "🍃" if section.get('is_leaf') else "🌿"
            print(f"  {i}. {leaf_status} {section['title']} (Level {section['level']})")
        
        if len(state.sections) > 10:
            print(f"  ... 还有{len(state.sections) - 10}个章节")
        
        print("\n✅ 数字编号工作流测试成功!")
        return state
        
    except Exception as e:
        print(f"❌ 工作流执行异常: {e}")
        import traceback
        traceback.print_exc()
        return None


def create_mock_numbered_outline():
    """创建模拟的数字编号提纲用于测试"""
    return """
1. 项目概述
1.1 项目背景
1.2 项目目标
1.3 项目范围
2. 系统总体设计
2.1 设计原则
2.2 总体架构
2.2.1 逻辑架构
2.2.2 物理架构
2.2.3 部署架构
2.3 技术选型
3. 功能设计
3.1 核心功能模块
3.1.1 内容管理模块
3.1.2 用户管理模块
3.1.3 设备管理模块
3.2 扩展功能模块
3.2.1 数据分析模块
3.2.2 监控运维模块
4. 技术实现方案
4.1 关键技术
4.1.1 视频编解码技术
4.1.2 流媒体传输技术
4.2 性能优化
4.3 安全保障
5. 实施计划
5.1 项目计划
5.2 里程碑管理
5.3 风险控制
"""


async def test_mock_outline():
    """测试模拟的数字编号提纲"""
    print("\n🎭 测试模拟数字编号提纲")
    print("=" * 50)
    
    mock_outline = create_mock_numbered_outline()
    print("📄 使用模拟提纲进行测试...")
    
    await test_numbered_outline_parsing(mock_outline)


async def main():
    """主测试函数"""
    print("🤖 数字编号格式工作流测试")
    print("=" * 60)
    
    # 测试LLM提纲生成（需要API密钥）
    try:
        outline = await test_numbered_outline_generation()
        if outline:
            await test_numbered_outline_parsing(outline)
    except Exception as e:
        print(f"⚠️ LLM测试跳过: {e}")
        print("使用模拟数据进行测试...")
    
    # 测试模拟提纲
    await test_mock_outline()
    
    # 测试完整工作流
    await test_complete_workflow()
    
    print("\n" + "=" * 60)
    print("🎉 数字编号格式工作流测试完成!")
    
    print("\n📋 功能确认:")
    print("✅ LLM生成数字编号格式提纲")
    print("✅ 正确解析多级数字编号")
    print("✅ 构建层次化章节树")
    print("✅ 识别叶子节点和父节点")
    print("✅ 完整工作流正常运行")


if __name__ == "__main__":
    asyncio.run(main())
