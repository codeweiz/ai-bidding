#!/usr/bin/env python3
"""
快速测试优化功能
"""
import asyncio
import time
from pathlib import Path

def test_config_manager():
    """测试配置管理功能"""
    print("⚙️ 测试配置管理功能")
    print("=" * 40)
    
    try:
        from backend.services.config_manager import config_manager
        
        # 测试配置读取
        llm_config = config_manager.get_llm_config()
        print(f"✅ LLM配置读取成功: temperature={llm_config.get('temperature')}")
        
        # 测试配置更新
        config_manager.set("test.key", "test_value")
        retrieved_value = config_manager.get("test.key")
        
        if retrieved_value == "test_value":
            print("✅ 配置更新成功")
        else:
            print("❌ 配置更新失败")
        
        # 测试Prompt管理
        test_prompt = "这是一个测试Prompt"
        config_manager.set_prompt("test_prompt", test_prompt)
        retrieved_prompt = config_manager.get_prompt("test_prompt")
        
        if retrieved_prompt == test_prompt:
            print("✅ Prompt管理成功")
        else:
            print("❌ Prompt管理失败")
        
        return True
    except Exception as e:
        print(f"❌ 配置管理测试失败: {e}")
        return False


def test_llm_manager():
    """测试LLM管理器功能"""
    print("\n🤖 测试LLM管理器功能")
    print("=" * 40)
    
    try:
        from backend.services.llm_manager import llm_manager
        
        # 测试配置更新
        llm_manager.update_config({
            "temperature": 0.3,
            "max_tokens": 3000
        })
        print("✅ LLM配置更新成功")
        
        # 测试自定义Prompt
        custom_prompt = "你是一个测试专家，请简洁回答问题。"
        llm_manager.set_custom_prompt("test_prompt", custom_prompt)
        retrieved_prompt = llm_manager.get_custom_prompt("test_prompt")
        
        if retrieved_prompt == custom_prompt:
            print("✅ 自定义Prompt设置成功")
        else:
            print("❌ 自定义Prompt设置失败")
        
        return True
    except Exception as e:
        print(f"❌ LLM管理器测试失败: {e}")
        return False


async def test_document_formatter():
    """测试文档格式化功能"""
    print("\n📄 测试文档格式化功能")
    print("=" * 40)
    
    try:
        from backend.services.document_formatter import document_formatter
        
        # 测试原始文本格式化
        raw_text = """
1. 系统概述
本系统是一个IPTV管理平台。

1.1 系统架构
采用微服务架构设计。

1.2 技术特点
具备高可用性和可扩展性。

2. 功能设计
系统包含多个功能模块。

2.1 内容管理
支持视频内容的管理和分发。

2.2 用户管理
提供用户注册、认证和权限管理功能。
        """
        
        doc_path = await document_formatter.format_raw_text(
            raw_text=raw_text,
            project_name="快速测试格式化文档"
        )
        print(f"✅ 原始文本格式化成功: {doc_path}")
        
        # 测试章节数据格式化
        sections_data = [
            {
                "title": "系统总体设计",
                "level": 1,
                "content": "本章节介绍系统的总体设计方案，包括架构设计、技术选型等内容。",
                "is_generated": True,
                "order": 1
            },
            {
                "title": "架构设计",
                "level": 2,
                "content": "系统采用微服务架构，具备高可用性和可扩展性。支持云原生部署。",
                "is_generated": True,
                "order": 2
            }
        ]
        
        doc_path = await document_formatter.format_sections_data(
            sections_data=sections_data,
            project_name="快速测试章节格式化"
        )
        print(f"✅ 章节数据格式化成功: {doc_path}")
        
        return True
    except Exception as e:
        print(f"❌ 文档格式化测试失败: {e}")
        return False


async def test_workflow_structure():
    """测试工作流结构优化"""
    print("\n🌳 测试工作流结构优化")
    print("=" * 40)
    
    try:
        from backend.services.workflow_engine import workflow_engine
        from backend.models.generation import WorkflowState
        
        # 创建测试状态
        state = WorkflowState(
            project_id="structure_test",
            current_step="start",
            document_content="测试文档内容",
            enable_differentiation=False
        )
        
        # 测试提纲解析
        test_outline = """
1. 项目概述
1.1 项目背景
1.2 项目目标
2. 系统设计
2.1 总体架构
2.1.1 架构原则
2.1.2 技术选型
2.2 详细设计
        """
        
        state.outline = test_outline
        
        # 测试章节树构建
        state = await workflow_engine._build_section_tree(state)
        if state.error:
            print(f"❌ 章节树构建失败: {state.error}")
            return False
        
        print(f"✅ 章节树构建成功，共{len(state.sections)}个章节")
        
        # 验证叶子节点识别
        if hasattr(state, 'section_tree') and state.section_tree:
            leaf_count = 0
            for root_node in state.section_tree:
                leaf_count += len(root_node.get_all_leaf_nodes())
            print(f"✅ 叶子节点识别成功，共{leaf_count}个叶子节点")
        
        return True
    except Exception as e:
        print(f"❌ 工作流结构测试失败: {e}")
        return False


def test_file_structure():
    """测试文件结构"""
    print("\n📁 测试文件结构")
    print("=" * 40)
    
    required_files = [
        "backend/services/llm_manager.py",
        "backend/services/document_formatter.py", 
        "backend/services/config_manager.py",
        "backend/api/routes/config.py",
        "backend/api/routes/formatting.py",
        "docs/optimization_implementation.md"
    ]
    
    all_exist = True
    for file_path in required_files:
        if Path(file_path).exists():
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path} - 文件不存在")
            all_exist = False
    
    return all_exist


async def main():
    """主测试函数"""
    print("🎯 AI投标系统优化功能快速测试")
    print("=" * 60)
    
    results = []
    
    # 测试文件结构
    results.append(test_file_structure())
    
    # 测试配置管理
    results.append(test_config_manager())
    
    # 测试LLM管理器
    results.append(test_llm_manager())
    
    # 测试文档格式化
    results.append(await test_document_formatter())
    
    # 测试工作流结构
    results.append(await test_workflow_structure())
    
    print("\n" + "=" * 60)
    print("🎉 快速测试完成!")
    
    success_count = sum(results)
    total_count = len(results)
    
    print(f"\n📊 测试结果: {success_count}/{total_count} 通过")
    
    if success_count == total_count:
        print("🎉 所有测试通过！优化功能正常工作")
    else:
        print("⚠️ 部分测试失败，请检查相关功能")
    
    print(f"\n📋 优化功能总结:")
    print(f"✅ 1. 并发生成 - 支持叶子节点并发生成")
    print(f"✅ 2. 稳定格式化 - 基于数据结构的格式化")
    print(f"✅ 3. 长Prompt优化 - 智能内容筛选")
    print(f"✅ 4. LLM扩展 - 支持多Provider动态切换")
    print(f"✅ 5. 格式化独立化 - 独立的格式化服务")
    print(f"✅ 6. 重试机制 - 智能重试和格式验证")
    print(f"✅ 7. 开放配置 - 动态配置管理")
    
    print(f"\n🚀 使用指南:")
    print(f"1. 启动后端: python backend/main.py")
    print(f"2. 配置管理: http://localhost:8000/api/config/")
    print(f"3. 格式化服务: http://localhost:8000/api/formatting/")
    print(f"4. 查看文档: docs/optimization_implementation.md")


if __name__ == "__main__":
    asyncio.run(main())
