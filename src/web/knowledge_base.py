from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path

from pypdf import PdfReader

from src.core.config import get_settings
from src.rag.ingest import MarkdownKnowledgeIngestor


class KnowledgeBaseManager:
    """知识库文件管理器。"""

    def __init__(self) -> None:
        self.settings = get_settings()
        self.manifest_path = Path("data/docs_manifest.json")
        self.ingestor = MarkdownKnowledgeIngestor(self.settings)
        if not self.manifest_path.exists():
            self.manifest_path.write_text("{}", encoding="utf-8")

    def list_documents(self) -> list[dict]:
        manifest = self._load_manifest()
        records: list[dict] = []
        for file_path in sorted(self.settings.docs_dir.glob("*.md")):
            stat = file_path.stat()
            meta = manifest.get(file_path.name, {})
            records.append(
                {
                    "file_name": file_path.name,
                    "display_name": meta.get("display_name", file_path.name),
                    "source_type": meta.get("source_type", "markdown"),
                    "size": stat.st_size,
                    "updated_at": datetime.fromtimestamp(stat.st_mtime).isoformat(timespec="seconds"),
                }
            )
        return records

    def save_and_rebuild(self, original_name: str, file_bytes: bytes) -> dict:
        suffix = Path(original_name).suffix.lower()
        safe_name = self._safe_file_name(original_name)
        target_name = f"{Path(safe_name).stem}.md"
        target_path = self.settings.docs_dir / target_name

        if suffix == ".pdf":
            content = self._extract_pdf_to_markdown(file_bytes, original_name)
            source_type = "pdf"
        elif suffix in {".md", ".markdown", ".txt"}:
            content = file_bytes.decode("utf-8", errors="ignore")
            source_type = "markdown"
        else:
            raise ValueError("仅支持 Markdown、TXT 和 PDF 文件。")

        target_path.write_text(content, encoding="utf-8")
        manifest = self._load_manifest()
        manifest[target_name] = {
            "display_name": original_name,
            "source_type": source_type,
        }
        self._save_manifest(manifest)
        chunk_count = self.ingestor.ingest()
        return {
            "file_name": target_name,
            "display_name": original_name,
            "chunk_count": chunk_count,
        }

    def delete_document(self, file_name: str) -> dict:
        target_path = self.settings.docs_dir / file_name
        if not target_path.exists():
            raise ValueError("文档不存在。")
        target_path.unlink()
        manifest = self._load_manifest()
        manifest.pop(file_name, None)
        self._save_manifest(manifest)
        chunk_count = self.ingestor.ingest()
        return {"file_name": file_name, "chunk_count": chunk_count}

    def _extract_pdf_to_markdown(self, file_bytes: bytes, original_name: str) -> str:
        temp_path = self.settings.docs_dir / f"__temp__{Path(original_name).name}"
        temp_path.write_bytes(file_bytes)
        try:
            reader = PdfReader(str(temp_path))
            chunks = [page.extract_text() or "" for page in reader.pages]
        finally:
            if temp_path.exists():
                temp_path.unlink()

        text = "\n\n".join(part.strip() for part in chunks if part.strip())
        if not text:
            raise ValueError("PDF 未提取到可用文本，请确认文档不是扫描图片版。")

        return f"# {Path(original_name).stem}\n\n{text}\n"

    def _load_manifest(self) -> dict:
        return json.loads(self.manifest_path.read_text(encoding="utf-8"))

    def _save_manifest(self, manifest: dict) -> None:
        self.manifest_path.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def _safe_file_name(self, file_name: str) -> str:
        normalized = re.sub(r"[^0-9a-zA-Z\u4e00-\u9fa5._-]+", "_", file_name)
        return normalized.strip("._") or "uploaded_document.md"
