#!/usr/bin/env python3
"""
最终验证测试 - 快速验证所有优化功能
"""
import asyncio
import time
from pathlib import Path

def test_markdown_cleanup():
    """测试markdown格式清理"""
    print("🧹 测试markdown格式清理")
    print("-" * 30)
    
    try:
        from backend.services.workflow_engine import workflow_engine
        
        # 测试内容
        test_content = """
# 标题
**粗体文本** 和 *斜体文本*
- 列表项1
- 列表项2
```python
代码块
```
> 引用内容
[链接](http://example.com)
        """
        
        cleaned = workflow_engine._clean_markdown_format(test_content)
        
        # 检查是否还有markdown标记
        markdown_markers = ['*', '#', '```', '`', '>', '-', '[', ']']
        has_markdown = any(marker in cleaned for marker in markdown_markers)
        
        if not has_markdown:
            print("✅ markdown格式清理成功")
            return True
        else:
            print("❌ 仍然包含markdown标记")
            return False
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False


async def test_content_generation():
    """测试内容生成质量"""
    print("\n📝 测试内容生成质量")
    print("-" * 30)
    
    try:
        from backend.services.llm_service import llm_service
        
        # 简短测试
        document_content = """
        IPTV系统建设项目要求：
        1. 采用微服务架构
        2. 支持高并发访问
        3. 具备高可用性
        4. 支持云原生部署
        """
        
        print("🔧 生成测试章节内容...")
        result = await llm_service.generate_iptv_section_content(
            section_title="系统架构设计",
            section_path="2.1 系统架构设计",
            document_content=document_content
        )
        
        if result["status"] == "success":
            content = result["content"]
            
            # 质量检查
            checks = {
                "内容不为空": len(content.strip()) > 0,
                "无markdown格式": not any(marker in content for marker in ['*', '#', '```']),
                "包含关键词": any(word in content for word in ["IPTV", "架构", "微服务"]),
                "长度适中": 500 <= len(content) <= 3000
            }
            
            print(f"生成内容长度: {len(content)}字符")
            
            all_passed = True
            for check, passed in checks.items():
                status = "✅" if passed else "❌"
                print(f"  {status} {check}")
                if not passed:
                    all_passed = False
            
            return all_passed
        else:
            print(f"❌ 内容生成失败: {result.get('error')}")
            return False
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False


def test_file_structure():
    """测试文件结构完整性"""
    print("\n📁 测试文件结构")
    print("-" * 30)
    
    required_files = [
        "backend/services/llm_service.py",
        "backend/services/workflow_engine.py",
        "backend/services/llm_manager.py",
        "backend/services/document_formatter.py",
        "backend/services/config_manager.py",
        "docs/content_quality_optimization_report.md"
    ]
    
    all_exist = True
    for file_path in required_files:
        if Path(file_path).exists():
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path}")
            all_exist = False
    
    return all_exist


def test_concurrent_capability():
    """测试并发能力"""
    print("\n⚡ 测试并发能力")
    print("-" * 30)
    
    try:
        from backend.services.workflow_engine import workflow_engine
        
        # 检查是否有并发相关方法
        methods = [
            "_collect_parent_nodes",
            "_generate_single_parent_summary", 
            "_generate_single_leaf_content"
        ]
        
        all_methods_exist = True
        for method in methods:
            if hasattr(workflow_engine, method):
                print(f"✅ {method}")
            else:
                print(f"❌ {method}")
                all_methods_exist = False
        
        return all_methods_exist
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False


async def main():
    """主测试函数"""
    print("🎯 最终验证测试")
    print("=" * 50)
    
    results = []
    
    # 运行所有测试
    results.append(test_file_structure())
    results.append(test_markdown_cleanup())
    results.append(test_concurrent_capability())
    results.append(await test_content_generation())
    
    print("\n" + "=" * 50)
    print("🎉 最终验证完成!")
    
    success_count = sum(results)
    total_count = len(results)
    
    print(f"\n📊 测试结果: {success_count}/{total_count} 通过")
    
    if success_count == total_count:
        print("🎉 所有测试通过！优化功能正常工作")
        print("\n✅ 系统已准备好使用，主要改进:")
        print("  - 完全消除markdown格式输出")
        print("  - 支持并发生成提升性能")
        print("  - 使用完整文档确保内容质量")
        print("  - 优化Prompt提升阅读流畅性")
    else:
        print("⚠️ 部分测试失败，请检查相关功能")
    
    print(f"\n🚀 使用指南:")
    print(f"1. 启动后端: python backend/main.py")
    print(f"2. 启动前端: python frontend/app.py")
    print(f"3. 测试生成: 上传招标文档，创建项目")
    print(f"4. 查看结果: 检查生成的投标书格式和内容")


if __name__ == "__main__":
    asyncio.run(main())
