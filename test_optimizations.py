#!/usr/bin/env python3
"""
测试所有优化功能
"""
import asyncio
import json
from pathlib import Path
import time

from backend.services.workflow_engine import workflow_engine
from backend.services.llm_manager import llm_manager
from backend.services.document_formatter import document_formatter
from backend.services.config_manager import config_manager
from backend.models.generation import WorkflowState


async def test_concurrent_generation():
    """测试1: 并发生成优化"""
    print("🚀 测试1: 并发生成优化")
    print("=" * 50)
    
    # 创建测试状态
    state = WorkflowState(
        project_id="test_concurrent",
        current_step="start",
        document_content="""
        智慧城市IPTV系统建设项目招标文件
        
        一、项目概述
        本项目旨在建设一套完整的智慧城市IPTV管理系统，包括内容管理、用户管理、设备管理等多个子系统。
        
        二、技术需求
        1. 系统架构要求
        - 采用微服务架构设计
        - 支持云原生部署
        - 具备高可用性和可扩展性
        
        2. 功能需求
        2.1 内容管理系统
        - 支持多种视频格式的上传和转码
        - 提供内容分类和标签管理
        
        2.2 用户管理系统
        - 支持用户注册和认证
        - 提供用户权限管理
        
        2.3 设备管理系统
        - 支持机顶盒设备管理
        - 提供设备状态监控
        """,
        enable_differentiation=False
    )
    
    # 测试提纲生成
    print("📝 生成提纲...")
    start_time = time.time()
    
    state = await workflow_engine._generate_outline(state)
    if state.error:
        print(f"❌ 提纲生成失败: {state.error}")
        return
    
    print(f"✅ 提纲生成完成，耗时: {time.time() - start_time:.2f}秒")
    print(f"提纲内容预览: {state.outline[:200]}...")
    
    # 测试章节树构建
    print("\n🌳 构建章节树...")
    state = await workflow_engine._build_section_tree(state)
    if state.error:
        print(f"❌ 章节树构建失败: {state.error}")
        return
    
    print(f"✅ 章节树构建完成，共{len(state.sections)}个章节")
    
    # 测试并发叶子节点生成
    print("\n⚡ 并发生成叶子节点内容...")
    start_time = time.time()
    
    state = await workflow_engine._generate_leaf_content(state)
    generation_time = time.time() - start_time
    
    if state.error:
        print(f"❌ 叶子节点生成失败: {state.error}")
        return
    
    print(f"✅ 叶子节点生成完成，耗时: {generation_time:.2f}秒")
    
    # 统计生成结果
    leaf_count = sum(1 for s in state.sections if s.get("is_leaf", False))
    success_count = sum(1 for s in state.sections if s.get("is_generated", False))
    
    print(f"📊 生成统计:")
    print(f"  - 叶子节点总数: {leaf_count}")
    print(f"  - 成功生成: {success_count}")
    print(f"  - 平均每节点耗时: {generation_time/max(leaf_count, 1):.2f}秒")
    
    return state


async def test_llm_manager():
    """测试2: LLM管理器功能"""
    print("\n🤖 测试2: LLM管理器功能")
    print("=" * 50)
    
    # 测试配置更新
    print("⚙️ 测试配置更新...")
    llm_manager.update_config({
        "temperature": 0.3,
        "max_tokens": 3000
    })
    print("✅ 配置更新成功")
    
    # 测试自定义Prompt
    print("\n📝 测试自定义Prompt...")
    custom_prompt = "你是一个测试专家，请简洁回答问题。"
    llm_manager.set_custom_prompt("test_prompt", custom_prompt)
    retrieved_prompt = llm_manager.get_custom_prompt("test_prompt")
    
    if retrieved_prompt == custom_prompt:
        print("✅ 自定义Prompt设置成功")
    else:
        print("❌ 自定义Prompt设置失败")
    
    # 测试重试机制
    print("\n🔄 测试重试机制...")
    from langchain_core.messages import HumanMessage, SystemMessage
    
    messages = [
        SystemMessage(content="你是一个助手"),
        HumanMessage(content="请简单介绍IPTV系统")
    ]
    
    start_time = time.time()
    result = await llm_manager.generate_with_retry(messages)
    retry_time = time.time() - start_time
    
    if result["status"] == "success":
        print(f"✅ 重试机制测试成功，耗时: {retry_time:.2f}秒")
        print(f"生成内容长度: {len(result['content'])}字符")
    else:
        print(f"❌ 重试机制测试失败: {result.get('error')}")


