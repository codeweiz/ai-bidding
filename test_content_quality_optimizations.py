#!/usr/bin/env python3
"""
测试内容质量优化功能
"""
import asyncio
import time
from pathlib import Path

from backend.services.workflow_engine import workflow_engine
from backend.services.llm_service import llm_service
from backend.services.document_formatter import document_formatter
from backend.models.generation import WorkflowState


async def test_markdown_cleanup():
    """测试markdown格式清理功能"""
    print("🧹 测试markdown格式清理功能")
    print("=" * 50)
    
    # 测试内容包含各种markdown格式
    test_content = """
# 系统架构设计

## 总体架构

本系统采用**微服务架构**设计，具有以下特点：

- 高可用性
- 可扩展性
- *灵活部署*

### 技术选型

1. 前端框架：React
2. 后端框架：Spring Boot
3. 数据库：MySQL

```mermaid
graph TD
    A[用户层] --> B[网关层]
    B --> C[业务服务层]
```

> 注意：系统需要满足高并发要求

---

更多详细信息请参考[技术文档](http://example.com)。

`配置参数`需要根据实际情况调整。
    """
    
    # 清理markdown格式
    cleaned_content = workflow_engine._clean_markdown_format(test_content)
    
    print("原始内容（包含markdown格式）:")
    print(test_content[:200] + "...")
    
    print("\n清理后内容（纯文本）:")
    print(cleaned_content[:200] + "...")
    
    # 检查是否还有markdown标记
    markdown_markers = ['*', '#', '```', '`', '>', '-', '[', ']']
    has_markdown = any(marker in cleaned_content for marker in markdown_markers)
    
    if has_markdown:
        print("❌ 仍然包含markdown标记")
        return False
    else:
        print("✅ markdown格式清理成功")
        return True


async def test_full_document_content():
    """测试完整文档内容传递"""
    print("\n📄 测试完整文档内容传递")
    print("=" * 50)
    
    # 创建测试文档内容
    full_document = """
    智慧城市IPTV系统建设项目招标文件
    
    一、项目概述
    本项目旨在建设一套完整的智慧城市IPTV管理系统，包括内容管理、用户管理、设备管理等多个子系统。
    系统需要具备高可用性、高并发处理能力和良好的扩展性。
    
    二、技术需求
    1. 系统架构要求
    - 采用微服务架构设计
    - 支持云原生部署
    - 具备高可用性和可扩展性
    - 系统可用性要求达到99.9%以上
    
    2. 功能需求
    2.1 内容管理系统
    - 支持多种视频格式的上传和转码
    - 提供内容分类和标签管理
    - 支持内容审核和发布流程
    - 提供内容统计和分析功能
    
    2.2 用户管理系统
    - 支持用户注册和认证
    - 提供用户权限管理
    - 支持用户行为分析
    - 提供用户服务和支持
    
    2.3 设备管理系统
    - 支持机顶盒设备管理
    - 提供设备状态监控
    - 支持远程设备控制
    - 提供设备故障诊断
    
    三、性能指标
    - 系统响应时间：≤2秒
    - 并发用户数：≥10000
    - 视频流处理能力：≥1000路并发
    - 存储容量：≥100TB
    - 网络带宽：≥10Gbps
    
    四、技术标准
    - 遵循国家广电总局相关技术标准
    - 支持H.264/H.265视频编码
    - 符合IPTV行业标准
    - 支持IPv6协议
    - 遵循信息安全等级保护要求
    """
    
    print(f"测试文档长度: {len(full_document)}字符")
    
    # 测试单个章节内容生成
    print("\n🔧 测试章节内容生成...")
    start_time = time.time()
    
    result = await llm_service.generate_iptv_section_content(
        section_title="系统架构设计",
        section_path="2. 系统设计 > 2.1 系统架构设计",
        document_content=full_document
    )
    
    generation_time = time.time() - start_time
    
    if result["status"] == "success":
        content = result["content"]
        print(f"✅ 章节内容生成成功，耗时: {generation_time:.2f}秒")
        print(f"生成内容长度: {len(content)}字符")
        print(f"内容预览: {content[:300]}...")
        
        # 检查内容质量
        quality_checks = {
            "包含招标需求关键词": any(keyword in content for keyword in ["IPTV", "微服务", "高可用", "云原生"]),
            "内容长度适中": 800 <= len(content) <= 2500,
            "无markdown格式": not any(marker in content for marker in ['*', '#', '```', '`']),
            "无mermaid代码": "mermaid" not in content.lower(),
            "逻辑结构清晰": "架构" in content and "设计" in content
        }
        
        print(f"\n📊 内容质量检查:")
        for check, passed in quality_checks.items():
            status = "✅" if passed else "❌"
            print(f"  {status} {check}")
        
        return all(quality_checks.values())
    else:
        print(f"❌ 章节内容生成失败: {result.get('error')}")
        return False


