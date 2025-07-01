from typing import Tuple

import gradio as gr
import requests

# 后端API基础URL
API_BASE_URL = "http://localhost:8000/api"


class AIBiddingApp:
    """AI投标方案生成系统前端应用"""

    def __init__(self):
        self.current_project_id = None
        self.current_task_id = None

    def upload_document(self, file) -> Tuple[str, str]:
        """上传招标文档"""
        if file is None:
            return "请选择文件", ""

        try:
            files = {"file": (file.name, open(file.name, "rb"))}
            response = requests.post(f"{API_BASE_URL}/documents/upload", files=files)

            if response.status_code == 200:
                result = response.json()
                return f"✅ 文档上传成功: {result['file_name']}", result['file_path']
            else:
                return f"❌ 上传失败: {response.text}", ""

        except Exception as e:
            return f"❌ 上传异常: {str(e)}", ""

    def analyze_document(self, file_path: str) -> Tuple[str, str]:
        """分析文档需求"""
        if not file_path:
            return "请先上传文档", ""

        try:
            response = requests.post(
                f"{API_BASE_URL}/documents/analyze",
                json={"file_path": file_path}
            )

            if response.status_code == 200:
                result = response.json()
                analysis = result['analysis']
                return "✅ 需求分析完成", analysis
            else:
                return f"❌ 分析失败: {response.text}", ""

        except Exception as e:
            return f"❌ 分析异常: {str(e)}", ""

    def create_project(self, project_name: str, description: str, enable_diff: bool) -> str:
        """创建项目"""
        if not project_name.strip():
            return "请输入项目名称"

        try:
            data = {
                "name": project_name.strip(),
                "description": description.strip() if description else None,
                "enable_differentiation": enable_diff
            }

            response = requests.post(f"{API_BASE_URL}/projects/", json=data)

            if response.status_code == 200:
                result = response.json()
                self.current_project_id = result['id']
                return f"✅ 项目创建成功: {result['name']} (ID: {result['id']})"
            else:
                return f"❌ 创建失败: {response.text}"

        except Exception as e:
            return f"❌ 创建异常: {str(e)}"

    def generate_outline(self, requirements: str) -> Tuple[str, str]:
        """生成方案提纲"""
        if not requirements.strip():
            return "请先进行需求分析", ""

        try:
            data = {"requirements_analysis": requirements}
            response = requests.post(f"{API_BASE_URL}/generation/outline", json=data)

            if response.status_code == 200:
                result = response.json()
                return "✅ 提纲生成完成", result['outline']
            else:
                return f"❌ 生成失败: {response.text}", ""

        except Exception as e:
            return f"❌ 生成异常: {str(e)}", ""

    def start_full_generation(self, file_path: str) -> str:
        """启动完整方案生成"""
        if not self.current_project_id:
            return "请先创建项目"

        if not file_path:
            return "请先上传文档"

        try:
            data = {
                "project_id": self.current_project_id,
                "document_path": file_path
            }

            response = requests.post(f"{API_BASE_URL}/generation/full", json=data)

            if response.status_code == 200:
                result = response.json()
                self.current_task_id = result['task_id']
                return f"✅ 生成任务已启动，任务ID: {result['task_id']}"
            else:
                return f"❌ 启动失败: {response.text}"

        except Exception as e:
            return f"❌ 启动异常: {str(e)}"

    def check_task_status(self) -> str:
        """检查任务状态"""
        if not self.current_task_id:
            return "没有正在运行的任务"

        try:
            response = requests.get(f"{API_BASE_URL}/generation/task/{self.current_task_id}")

            if response.status_code == 200:
                result = response.json()
                task = result['task']

                status = task['status']
                progress = task.get('progress', 0)
                current_step = task.get('current_step', '')

                if status == "running":
                    return f"🔄 任务进行中... 进度: {progress}% - {current_step}"
                elif status == "completed":
                    return f"✅ 任务完成! 进度: {progress}%"
                elif status == "failed":
                    error = task.get('error', '未知错误')
                    return f"❌ 任务失败: {error}"
                else:
                    return f"📋 任务状态: {status}"
            else:
                return f"❌ 查询失败: {response.text}"

        except Exception as e:
            return f"❌ 查询异常: {str(e)}"

    def get_output_files(self) -> str:
        """获取输出文件列表"""
        try:
            response = requests.get(f"{API_BASE_URL}/generation/outputs")

            if response.status_code == 200:
                result = response.json()
                files = result['files']

                if not files:
                    return "暂无输出文件"

                file_list = []
                for file in files[:10]:  # 只显示最近10个文件
                    name = file['name']
                    size_mb = file['size'] / (1024 * 1024)
                    file_list.append(f"📄 {name} ({size_mb:.1f}MB)")

                return "\n".join(file_list)
            else:
                return f"❌ 获取失败: {response.text}"

        except Exception as e:
            return f"❌ 获取异常: {str(e)}"