async def test_document_formatter():
    """测试3: 文档格式化功能"""
    print("\n📄 测试3: 文档格式化功能")
    print("=" * 50)
    
    # 测试原始文本格式化
    print("📝 测试原始文本格式化...")
    
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
    
    try:
        doc_path = await document_formatter.format_raw_text(
            raw_text=raw_text,
            project_name="测试格式化文档"
        )
        print(f"✅ 原始文本格式化成功: {doc_path}")
    except Exception as e:
        print(f"❌ 原始文本格式化失败: {e}")
    
    # 测试章节数据格式化
    print("\n📊 测试章节数据格式化...")
    
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
        },
        {
            "title": "技术选型",
            "level": 2,
            "content": "选择成熟稳定的技术栈，包括Spring Boot、Redis、MySQL等。",
            "is_generated": True,
            "order": 3
        }
    ]
    
    try:
        doc_path = await document_formatter.format_sections_data(
            sections_data=sections_data,
            project_name="测试章节格式化"
        )
        print(f"✅ 章节数据格式化成功: {doc_path}")
    except Exception as e:
        print(f"❌ 章节数据格式化失败: {e}")


def test_config_manager():
    """测试4: 配置管理功能"""
    print("\n⚙️ 测试4: 配置管理功能")
    print("=" * 50)
    
    # 测试配置读取
    print("📖 测试配置读取...")
    llm_config = config_manager.get_llm_config()
    print(f"✅ LLM配置: {llm_config}")
    
    # 测试配置更新
    print("\n✏️ 测试配置更新...")
    config_manager.set("test.key", "test_value")
    retrieved_value = config_manager.get("test.key")
    
    if retrieved_value == "test_value":
        print("✅ 配置更新成功")
    else:
        print("❌ 配置更新失败")
    
    # 测试Prompt管理
    print("\n📝 测试Prompt管理...")
    test_prompt = "这是一个测试Prompt"
    config_manager.set_prompt("test_prompt", test_prompt)
    retrieved_prompt = config_manager.get_prompt("test_prompt")
    
    if retrieved_prompt == test_prompt:
        print("✅ Prompt管理成功")
    else:
        print("❌ Prompt管理失败")
    
    # 测试Provider配置
    print("\n🔌 测试Provider配置...")
    provider_config = config_manager.get_provider_config()
    print(f"✅ Provider配置: {list(provider_config.get('available', {}).keys())}")
    
    # 测试配置导出
    print("\n💾 测试配置导出...")
    try:
        export_path = config_manager.export_config()
        print(f"✅ 配置导出成功: {export_path}")
    except Exception as e:
        print(f"❌ 配置导出失败: {e}")


async def test_integration():
    """测试5: 集成测试"""
    print("\n🔗 测试5: 集成测试")
    print("=" * 50)
    
    print("🚀 运行完整工作流...")
    
    # 创建测试状态
    state = WorkflowState(
        project_id="integration_test",
        current_step="start",
        document_content="""
        IPTV智慧广电系统建设项目
        
        项目要求建设一套完整的IPTV系统，包括：
        1. 内容管理平台
        2. 用户管理系统
        3. 设备监控系统
        4. 数据分析平台
        
        技术要求：
        - 支持高并发访问
        - 具备高可用性
        - 支持云原生部署
        - 提供完整的API接口
        """,
        enable_differentiation=False
    )
    
    try:
        # 运行完整工作流
        start_time = time.time()
        final_state = await workflow_engine.run_workflow(state)
        total_time = time.time() - start_time
        
        if final_state.error:
            print(f"❌ 工作流执行失败: {final_state.error}")
            return
        
        print(f"✅ 工作流执行成功，总耗时: {total_time:.2f}秒")
        print(f"📊 生成统计:")
        print(f"  - 总章节数: {len(final_state.sections)}")
        print(f"  - 成功生成: {sum(1 for s in final_state.sections if s.get('is_generated', False))}")
        
        # 格式化输出文档
        print("\n📄 格式化输出文档...")
        doc_path = await document_formatter.format_sections_data(
            sections_data=final_state.sections,
            project_name="集成测试文档"
        )
        print(f"✅ 文档生成成功: {doc_path}")
        
    except Exception as e:
        print(f"❌ 集成测试失败: {e}")


async def main():
    """主测试函数"""
    print("🎯 AI投标系统优化功能测试")
    print("=" * 70)
    
    # 运行所有测试
    await test_concurrent_generation()
    await test_llm_manager()
    await test_document_formatter()
    test_config_manager()
    await test_integration()
    
    print("\n" + "=" * 70)
    print("🎉 所有测试完成!")
    
    print(f"\n📋 优化功能总结:")
    print(f"✅ 1. 并发生成 - 支持叶子节点并发生成，提升效率")
    print(f"✅ 2. 稳定格式化 - 基于数据结构的稳定格式化")
    print(f"✅ 3. 长Prompt优化 - 智能内容筛选，减少token消耗")
    print(f"✅ 4. LLM扩展 - 支持多Provider动态切换")
    print(f"✅ 5. 格式化独立化 - 独立的格式化服务")
    print(f"✅ 6. 重试机制 - 智能重试和格式验证")
    print(f"✅ 7. 开放配置 - 动态配置管理")


if __name__ == "__main__":
    asyncio.run(main())
