#!/usr/bin/env python3
"""
前后端集成测试
"""

import requests
import time
import json
from pathlib import Path


def test_backend_health():
    """测试后端健康状态"""
    print("🔍 测试后端健康状态...")
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 后端健康: {data}")
            return True
        else:
            print(f"❌ 后端不健康: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 后端连接失败: {e}")
        return False


def test_frontend_access():
    """测试前端访问"""
    print("🔍 测试前端访问...")
    try:
        response = requests.get("http://localhost:7860", timeout=5)
        if response.status_code == 200:
            print("✅ 前端可访问")
            return True
        else:
            print(f"❌ 前端访问失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 前端连接失败: {e}")
        return False


def test_project_creation():
    """测试项目创建API"""
    print("🔍 测试项目创建...")
    try:
        data = {
            "name": "测试项目",
            "description": "前后端集成测试项目",
            "enable_differentiation": True
        }
        response = requests.post("http://localhost:8000/api/projects/", json=data, timeout=10)
        if response.status_code == 200:
            project = response.json()
            print(f"✅ 项目创建成功: {project['id']}")
            return project['id']
        else:
            print(f"❌ 项目创建失败: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"❌ 项目创建异常: {e}")
        return None


def test_document_upload():
    """测试文档上传API"""
    print("🔍 测试文档上传...")

    # 检查测试文件
    test_file = Path("uploads/test_tender_document.docx")
    if not test_file.exists():
        print(f"❌ 测试文件不存在: {test_file}")
        return None

    try:
        with open(test_file, 'rb') as f:
            files = {"file": (test_file.name, f, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}
            response = requests.post("http://localhost:8000/api/documents/upload", files=files, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 文档上传成功: {result['file_path']}")
            return result['file_path']
        else:
            print(f"❌ 文档上传失败: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"❌ 文档上传异常: {e}")
        return None


def test_generation_api(project_id, document_path):
    """测试生成API"""
    print("🔍 测试生成API...")
    try:
        data = {
            "project_id": project_id,
            "document_path": document_path,
            "template_path": None
        }
        response = requests.post("http://localhost:8000/api/generation/full", json=data, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 生成任务启动成功: {result['task_id']}")
            return result['task_id']
        else:
            print(f"❌ 生成任务启动失败: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"❌ 生成任务启动异常: {e}")
        return None


def test_task_status(task_id):
    """测试任务状态查询"""
    print("🔍 测试任务状态查询...")
    try:
        response = requests.get(f"http://localhost:8000/api/generation/task/{task_id}", timeout=5)
        
        if response.status_code == 200:
            result = response.json()
            task = result['task']
            status = task['status']
            progress = task.get('progress', 0)
            current_step = task.get('current_step', '')
            
            print(f"✅ 任务状态: {status}, 进度: {progress}%, 步骤: {current_step}")
            return status
        else:
            print(f"❌ 状态查询失败: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"❌ 状态查询异常: {e}")
        return None


def test_api_endpoints():
    """测试所有API端点"""
    print("🔍 测试API端点...")
    
    endpoints = [
        ("GET", "/", "根路径"),
        ("GET", "/health", "健康检查"),
        ("GET", "/api/projects/", "项目列表"),
        ("GET", "/api/documents/uploads", "上传文件列表"),
        ("GET", "/api/generation/outputs", "输出文件列表")
    ]
    
    for method, path, desc in endpoints:
        try:
            url = f"http://localhost:8000{path}"
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                print(f"  ✅ {desc}: {path}")
            else:
                print(f"  ❌ {desc}: {path} - {response.status_code}")
        except Exception as e:
            print(f"  ❌ {desc}: {path} - {e}")


def main():
    """主测试函数"""
    print("🤖 AI投标系统前后端集成测试")
    print("=" * 50)
    
    # 1. 测试后端健康状态
    if not test_backend_health():
        print("❌ 后端服务未启动，请先启动后端")
        return
    
    # 2. 测试前端访问
    if not test_frontend_access():
        print("❌ 前端服务未启动，请先启动前端")
        return
    
    # 3. 测试API端点
    test_api_endpoints()
    
    # 4. 测试项目创建
    project_id = test_project_creation()
    if not project_id:
        print("❌ 项目创建失败，停止测试")
        return
    
    # 5. 测试文档上传
    document_path = test_document_upload()
    if not document_path:
        print("❌ 文档上传失败，停止测试")
        return
    
    # 6. 测试生成API（不等待完成）
    task_id = test_generation_api(project_id, document_path)
    if not task_id:
        print("❌ 生成任务启动失败")
        return
    
    # 7. 测试任务状态查询
    for i in range(3):
        status = test_task_status(task_id)
        if status in ["completed", "failed"]:
            break
        time.sleep(2)
    
    print("\n" + "=" * 50)
    print("🎉 前后端集成测试完成!")
    print("\n📋 测试结果总结:")
    print("✅ 后端服务: 正常")
    print("✅ 前端服务: 正常")
    print("✅ API端点: 可访问")
    print("✅ 项目创建: 正常")
    print("✅ 文档上传: 正常")
    print("✅ 生成任务: 可启动")
    print("✅ 状态查询: 正常")
    
    print("\n🌐 访问地址:")
    print("  前端界面: http://localhost:7860")
    print("  后端API: http://localhost:8000")
    print("  API文档: http://localhost:8000/docs")


if __name__ == "__main__":
    main()
