import pytest
from pathlib import Path
import unittest

from unittest import skipIf
from backend.services.document_parser import document_parser


class TestDocumentParser(unittest.TestCase):
    def test_document_parser(self):
        path = Path("./data/en/home/home.md")
        if not path.exists():
            self.skipTest(f"测试文件 {path} 不存在")  # 使用 unittest 的 skipTest

        result = document_parser.parse_document(path)
        self.assertIsInstance(result, dict)
        self.assertIn("file_name", result)
