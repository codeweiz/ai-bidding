#!/usr/bin/env python3
"""
测试文档路径传递修复
"""

import requests
import json
from pathlib import Path


def test_document_upload_and_generation():
    """测试文档上传和生成流程"""
    print("🧪 测试文档路径传递修复")
    print("=" * 50)
    
    # 1. 测试文档上传
    print("📄 测试文档上传...")
    test_file = Path("uploads/test_tender_document.docx")
    
    if not test_file.exists():
        print(f"❌ 测试文件不存在: {test_file}")
        return
    
    try:
        with open(test_file, 'rb') as f:
            files = {"file": (test_file.name, f, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}
            response = requests.post("http://localhost:8000/api/documents/upload", files=files, timeout=10)
        
        if response.status_code == 200:
            upload_result = response.json()
            uploaded_path = upload_result['file_path']
            print(f"✅ 文档上传成功: {uploaded_path}")
        else:
            print(f"❌ 文档上传失败: {response.status_code} - {response.text}")
            return
    except Exception as e:
        print(f"❌ 文档上传异常: {e}")
        return
    
    # 2. 创建项目
    print("\n📋 创建测试项目...")
    try:
        project_data = {
            "name": "文档路径测试项目",
            "description": "测试实际上传文档的使用",
            "enable_differentiation": True
        }
        response = requests.post("http://localhost:8000/api/projects/", json=project_data, timeout=10)
        
        if response.status_code == 200:
            project = response.json()
            project_id = project['id']
            print(f"✅ 项目创建成功: {project_id}")
        else:
            print(f"❌ 项目创建失败: {response.status_code} - {response.text}")
            return
    except Exception as e:
        print(f"❌ 项目创建异常: {e}")
        return
    
    # 3. 启动生成任务（使用实际上传的文档）
    print(f"\n🚀 启动生成任务（使用文档: {uploaded_path}）...")
    try:
        generation_data = {
            "project_id": project_id,
            "document_path": uploaded_path,  # 使用实际上传的文档路径
            "template_path": None
        }
        
        print(f"📤 发送的数据: {json.dumps(generation_data, indent=2)}")
        
        response = requests.post("http://localhost:8000/api/generation/full", json=generation_data, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            task_id = result['task_id']
            print(f"✅ 生成任务启动成功: {task_id}")
            
            # 4. 检查任务状态
            print(f"\n🔍 检查任务状态...")
            status_response = requests.get(f"http://localhost:8000/api/generation/task/{task_id}", timeout=5)
            
            if status_response.status_code == 200:
                status_result = status_response.json()
                task = status_result['task']
                print(f"📊 任务状态: {task['status']}")
                print(f"📈 进度: {task.get('progress', 0)}%")
                print(f"📝 当前步骤: {task.get('current_step', '')}")
                
                # 检查是否使用了正确的文档
                if 'test_tender_document.docx' in uploaded_path:
                    print("✅ 确认使用了正确的上传文档")
                else:
                    print("❌ 可能使用了错误的文档")
                    
            else:
                print(f"❌ 状态查询失败: {status_response.status_code}")
                
        else:
            print(f"❌ 生成任务启动失败: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"❌ 生成任务异常: {e}")
    
    print("\n" + "=" * 50)
    print("🎯 测试总结:")
    print(f"📄 上传文档: {uploaded_path}")
    print(f"📋 项目ID: {project_id}")
    print(f"🚀 任务ID: {task_id if 'task_id' in locals() else 'N/A'}")
    print("✅ 文档路径传递测试完成")


def test_file_content_verification():
    """验证上传文件的内容"""
    print("\n🔍 验证上传文件内容...")
    
    test_file = Path("uploads/test_tender_document.docx")
    if test_file.exists():
        print(f"📄 测试文件存在: {test_file}")
        print(f"📊 文件大小: {test_file.stat().st_size} bytes")
        
        # 使用document_parser解析文件内容
        try:
            import sys
            sys.path.append('.')
            from backend.services.document_parser import document_parser
            
            result = document_parser.parse_document(test_file)
            content = "\n".join([doc.page_content for doc in result["documents"]])
            
            print(f"📝 文档内容预览 (前200字符):")
            print(content[:200] + "..." if len(content) > 200 else content)
            
            # 检查关键词
            keywords = ["IPTV", "智慧城市", "系统架构", "微服务", "技术需求"]
            found_keywords = [kw for kw in keywords if kw in content]
            print(f"🔍 找到关键词: {found_keywords}")
            
        except Exception as e:
            print(f"❌ 文档解析失败: {e}")
    else:
        print(f"❌ 测试文件不存在: {test_file}")


if __name__ == "__main__":
    # 验证文件内容
    test_file_content_verification()
    
    # 测试完整流程
    test_document_upload_and_generation()
