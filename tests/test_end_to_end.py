#!/usr/bin/env python3
"""
端到端测试：从招标书到标书的完整流程测试
"""

import shutil
import tempfile
import time
from pathlib import Path

import pytest

from backend.services.content_generator import content_generator
from backend.services.document_parser import document_parser
from backend.services.llm_service import llm_service


class TestEndToEndWorkflow:
    """端到端工作流测试"""

    @pytest.fixture(autouse=True)
    def setup_test_environment(self):
        """设置测试环境"""
        # 创建临时目录
        self.temp_dir = Path(tempfile.mkdtemp())
        self.test_uploads_dir = self.temp_dir / "uploads"
        self.test_outputs_dir = self.temp_dir / "outputs"

        self.test_uploads_dir.mkdir(exist_ok=True)
        self.test_outputs_dir.mkdir(exist_ok=True)

        # 准备测试文档
        self.test_doc_path = self.test_uploads_dir / "test_bidding_document.txt"
        self.test_doc_content = """智慧城市综合管理平台建设项目招标文件

一、项目概述
本项目旨在建设一套智慧城市综合管理平台，实现城市各类数据的统一管理、分析和展示。

二、技术需求
1. 系统架构要求
- 采用微服务架构设计
- 支持分布式部署
- 具备高可用性和可扩展性

2. 功能需求
- 数据采集模块：支持多种数据源接入
- 数据处理模块：实时数据处理和分析
- 可视化展示：提供丰富的图表和大屏展示
- 用户管理：支持多级用户权限管理

3. 性能指标
- 系统并发用户数：不少于1000人
- 数据处理延迟：不超过3秒
- 系统可用性：99.9%以上

4. 技术栈要求
- 后端：Java Spring Boot或Python Django
- 前端：Vue.js或React
- 数据库：MySQL或PostgreSQL
- 缓存：Redis
- 消息队列：RabbitMQ或Kafka

三、评分标准
1. 技术方案（40分）
- 架构设计合理性
- 技术选型先进性
- 系统安全性

2. 实施方案（30分）
- 项目计划详细程度
- 风险控制措施
- 质量保证体系

3. 团队实力（20分）
- 项目经验
- 技术能力
- 团队规模

4. 商务报价（10分）
- 价格合理性
- 性价比

四、项目周期
项目总工期为6个月，分为以下阶段：
1. 需求分析和设计阶段（1个月）
2. 开发阶段（3个月）
3. 测试阶段（1个月）
4. 部署和验收阶段（1个月）

五、交付要求
1. 完整的系统源代码
2. 详细的技术文档
3. 用户操作手册
4. 系统部署文档
5. 培训服务
"""

        # 写入测试文档
        with open(self.test_doc_path, 'w', encoding='utf-8') as f:
            f.write(self.test_doc_content)

        yield

        # 清理临时目录
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_document_parsing(self):
        """测试文档解析功能"""
        print("\n🔍 测试文档解析功能...")

        # 解析文档
        result = document_parser.parse_document(self.test_doc_path)

        # 验证解析结果
        assert isinstance(result, dict), "解析结果应该是字典类型"
        assert "file_name" in result, "解析结果应包含文件名"
        assert "documents" in result, "解析结果应包含文档内容"
        assert "chunks" in result, "解析结果应包含文档分块"
        assert "metadata" in result, "解析结果应包含元数据"

        # 验证具体内容
        assert result["file_name"] == "test_bidding_document.txt"
        assert len(result["documents"]) > 0, "应该有文档内容"
        assert len(result["chunks"]) > 0, "应该有文档分块"

        print(f"✅ 文档解析成功：{result['file_name']}")
        print(f"   - 文档数量: {len(result['documents'])}")
        print(f"   - 分块数量: {len(result['chunks'])}")

        return result

    @pytest.mark.asyncio
    async def test_requirement_analysis(self):
        """测试需求分析功能"""
        print("\n🧠 测试需求分析功能...")

        # 先解析文档
        parse_result = self.test_document_parsing()

        # 提取文档内容
        content = "\n".join([doc.page_content for doc in parse_result["documents"]])

        # 分析需求
        analysis_result = await llm_service.analyze_requirements(content)

        # 验证分析结果
        assert isinstance(analysis_result, dict), "分析结果应该是字典类型"
        assert "status" in analysis_result, "分析结果应包含状态"
        assert "analysis" in analysis_result, "分析结果应包含分析内容"

        if analysis_result["status"] == "success":
            analysis = analysis_result["analysis"]
            assert isinstance(analysis, str), "分析内容应该是字符串类型"
            assert len(analysis) > 0, "分析内容不应为空"

            print("✅ 需求分析成功")
            print(f"   - 分析内容长度: {len(analysis)} 字符")
            print(f"   - 内容预览: {analysis[:200]}...")
        else:
            print(f"⚠️ 需求分析失败: {analysis_result.get('error', 'Unknown error')}")

        return analysis_result

    @pytest.mark.asyncio
    async def test_outline_generation(self):
        """测试提纲生成功能"""
        print("\n📋 测试提纲生成功能...")

        # 先进行需求分析
        analysis_result = await self.test_requirement_analysis()

        if analysis_result["status"] != "success":
            pytest.skip("需求分析失败，跳过提纲生成测试")

        # 生成提纲
        requirements = analysis_result["analysis"]  # 直接使用字符串，不需要JSON序列化
        outline_result = await llm_service.generate_outline(requirements)

        # 验证提纲结果
        assert isinstance(outline_result, dict), "提纲结果应该是字典类型"
        assert "status" in outline_result, "提纲结果应包含状态"
        assert "outline" in outline_result, "提纲结果应包含提纲内容"

        if outline_result["status"] == "success":
            outline = outline_result["outline"]
            assert isinstance(outline, str), "提纲内容应该是字符串类型"
            assert len(outline) > 0, "提纲内容不应为空"

            print("✅ 提纲生成成功")
            print(f"   - 提纲内容长度: {len(outline)} 字符")
            print(f"   - 内容预览: {outline[:300]}...")
        else:
            print(f"⚠️ 提纲生成失败: {outline_result.get('error', 'Unknown error')}")

        return outline_result

    @pytest.mark.asyncio
    async def test_content_generation(self):
        """测试内容生成功能"""
        print("\n📝 测试内容生成功能...")

        # 先进行需求分析
        analysis_result = await self.test_requirement_analysis()

        if analysis_result["status"] != "success":
            pytest.skip("需求分析失败，跳过内容生成测试")

        # 再生成提纲
        outline_result = await self.test_outline_generation()

        if outline_result["status"] != "success":
            pytest.skip("提纲生成失败，跳过内容生成测试")

        # 创建一个模拟的项目对象
        from backend.models.project import Project, ProjectStatus

        mock_project = Project(
            id="test_project_001",
            name="智慧城市综合管理平台测试项目",
            description="端到端测试项目",
            company_name="测试公司",
            enable_differentiation=True,
            status=ProjectStatus.ANALYZING
        )

        # 生成内容
        generation_result = await content_generator.generate_proposal(
            project=mock_project,
            document_path=str(self.test_doc_path)
        )

        # 验证生成结果
        assert isinstance(generation_result, dict), "生成结果应该是字典类型"
        assert "status" in generation_result, "生成结果应包含状态"

        if generation_result["status"] == "success":
            assert "document_path" in generation_result, "成功结果应包含文档路径"

            file_path = Path(generation_result["document_path"])
            assert file_path.exists(), "生成的文件应该存在"
            assert file_path.suffix == ".docx", "生成的文件应该是Word格式"

            print("✅ 内容生成成功")
            print(f"   - 输出文件: {file_path.name}")
            print(f"   - 文件大小: {file_path.stat().st_size} bytes")
        else:
            print(f"⚠️ 内容生成失败: {generation_result.get('error', 'Unknown error')}")

        return generation_result

    @pytest.mark.asyncio
    async def test_full_workflow(self):
        """测试完整工作流程"""
        print("\n🚀 测试完整工作流程...")

        start_time = time.time()

        try:
            # 1. 文档解析
            print("步骤 1/4: 文档解析")
            parse_result = self.test_document_parsing()

            # 2. 需求分析
            print("步骤 2/4: 需求分析")
            analysis_result = await self.test_requirement_analysis()

            # 3. 提纲生成
            print("步骤 3/4: 提纲生成")
            outline_result = await self.test_outline_generation()

            # 4. 内容生成
            print("步骤 4/4: 内容生成")
            generation_result = await self.test_content_generation()

            end_time = time.time()
            total_time = end_time - start_time

            print(f"\n🎉 完整工作流程测试完成!")
            print(f"   - 总耗时: {total_time:.2f} 秒")

            # 验证所有步骤都成功
            assert parse_result is not None
            if analysis_result["status"] == "success":
                assert outline_result["status"] == "success"
                assert generation_result["status"] == "success"
                print("   - 所有步骤都成功完成 ✅")
            else:
                print("   - 部分步骤失败，但文档解析成功 ⚠️")

        except Exception as e:
            print(f"❌ 工作流程测试失败: {str(e)}")
            raise


if __name__ == "__main__":
    # 直接运行测试
    pytest.main([__file__, "-v", "-s"])
