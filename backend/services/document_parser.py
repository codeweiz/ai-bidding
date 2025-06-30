from pathlib import Path
from typing import Dict, Any, Optional

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_unstructured import UnstructuredLoader


class DocumentParser:
    def __init__(self, chunk_size: int = 2000, chunk_overlap: int = 200):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )

    def parse_document(self, file_path: Path) -> Dict[str, Any]:
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        try:
            loader = UnstructuredLoader(
                file_path=str(file_path),
                languages=["chi_sim", "eng"],
                separators=["\n\n", "\n", ".", "。", "!", "?", " ", "! "]
            )
            documents = loader.load()
            chunks = self.text_splitter.split_documents(documents)
        except Exception as e:
            raise ValueError(f"Failed to parse document: {e}")

        return {
            "file_name": file_path.name,
            "file_type": file_path.suffix,
            "documents": documents,
            "chunks": chunks,
            "metadata": {
                "total_pages": len(documents),
                "total_chunks": len(chunks),
            }
        }


# 全局实例
document_parser = DocumentParser()
