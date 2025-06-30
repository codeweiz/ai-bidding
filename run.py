#!/usr/bin/env python3
"""
AI投标方案生成系统启动脚本
"""

import subprocess
import sys
import time
import signal
import os
from pathlib import Path


def check_dependencies():
    """检查依赖是否安装"""
    try:
        import fastapi
        import gradio
        import langchain
        import langgraph
        import unstructured
        print("✅ 依赖检查通过")
        return True
    except ImportError as e:
        print(f"❌ 缺少依赖: {e}")
        print("请运行: make install 或 pip install -e .")
        return False


def check_config():
    """检查配置文件"""
    config_file = Path("config.toml")
    if not config_file.exists():
        print("❌ 配置文件 config.toml 不存在")
        return False
    
    # 检查API密钥
    with open(config_file) as f:
        content = f.read()
        if "api_key = \"\"" in content or "api_key = \"sk-\"" in content:
            print("⚠️  请在 config.toml 中配置正确的 API 密钥")
    
    print("✅ 配置文件检查通过")
    return True


def create_directories():
    """创建必要的目录"""
    dirs = ["uploads", "outputs", "logs"]
    for dir_name in dirs:
        Path(dir_name).mkdir(exist_ok=True)
    print("✅ 目录创建完成")


def start_backend():
    """启动后端服务"""
    print("🚀 启动后端服务...")
    return subprocess.Popen([
        sys.executable, "-m", "uvicorn", 
        "backend.main:app", 
        "--host", "0.0.0.0", 
        "--port", "8000", 
        "--reload"
    ])


def start_frontend():
    """启动前端服务"""
    print("🚀 启动前端服务...")
    return subprocess.Popen([
        sys.executable, "-m", "frontend.app"
    ])


def wait_for_service(url, timeout=30):
    """等待服务启动"""
    import requests
    
    for i in range(timeout):
        try:
            response = requests.get(url, timeout=1)
            if response.status_code == 200:
                return True
        except:
            pass
        time.sleep(1)
    return False


def main():
    """主函数"""
    print("🤖 AI投标方案生成系统启动器")
    print("=" * 50)
    
    # 检查依赖
    if not check_dependencies():
        sys.exit(1)
    
    # 检查配置
    if not check_config():
        sys.exit(1)
    
    # 创建目录
    create_directories()
    
    # 启动服务
    backend_process = None
    frontend_process = None
    
    try:
        # 启动后端
        backend_process = start_backend()
        
        # 等待后端启动
        print("⏳ 等待后端服务启动...")
        if wait_for_service("http://localhost:8000/health"):
            print("✅ 后端服务启动成功")
        else:
            print("❌ 后端服务启动失败")
            return
        
        # 启动前端
        frontend_process = start_frontend()
        
        # 等待前端启动
        print("⏳ 等待前端服务启动...")
        time.sleep(5)  # Gradio启动需要一些时间
        
        print("\n" + "=" * 50)
        print("🎉 系统启动成功!")
        print("📊 后端API: http://localhost:8000")
        print("🌐 前端界面: http://localhost:7860")
        print("📚 API文档: http://localhost:8000/docs")
        print("=" * 50)
        print("按 Ctrl+C 停止服务")
        
        # 等待用户中断
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n🛑 正在停止服务...")
        
    finally:
        # 清理进程
        if backend_process:
            backend_process.terminate()
            backend_process.wait()
        
        if frontend_process:
            frontend_process.terminate()
            frontend_process.wait()
        
        print("✅ 服务已停止")


if __name__ == "__main__":
    main()
