import pytest
from pathlib import Path
import unittest
import asyncio

from backend.services.document_parser import document_parser
from backend.services.llm_service import llm_service


class TestDocumentParser(unittest.TestCase):
    def test_document_parser(self):
        """测试文档解析功能"""
        path = Path("./data/sample_tender.md")
        if not path.exists():
            self.skipTest(f"测试文件 {path} 不存在")

        result = document_parser.parse_document(path)
        self.assertIsInstance(result, dict)
        self.assertIn("file_name", result)
        self.assertIn("documents", result)
        self.assertIn("chunks", result)
        self.assertIn("metadata", result)

        # 检查解析结果
        self.assertEqual(result["file_name"], "sample_tender.md")
        self.assertGreater(len(result["documents"]), 0)
        self.assertGreater(len(result["chunks"]), 0)


class TestLLMService(unittest.TestCase):
    def setUp(self):
        """设置测试环境"""
        self.sample_content = """
        某市智慧城市建设项目招标文件

        项目要求：
        1. 构建统一的城市数据中心
        2. 实现多部门数据共享
        3. 系统并发用户数不少于10000
        4. 数据查询响应时间不超过3秒
        """

    # @unittest.skip("需要API密钥才能运行")
    def test_analyze_requirements(self):
        """测试需求分析功能"""
        async def run_test():
            result = await llm_service.analyze_requirements(self.sample_content)
            self.assertIsInstance(result, dict)
            self.assertIn("status", result)
            self.assertIn("analysis", result)

        asyncio.run(run_test())

    # @unittest.skip("需要API密钥才能运行")
    def test_generate_outline(self):
        """测试提纲生成功能"""
        async def run_test():
            requirements = "需要构建智慧城市数据平台，包含数据采集、存储、分析等模块"
            result = await llm_service.generate_outline(requirements)
            self.assertIsInstance(result, dict)
            self.assertIn("status", result)
            self.assertIn("outline", result)

        asyncio.run(run_test())


if __name__ == "__main__":
    unittest.main()
