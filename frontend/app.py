from typing import Tuple, Optional
import time
import threading

import gradio as gr
import requests

# 后端API基础URL
API_BASE_URL = "http://localhost:8000/api"


class AIBiddingApp:
    """AI投标方案生成系统前端应用"""

    def __init__(self):
        self.current_project_id = None
        self.current_task_id = None
        self.progress_thread = None
        self.stop_progress = False

    def upload_document(self, file) -> Tuple[str, str]:
        """上传招标文档"""
        if file is None:
            return "请选择招标文档", ""

        try:
            files = {"file": (file.name, open(file.name, "rb"))}
            response = requests.post(f"{API_BASE_URL}/documents/upload", files=files)

            if response.status_code == 200:
                result = response.json()
                return f"✅ 招标文档上传成功: {result['file_name']}", result['file_path']
            else:
                return f"❌ 上传失败: {response.text}", ""

        except Exception as e:
            return f"❌ 上传异常: {str(e)}", ""

    def upload_template(self, file) -> Tuple[str, str]:
        """上传模板文档"""
        if file is None:
            return "使用默认模板", ""

        try:
            files = {"file": (file.name, open(file.name, "rb"))}
            response = requests.post(f"{API_BASE_URL}/documents/upload", files=files)

            if response.status_code == 200:
                result = response.json()
                return f"✅ 模板上传成功: {result['file_name']}", result['file_path']
            else:
                return f"❌ 模板上传失败: {response.text}", ""

        except Exception as e:
            return f"❌ 模板上传异常: {str(e)}", ""

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

    def start_full_generation(self, tender_file_path: str, template_file_path: str = None) -> Tuple[str, gr.update]:
        """启动完整方案生成"""
        if not self.current_project_id:
            return "❌ 请先创建项目", gr.update(visible=False)

        if not tender_file_path:
            return "❌ 请先上传招标文档", gr.update(visible=False)

        try:
            # 使用实际上传的文档路径
            data = {
                "project_id": self.current_project_id,
                "document_path": tender_file_path,  # 使用实际上传的文档路径
                "template_path": template_file_path if template_file_path else None
            }

            response = requests.post(f"{API_BASE_URL}/generation/full", json=data)

            if response.status_code == 200:
                result = response.json()
                self.current_task_id = result['task_id']

                # 启动进度监控
                self.start_progress_monitoring()

                return f"✅ 生成任务已启动，正在处理您上传的招标文档...", gr.update(visible=True)
            else:
                return f"❌ 启动失败: {response.text}", gr.update(visible=False)

        except Exception as e:
            return f"❌ 启动异常: {str(e)}", gr.update(visible=False)

    def start_progress_monitoring(self):
        """启动进度监控线程"""
        self.stop_progress = False
        if self.progress_thread and self.progress_thread.is_alive():
            self.stop_progress = True
            self.progress_thread.join()

        self.progress_thread = threading.Thread(target=self._monitor_progress)
        self.progress_thread.daemon = True
        self.progress_thread.start()

    def _monitor_progress(self):
        """监控进度的后台线程"""
        while not self.stop_progress and self.current_task_id:
            try:
                status_info = self.check_task_status()
                if "完成" in status_info or "失败" in status_info:
                    break
                time.sleep(2)  # 每2秒检查一次
            except:
                break

    def check_task_status(self) -> Tuple[str, int, gr.update]:
        """检查任务状态"""
        if not self.current_task_id:
            return "没有正在运行的任务", 0, gr.update(visible=False)

        try:
            response = requests.get(f"{API_BASE_URL}/generation/task/{self.current_task_id}")

            if response.status_code == 200:
                result = response.json()
                task = result['task']

                status = task['status']
                progress = task.get('progress', 0)
                current_step = task.get('current_step', '')
                error = task.get('error', '')

                if status == "running":
                    status_text = f"🔄 任务进行中... {current_step}"
                    return status_text, progress, gr.update(visible=False)
                elif status == "completed":
                    status_text = f"✅ 任务完成! 可以下载投标书了"
                    self.stop_progress = True
                    return status_text, 100, gr.update(visible=True)
                elif status == "failed":
                    status_text = f"❌ 任务失败: {error}"
                    self.stop_progress = True
                    return status_text, 0, gr.update(visible=False)
                else:
                    return f"📋 任务状态: {status}", progress, gr.update(visible=False)
            else:
                return f"❌ 查询失败: {response.text}", 0, gr.update(visible=False)

        except Exception as e:
            return f"❌ 查询异常: {str(e)}", 0, gr.update(visible=False)

    def download_result(self) -> str:
        """下载生成的投标书"""
        if not self.current_project_id:
            return "❌ 没有可下载的文件"

        try:
            # 获取项目信息
            response = requests.get(f"{API_BASE_URL}/projects/{self.current_project_id}")

            if response.status_code == 200:
                project = response.json()
                if project.get('final_document_path'):
                    # 返回下载链接信息
                    download_url = f"http://localhost:8000/api/projects/{self.current_project_id}/download"
                    return f"✅ 文件准备就绪！请访问下载链接：{download_url}"
                else:
                    return "❌ 文件尚未生成"
            else:
                return f"❌ 获取项目信息失败: {response.text}"

        except Exception as e:
            return f"❌ 下载异常: {str(e)}"

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
        gr.Markdown("基于AI的投标方案辅助生成系统，帮助您快速生成高质量的IPTV技术方案")
        gr.Markdown("### 📋 使用说明：创建项目 → 上传招标文档 → 可选上传模板 → 点击生成 → 下载投标书")

        # 项目创建区域
        gr.Markdown("## 📋 项目管理")
        with gr.Row():
            with gr.Column(scale=2):
                project_name = gr.Textbox(label="项目名称", placeholder="请输入项目名称")
                project_desc = gr.Textbox(label="项目描述", placeholder="请输入项目描述（可选）", lines=2)
                enable_diff = gr.Checkbox(label="启用差异化处理", value=True)
                create_btn = gr.Button("创建项目", variant="primary")

            with gr.Column(scale=1):
                project_status = gr.Textbox(label="项目状态", interactive=False)

        create_btn.click(
            app.create_project,
            inputs=[project_name, project_desc, enable_diff],
            outputs=[project_status]
        )

        # 文档上传区域
        gr.Markdown("---")
        gr.Markdown("## 📄 文档上传")
        with gr.Row():
            with gr.Column():
                gr.Markdown("### 📄 招标文档 (必需)")
                tender_file = gr.File(label="选择招标文档", file_types=[".pdf", ".docx", ".doc"])
                tender_upload_btn = gr.Button("上传招标文档", variant="primary")
                tender_status = gr.Textbox(label="招标文档状态", interactive=False)
                tender_path = gr.Textbox(label="招标文档路径", interactive=False, visible=False)

            with gr.Column():
                gr.Markdown("### 📋 模板文档 (可选)")
                template_file = gr.File(label="选择模板文档", file_types=[".docx"])
                template_upload_btn = gr.Button("上传模板文档", variant="secondary")
                template_status = gr.Textbox(label="模板状态", interactive=False, value="使用默认模板")
                template_path = gr.Textbox(label="模板路径", interactive=False, visible=False)

        tender_upload_btn.click(
            app.upload_document,
            inputs=[tender_file],
            outputs=[tender_status, tender_path]
        )

        template_upload_btn.click(
            app.upload_template,
            inputs=[template_file],
            outputs=[template_status, template_path]
        )

        # 生成控制区域
        gr.Markdown("---")
        gr.Markdown("## 🚀 投标书生成")
        with gr.Row():
            with gr.Column(scale=2):
                generate_btn = gr.Button("🎯 开始生成投标书", variant="primary", size="lg")
                generation_status = gr.Textbox(label="生成状态", interactive=False, value="等待开始...")

                # 进度条
                progress_bar = gr.Slider(
                    minimum=0, maximum=100, value=0, step=1,
                    label="生成进度", interactive=False, visible=False
                )

                # 下载按钮
                download_btn = gr.Button("📥 下载投标书", variant="success", visible=False)
                download_status = gr.Textbox(label="下载状态", interactive=False)

            with gr.Column(scale=1):
                status_btn = gr.Button("🔄 刷新状态", variant="secondary")
                gr.Markdown("### 📝 操作说明")
                gr.Markdown("""
                1. 创建项目
                2. 上传招标文档（必需）
                3. 可选择上传模板文档
                4. 点击"开始生成投标书"
                5. 观察进度条更新
                6. 生成完成后下载投标书

                ⏱️ 预计用时：5-15分钟
                """)

        generate_btn.click(
            app.start_full_generation,
            inputs=[tender_path, template_path],
            outputs=[generation_status, progress_bar]
        )

        status_btn.click(
            app.check_task_status,
            outputs=[generation_status, progress_bar, download_btn]
        )

        download_btn.click(
            app.download_result,
            outputs=[download_status]
        )

        # 页面加载时初始化状态
        interface.load(
            lambda: ("等待任务启动...", 0, gr.update(visible=False)),
            outputs=[generation_status, progress_bar, download_btn]
        )

    return interface


if __name__ == "__main__":
    interface = create_interface()
    interface.launch(
        server_name="127.0.0.1",
        server_port=7860,
        share=False,
        debug=False
    )
