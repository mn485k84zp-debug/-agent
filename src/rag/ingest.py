from __future__ import annotations

import json
from pathlib import Path

from langchain_chroma import Chroma

from src.core.config import Settings
from src.llm.factory import build_embeddings
from src.rag.splitter import MarkdownSemanticSplitter


class MarkdownKnowledgeIngestor:
    """知识库入库器。"""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.splitter = MarkdownSemanticSplitter()
        self.embeddings = build_embeddings(settings)
        self.vectorstore = Chroma(
            collection_name="knowledge_base",
            persist_directory=str(settings.chroma_dir),
            embedding_function=self.embeddings,
        )

    def ingest(self) -> int:
        docs = []
        for file_path in sorted(self.settings.docs_dir.glob("*.md")):
            docs.extend(self.splitter.split_file(file_path))

        if not docs:
            return 0

        ids = [doc.metadata["chunk_id"] for doc in docs]
        try:
            self.vectorstore.delete(ids=ids)
        except Exception:
            # 首次构建时删除失败是正常情况，不影响后续写入。
            pass

        self.vectorstore.add_documents(documents=docs, ids=ids)
        self._write_docs_index(docs)
        return len(docs)

    def _write_docs_index(self, docs) -> None:
        payload = [
            {"page_content": doc.page_content, "metadata": doc.metadata}
            for doc in docs
        ]
        self.settings.docs_index_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
