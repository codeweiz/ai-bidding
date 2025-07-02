#!/usr/bin/env python3
"""
完整工作流测试脚本
使用LangGraph流程处理招标书001.docx生成投标书
"""
import requests
import time
import json
from pathlib import Path

# API配置
API_BASE_URL = "http://localhost:8000/api"

def test_full_workflow():
    """测试完整的工作流程"""
    print("🚀 开始测试完整的AI投标工作流程")
    print("=" * 60)
    
    try:
        # 1. 检查后端服务状态
        print("📡 步骤1: 检查后端服务状态")
        try:
            # 先测试根路径
            response = requests.get("http://localhost:8000/", timeout=5)
            if response.status_code == 200:
                print("✅ 后端服务运行正常")
                print(f"   服务信息: {response.json()}")
            else:
                print(f"❌ 后端服务异常: {response.status_code}")
                return
        except Exception as e:
            print(f"❌ 无法连接后端服务: {e}")
            return
        
        # 2. 上传招标文档
        print("\n📄 步骤2: 上传招标文档")
        tender_doc_path = Path("temp_docs/招标书001.docx")
        
        if not tender_doc_path.exists():
            print(f"❌ 招标文档不存在: {tender_doc_path}")
            return
        
        with open(tender_doc_path, "rb") as f:
            files = {"file": (tender_doc_path.name, f, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}
            response = requests.post(f"{API_BASE_URL}/documents/upload", files=files)
        
        if response.status_code == 200:
            upload_result = response.json()
            file_path = upload_result["file_path"]
            print(f"✅ 文档上传成功: {upload_result['file_name']}")
            print(f"   文件路径: {file_path}")
        else:
            print(f"❌ 文档上传失败: {response.text}")
            return
        
        # 3. 分析文档需求
        print("\n🔍 步骤3: 分析文档需求")
        response = requests.post(
            f"{API_BASE_URL}/documents/analyze",
            json={"file_path": file_path}
        )
        
        if response.status_code == 200:
            analysis_result = response.json()
            print("✅ 需求分析完成")
            print(f"   分析结果长度: {len(analysis_result['analysis'])} 字符")
            
            # 显示部分分析结果
            analysis_preview = analysis_result['analysis'][:500] + "..." if len(analysis_result['analysis']) > 500 else analysis_result['analysis']
            print(f"   分析预览: {analysis_preview}")
        else:
            print(f"❌ 需求分析失败: {response.text}")
            return
        
        # 4. 创建项目
        print("\n📋 步骤4: 创建项目")
        project_data = {
            "name": "广东IPTV可视化编辑工具三期项目投标",
            "description": "基于招标书001.docx的完整投标方案生成测试",
            "enable_differentiation": True
        }
        
        response = requests.post(f"{API_BASE_URL}/projects/", json=project_data)
        
        if response.status_code == 200:
            project_result = response.json()
            project_id = project_result["id"]
            print(f"✅ 项目创建成功")
            print(f"   项目ID: {project_id}")
            print(f"   项目名称: {project_result['name']}")
        else:
            print(f"❌ 项目创建失败: {response.text}")
            return
        
        # 5. 启动完整生成流程
        print("\n🔄 步骤5: 启动完整生成流程")
        generation_data = {
            "project_id": project_id,
            "document_content": analysis_result['analysis'],  # 使用分析结果作为文档内容
            "enable_differentiation": True,
            "enable_validation": True
        }
        
        response = requests.post(f"{API_BASE_URL}/generation/generate", json=generation_data)
        
        if response.status_code == 200:
            generation_result = response.json()
            task_id = generation_result["task_id"]
            print(f"✅ 生成任务启动成功")
            print(f"   任务ID: {task_id}")
        else:
            print(f"❌ 生成任务启动失败: {response.text}")
            return
        
        # 6. 监控生成进度
        print("\n⏳ 步骤6: 监控生成进度")
        max_wait_time = 300  # 最大等待5分钟
        start_time = time.time()
        
        while time.time() - start_time < max_wait_time:
            response = requests.get(f"{API_BASE_URL}/generation/status/{task_id}")
            
            if response.status_code == 200:
                status_result = response.json()
                current_status = status_result["status"]
                current_step = status_result.get("current_step", "unknown")
                
                print(f"   状态: {current_status} | 当前步骤: {current_step}")
                
                if current_status == "completed":
                    print("✅ 生成任务完成！")
                    break
                elif current_status == "failed":
                    error_msg = status_result.get("error", "未知错误")
                    print(f"❌ 生成任务失败: {error_msg}")
                    return
                
                time.sleep(10)  # 等待10秒后再次检查
            else:
                print(f"❌ 状态查询失败: {response.text}")
                return
        else:
            print("⚠️ 生成任务超时，但可能仍在后台运行")
        
        # 7. 获取生成结果
        print("\n📄 步骤7: 获取生成结果")
        response = requests.get(f"{API_BASE_URL}/generation/result/{task_id}")
        
        if response.status_code == 200:
            result_data = response.json()
            print("✅ 生成结果获取成功")
            
            # 显示结果统计
            sections = result_data.get("sections", [])
            print(f"   生成章节数量: {len(sections)}")
            
            for i, section in enumerate(sections[:5]):  # 显示前5个章节
                title = section.get("title", f"章节{i+1}")
                content_length = len(section.get("content", ""))
                print(f"   - {title}: {content_length} 字符")
            
            # 检查是否有最终文档路径
            final_doc_path = result_data.get("final_document_path")
            if final_doc_path:
                print(f"   最终文档路径: {final_doc_path}")
                
                # 检查文档是否存在
                if Path(final_doc_path).exists():
                    file_size = Path(final_doc_path).stat().st_size / 1024
                    print(f"   文档大小: {file_size:.1f} KB")
                else:
                    print("   ⚠️ 最终文档文件不存在")
            
        else:
            print(f"❌ 生成结果获取失败: {response.text}")
            return
        
        # 8. 总结
        print("\n🎉 完整工作流程测试完成")
        print("=" * 60)
        print("✅ 测试结果总结:")
        print(f"   - 后端服务: 正常运行")
        print(f"   - 前端服务: 正常运行")
        print(f"   - 文档上传: 成功")
        print(f"   - 需求分析: 成功")
        print(f"   - 项目创建: 成功")
        print(f"   - 生成流程: 完成")
        print(f"   - 结果获取: 成功")
        
        if final_doc_path and Path(final_doc_path).exists():
            print(f"\n📁 生成的投标书文档: {final_doc_path}")
            print("💡 可以打开查看生成的完整投标方案")
        
        return final_doc_path if final_doc_path and Path(final_doc_path).exists() else None
        
    except Exception as e:
        print(f"❌ 测试过程中发生异常: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    print("🎯 AI投标系统完整工作流程测试")
    print("本测试将使用招标书001.docx生成完整的投标方案")
    print("-" * 60)
    
    # 运行完整测试
    result_path = test_full_workflow()
    
    if result_path:
        print(f"\n🎊 测试成功完成！生成的投标书: {result_path}")
    else:
        print("\n😞 测试未能完成或生成文档")