async def test_parent_summary_quality():
    """测试父节点总结质量"""
    print("\n📝 测试父节点总结质量")
    print("=" * 50)
    
    # 模拟子章节内容
    children_content = """
    章节：系统架构设计
    本系统采用微服务架构设计，支持云原生部署。系统分为前端展示层、业务逻辑层、数据访问层和基础设施层。各层之间通过标准接口进行通信，确保系统的模块化和可维护性。系统具备高可用性和可扩展性，能够满足大规模并发访问需求。
    
    章节：技术选型
    前端采用React框架，后端使用Spring Boot微服务架构。数据库选择MySQL集群，缓存使用Redis。消息队列采用RabbitMQ，容器化部署使用Docker和Kubernetes。监控系统使用Prometheus和Grafana。
    
    章节：部署方案
    系统支持云原生部署，采用容器化技术。通过Kubernetes进行容器编排和管理。支持自动扩缩容，确保系统在高负载情况下的稳定运行。部署环境支持公有云、私有云和混合云模式。
    """
    
    document_content = """
    IPTV系统建设项目要求采用先进的技术架构，确保系统的高可用性、可扩展性和安全性。
    系统需要支持大规模并发访问，处理能力要求达到10000并发用户。
    """
    
    print("🔧 测试父节点总结生成...")
    start_time = time.time()
    
    result = await llm_service.generate_parent_summary(
        parent_title="系统总体设计",
        parent_path="2. 系统总体设计",
        children_content=children_content,
        document_content=document_content
    )
    
    generation_time = time.time() - start_time
    
    if result["status"] == "success":
        content = result["content"]
        print(f"✅ 父节点总结生成成功，耗时: {generation_time:.2f}秒")
        print(f"生成内容长度: {len(content)}字符")
        print(f"内容预览: {content[:300]}...")
        
        # 检查总结质量
        quality_checks = {
            "内容长度适中": 400 <= len(content) <= 1200,
            "无markdown格式": not any(marker in content for marker in ['*', '#', '```', '`']),
            "包含总结性语言": any(word in content for word in ["总体", "整体", "综合", "概述"]),
            "体现逻辑关系": any(word in content for word in ["基于", "通过", "确保", "实现"]),
            "阅读流畅": len(content.split('。')) >= 3  # 至少3个句子
        }
        
        print(f"\n📊 总结质量检查:")
        for check, passed in quality_checks.items():
            status = "✅" if passed else "❌"
            print(f"  {status} {check}")
        
        return all(quality_checks.values())
    else:
        print(f"❌ 父节点总结生成失败: {result.get('error')}")
        return False


async def test_concurrent_parent_generation():
    """测试并发父节点生成"""
    print("\n⚡ 测试并发父节点生成")
    print("=" * 50)
    
    # 创建测试状态
    state = WorkflowState(
        project_id="concurrent_parent_test",
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
    
    # 生成提纲和构建章节树
    print("📝 生成提纲...")
    state = await workflow_engine._generate_outline(state)
    if state.error:
        print(f"❌ 提纲生成失败: {state.error}")
        return False
    
    print("🌳 构建章节树...")
    state = await workflow_engine._build_section_tree(state)
    if state.error:
        print(f"❌ 章节树构建失败: {state.error}")
        return False
    
    # 模拟叶子节点已生成内容
    print("🔧 模拟叶子节点内容...")
    for root_node in state.section_tree:
        for leaf_node in root_node.get_all_leaf_nodes():
            leaf_node.content = f"这是{leaf_node.title}的详细技术方案内容。内容包含了具体的技术实现方案、架构设计和功能描述。"
            leaf_node.is_generated = True
    
    # 测试并发父节点生成
    print("⚡ 测试并发父节点生成...")
    start_time = time.time()
    
    state = await workflow_engine._generate_parent_summaries(state)
    generation_time = time.time() - start_time
    
    if state.error:
        print(f"❌ 父节点生成失败: {state.error}")
        return False
    
    # 统计结果
    parent_count = sum(1 for s in state.sections if not s.get("is_leaf", True))
    success_count = sum(1 for s in state.sections if not s.get("is_leaf", True) and s.get("is_generated", False))
    
    print(f"✅ 并发父节点生成完成，耗时: {generation_time:.2f}秒")
    print(f"📊 生成统计:")
    print(f"  - 父节点总数: {parent_count}")
    print(f"  - 成功生成: {success_count}")
    print(f"  - 平均每节点耗时: {generation_time/max(parent_count, 1):.2f}秒")
    
    return success_count > 0


async def main():
    """主测试函数"""
    print("🎯 内容质量优化功能测试")
    print("=" * 70)
    
    results = []
    
    # 运行所有测试
    results.append(await test_markdown_cleanup())
    results.append(await test_full_document_content())
    results.append(await test_parent_summary_quality())
    results.append(await test_concurrent_parent_generation())
    
    print("\n" + "=" * 70)
    print("🎉 内容质量优化测试完成!")
    
    success_count = sum(results)
    total_count = len(results)
    
    print(f"\n📊 测试结果: {success_count}/{total_count} 通过")
    
    if success_count == total_count:
        print("🎉 所有测试通过！内容质量优化功能正常工作")
    else:
        print("⚠️ 部分测试失败，请检查相关功能")
    
    print(f"\n📋 优化效果总结:")
    print(f"✅ 1. 格式清理 - 自动移除markdown格式标记")
    print(f"✅ 2. 完整内容 - 使用完整招标文档提升内容质量")
    print(f"✅ 3. 并发加速 - 父节点生成支持并行处理")
    print(f"✅ 4. 质量提升 - 优化Prompt确保内容专业流畅")
    
    print(f"\n🚀 主要改进:")
    print(f"- 严格禁止markdown格式输出")
    print(f"- 减少mermaid代码生成")
    print(f"- 使用完整文档内容确保质量")
    print(f"- 并行生成父节点提升速度")
    print(f"- 优化Prompt提升阅读流畅性")


if __name__ == "__main__":
    asyncio.run(main())
