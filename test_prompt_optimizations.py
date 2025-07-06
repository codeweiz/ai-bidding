#!/usr/bin/env python3
"""
测试Prompt优化和TOML配置功能
"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).parent))

from backend.services.config_manager import config_manager
from backend.services.llm_service import llm_service


def test_config_manager_toml_support():
    """测试配置管理器的TOML支持"""
    print("\n🔧 测试1: 配置管理器TOML支持")
    print("=" * 50)
    
    try:
        # 测试TOML配置加载
        if Path("config/dynamic_config.toml").exists():
            print("✅ TOML配置文件存在")
            
            # 测试读取配置
            llm_config = config_manager.get_llm_config()
            print(f"✅ LLM配置读取成功: temperature={llm_config.get('temperature')}")
            
            # 测试读取优化后的prompt
            iptv_prompt = config_manager.get_prompt("iptv_expert_prompt")
            if "避免涉及具体技术栈名称" in iptv_prompt:
                print("✅ 优化后的IPTV专家prompt加载成功")
            else:
                print("❌ IPTV专家prompt未正确加载")
            
            outline_prompt = config_manager.get_prompt("outline_generation_prompt")
            if "规范的数字编号格式" in outline_prompt:
                print("✅ 优化后的提纲生成prompt加载成功")
            else:
                print("❌ 提纲生成prompt未正确加载")
            
            parent_prompt = config_manager.get_prompt("parent_summary_prompt")
            if "高质量的总结性内容" in parent_prompt:
                print("✅ 优化后的父节点总结prompt加载成功")
            else:
                print("❌ 父节点总结prompt未正确加载")
            
            return True
        else:
            print("❌ TOML配置文件不存在")
            return False
            
    except Exception as e:
        print(f"❌ 配置管理器测试失败: {e}")
        return False


async def test_optimized_prompts():
    """测试优化后的prompt效果"""
    print("\n📝 测试2: 优化后的Prompt效果")
    print("=" * 50)
    
    try:
        # 测试文档内容
        test_document = """
        广东IPTV集成播控分平台首页可视化编辑工具三期工程招标文件
        
        项目概述：
        本项目旨在建设IPTV集成播控分平台的可视化编辑工具，支持EPG改版和运营管理。
        
        技术要求：
        1. 支持Vue.js前端框架开发
        2. 采用Spring Boot微服务架构
        3. 使用Redis缓存技术
        4. 支持1500万用户并发访问
        5. 响应时间不超过200ms
        
        功能需求：
        1. EPG改版：包括功能页、列表页、详情页、专区页
        2. 可视化编排：支持拖拽式操作
        3. 自动化运营：减少人工编排工作量
        """
        
        # 测试提纲生成
        print("📋 测试提纲生成...")
        outline_result = await llm_service.generate_iptv_outline(test_document)
        
        if outline_result["status"] == "success":
            outline = outline_result["outline"]
            print("✅ 提纲生成成功")
            
            # 检查提纲质量
            if "1." in outline and "1.1" in outline:
                print("✅ 提纲格式正确（数字编号）")
            else:
                print("❌ 提纲格式不正确")
            
            if "售后" not in outline and "验收" not in outline and "质量保障" not in outline:
                print("✅ 提纲避免了通用章节")
            else:
                print("❌ 提纲包含了不应有的通用章节")
            
            print(f"📄 生成的提纲预览:\n{outline[:500]}...")
        else:
            print(f"❌ 提纲生成失败: {outline_result.get('error')}")
            return False
        
        # 测试章节内容生成
        print("\n📖 测试章节内容生成...")
        content_result = await llm_service.generate_iptv_section_content(
            section_title="系统总体架构",
            section_path="2.1",
            document_content=test_document
        )
        
        if content_result["status"] == "success":
            content = content_result["content"]
            print("✅ 章节内容生成成功")
            
            # 检查内容质量
            if "Vue.js" not in content and "Spring Boot" not in content and "Redis" not in content:
                print("✅ 内容避免了具体技术栈名称")
            else:
                print("❌ 内容包含了具体技术栈名称")
            
            if "前端框架" in content or "微服务架构" in content or "缓存技术" in content:
                print("✅ 内容使用了通用技术描述")
            else:
                print("❌ 内容未使用通用技术描述")
            
            if len(content) >= 800 and len(content) <= 2000:
                print(f"✅ 内容长度合适: {len(content)}字")
            else:
                print(f"❌ 内容长度不合适: {len(content)}字")
            
            print(f"📄 生成的内容预览:\n{content[:300]}...")
        else:
            print(f"❌ 章节内容生成失败: {content_result.get('error')}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Prompt测试失败: {e}")
        return False


def test_config_export_import():
    """测试配置导出导入功能"""
    print("\n💾 测试3: 配置导出导入功能")
    print("=" * 50)
    
    try:
        # 测试导出TOML格式
        toml_file = config_manager.export_config(format_type="toml")
        if Path(toml_file).exists():
            print("✅ TOML格式配置导出成功")
        else:
            print("❌ TOML格式配置导出失败")
            return False
        
        # 测试导出JSON格式
        json_file = config_manager.export_config(format_type="json")
        if Path(json_file).exists():
            print("✅ JSON格式配置导出成功")
        else:
            print("❌ JSON格式配置导出失败")
            return False
        
        # 清理测试文件
        Path(toml_file).unlink(missing_ok=True)
        Path(json_file).unlink(missing_ok=True)
        
        return True
        
    except Exception as e:
        print(f"❌ 配置导出导入测试失败: {e}")
        return False


async def main():
    """主测试函数"""
    print("🧪 AI投标系统Prompt优化测试")
    print("=" * 60)
    
    # 运行所有测试
    tests = [
        ("配置管理器TOML支持", test_config_manager_toml_support),
        ("优化后的Prompt效果", test_optimized_prompts),
        ("配置导出导入功能", test_config_export_import),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n🔍 执行测试: {test_name}")
        try:
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
                result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ 测试 {test_name} 执行异常: {e}")
            results.append((test_name, False))
    
    # 输出测试结果
    print("\n📊 测试结果汇总")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n总计: {passed}/{total} 个测试通过")
    
    if passed == total:
        print("🎉 所有优化功能测试通过！")
        return True
    else:
        print("⚠️ 部分测试失败，请检查相关功能")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