def create_interface():
    """创建Gradio界面"""
    app = AIBiddingApp()

    with gr.Blocks(title="AI投标方案生成系统", theme=gr.themes.Soft()) as interface:
        gr.Markdown("# 🤖 AI投标方案生成系统")
        gr.Markdown("基于AI的投标方案辅助生成系统，帮助您快速生成高质量的技术方案")

        with gr.Tab("📁 项目管理"):
            with gr.Row():
                with gr.Column():
                    project_name = gr.Textbox(label="项目名称", placeholder="请输入项目名称")
                    project_desc = gr.Textbox(label="项目描述", placeholder="请输入项目描述（可选）", lines=3)
                    enable_diff = gr.Checkbox(label="启用差异化处理", value=True)
                    create_btn = gr.Button("创建项目", variant="primary")

                with gr.Column():
                    project_status = gr.Textbox(label="项目状态", interactive=False)

            create_btn.click(
                app.create_project,
                inputs=[project_name, project_desc, enable_diff],
                outputs=[project_status]
            )

        with gr.Tab("📄 文档处理"):
            with gr.Row():
                with gr.Column():
                    file_upload = gr.File(label="上传招标文档", file_types=[".pdf", ".docx", ".doc"])
                    upload_btn = gr.Button("上传文档", variant="primary")
                    analyze_btn = gr.Button("分析需求", variant="secondary")

                with gr.Column():
                    upload_status = gr.Textbox(label="上传状态", interactive=False)
                    file_path = gr.Textbox(label="文件路径", interactive=False, visible=False)

            with gr.Row():
                analysis_result = gr.Textbox(label="需求分析结果", lines=10, interactive=False)

            upload_btn.click(
                app.upload_document,
                inputs=[file_upload],
                outputs=[upload_status, file_path]
            )

            analyze_btn.click(
                app.analyze_document,
                inputs=[file_path],
                outputs=[upload_status, analysis_result]
            )

        with gr.Tab("📝 方案生成"):
            with gr.Row():
                with gr.Column():
                    outline_btn = gr.Button("生成提纲", variant="secondary")
                    generate_btn = gr.Button("开始完整生成", variant="primary")
                    status_btn = gr.Button("检查状态", variant="secondary")

                with gr.Column():
                    generation_status = gr.Textbox(label="生成状态", interactive=False)

            with gr.Row():
                outline_result = gr.Textbox(label="方案提纲", lines=15, interactive=False)

            outline_btn.click(
                app.generate_outline,
                inputs=[analysis_result],
                outputs=[generation_status, outline_result]
            )

            generate_btn.click(
                app.start_full_generation,
                inputs=[file_path],
                outputs=[generation_status]
            )

            status_btn.click(
                app.check_task_status,
                outputs=[generation_status]
            )

        with gr.Tab("📋 输出管理"):
            with gr.Row():
                with gr.Column():
                    refresh_btn = gr.Button("刷新文件列表", variant="secondary")

                with gr.Column():
                    pass

            with gr.Row():
                output_files = gr.Textbox(label="输出文件列表", lines=10, interactive=False)

            refresh_btn.click(
                app.get_output_files,
                outputs=[output_files]
            )

            # 页面加载时自动刷新文件列表
            interface.load(app.get_output_files, outputs=[output_files])

    return interface


if __name__ == "__main__":
    interface = create_interface()
    interface.launch(
        server_name="127.0.0.1",
        server_port=7860,
        share=False,
        debug=False
    )
