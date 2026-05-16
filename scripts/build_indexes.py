from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(PROJECT_ROOT))

from src.core.config import get_settings
from src.rag.ingest import MarkdownKnowledgeIngestor
from src.sql_agent.schema_index import SchemaIndexer


def main() -> None:
    settings = get_settings()
    docs_count = MarkdownKnowledgeIngestor(settings).ingest()
    schema_count = SchemaIndexer(settings).build()
    print(f"知识库索引完成，文档切片数: {docs_count}")
    print(f"Schema 索引完成，表数量: {schema_count}")


if __name__ == "__main__":
    main()
