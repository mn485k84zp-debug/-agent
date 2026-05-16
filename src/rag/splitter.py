from __future__ import annotations

import re
from pathlib import Path

from langchain_core.documents import Document


class MarkdownSemanticSplitter:
    """基于 Markdown 标题与语义块的切分器。

    不按固定字符数硬切，而是优先保留完整标题层级和自然段语义边界。
    当某一节过长时，只会在段落边界继续拆分，不会粗暴截断句子。
    """

    heading_pattern = re.compile(r"^(#{1,6})\s+(.*)$")

    def __init__(self, max_block_chars: int = 900) -> None:
        self.max_block_chars = max_block_chars

    def split_file(self, file_path: Path) -> list[Document]:
        text = file_path.read_text(encoding="utf-8")
        return self.split_text(text=text, source=file_path.name)

    def split_text(self, text: str, source: str) -> list[Document]:
        lines = text.splitlines()
        heading_stack: list[str] = []
        sections: list[tuple[list[str], list[str]]] = []
        buffer: list[str] = []

        for line in lines:
            match = self.heading_pattern.match(line.strip())
            if match:
                if buffer:
                    sections.append((heading_stack.copy(), buffer.copy()))
                    buffer.clear()

                level = len(match.group(1))
                title = match.group(2).strip()
                heading_stack = heading_stack[: level - 1]
                heading_stack.append(title)
                continue

            buffer.append(line)

        if buffer:
            sections.append((heading_stack.copy(), buffer.copy()))

        documents: list[Document] = []
        chunk_counter = 0

        for headings, section_lines in sections:
            paragraphs = self._split_paragraphs(section_lines)
            for merged_block in self._merge_paragraphs(paragraphs):
                heading_path = " > ".join(headings) if headings else "根节点"
                page_content = f"标题路径: {heading_path}\n\n{merged_block}".strip()
                documents.append(
                    Document(
                        page_content=page_content,
                        metadata={
                            "source": source,
                            "heading_path": heading_path,
                            "chunk_id": f"{source}-{chunk_counter}",
                        },
                    )
                )
                chunk_counter += 1

        return documents

    def _split_paragraphs(self, lines: list[str]) -> list[str]:
        paragraphs: list[str] = []
        buffer: list[str] = []

        for line in lines:
            stripped = line.rstrip()
            if not stripped:
                if buffer:
                    paragraphs.append("\n".join(buffer).strip())
                    buffer.clear()
                continue
            buffer.append(stripped)

        if buffer:
            paragraphs.append("\n".join(buffer).strip())

        return [item for item in paragraphs if item]

    def _merge_paragraphs(self, paragraphs: list[str]) -> list[str]:
        """只在段落边界做合并，保证语义完整。"""
        merged: list[str] = []
        current = ""
        for paragraph in paragraphs:
            if not current:
                current = paragraph
                continue

            candidate = f"{current}\n\n{paragraph}"
            if len(candidate) <= self.max_block_chars:
                current = candidate
            else:
                merged.append(current)
                current = paragraph

        if current:
            merged.append(current)
        return merged
