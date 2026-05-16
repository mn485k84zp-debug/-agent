from __future__ import annotations

import json
import math
import re
from collections import defaultdict

import jieba
from langchain_chroma import Chroma
from langchain_core.documents import Document
from rank_bm25 import BM25Okapi

from src.core.config import Settings
from src.core.types import RetrievedPassage
from src.llm.factory import build_embeddings, build_reranker
from src.rag.query_rewriter import QueryRewriter


def tokenize_text(text: str) -> list[str]:
    """中英文混合分词。"""
    chinese_tokens = list(jieba.cut(text))
    latin_tokens = re.findall(r"[A-Za-z0-9_-]+", text.lower())
    tokens = [token.strip().lower() for token in chinese_tokens + latin_tokens if token.strip()]
    return tokens or [text.lower()]


class HybridRetriever:
    """向量检索 + BM25 + Rerank 的企业级混合检索器。"""

    def __init__(self, settings: Settings, llm) -> None:
        self.settings = settings
        self.rewriter = QueryRewriter(llm)
        self.embeddings = build_embeddings(settings)
        self.reranker = build_reranker(settings)
        self.vectorstore = Chroma(
            collection_name="knowledge_base",
            persist_directory=str(settings.chroma_dir),
            embedding_function=self.embeddings,
        )
        self.documents = self._load_documents()
        self.doc_map = {doc.metadata["chunk_id"]: doc for doc in self.documents}
        self.bm25 = BM25Okapi([tokenize_text(doc.page_content) for doc in self.documents]) if self.documents else None

    def retrieve(self, query: str) -> list[Document]:
        if not self.documents:
            return []

        rewritten = self.rewriter.rewrite(query)
        candidate_queries = [rewritten.normalized_query] + rewritten.rewritten_queries
        candidate_queries = list(dict.fromkeys(item for item in candidate_queries if item))

        fused_scores = defaultdict(float)

        for candidate in candidate_queries:
            for rank, item in enumerate(self._vector_search(candidate), start=1):
                chunk_id = item.document.metadata["chunk_id"]
                fused_scores[chunk_id] += self._rrf(rank)

            for rank, item in enumerate(self._bm25_search(candidate), start=1):
                chunk_id = item.document.metadata["chunk_id"]
                fused_scores[chunk_id] += self._rrf(rank)

        top_candidates = sorted(fused_scores.items(), key=lambda x: x[1], reverse=True)[:20]
        rerank_docs = [self.doc_map[chunk_id] for chunk_id, _ in top_candidates]
        reranked = self._rerank(rewritten.normalized_query, rerank_docs)
        return reranked[: self.settings.rerank_top_k]

    def _load_documents(self) -> list[Document]:
        if not self.settings.docs_index_path.exists():
            return []

        payload = json.loads(self.settings.docs_index_path.read_text(encoding="utf-8"))
        return [
            Document(page_content=item["page_content"], metadata=item["metadata"])
            for item in payload
        ]

    def _vector_search(self, query: str) -> list[RetrievedPassage]:
        docs_and_scores = self.vectorstore.similarity_search_with_relevance_scores(
            query=query,
            k=min(self.settings.vector_top_k, len(self.documents)),
        )
        results: list[RetrievedPassage] = []
        for doc, score in docs_and_scores:
            results.append(
                RetrievedPassage(document=doc, score=float(score), source="vector")
            )
        return results

    def _bm25_search(self, query: str) -> list[RetrievedPassage]:
        if not self.bm25:
            return []

        tokens = tokenize_text(query)
        scores = self.bm25.get_scores(tokens)
        ranked_indices = sorted(
            range(len(scores)),
            key=lambda idx: scores[idx],
            reverse=True,
        )[: min(self.settings.bm25_top_k, len(scores))]

        return [
            RetrievedPassage(
                document=self.documents[idx],
                score=float(scores[idx]),
                source="bm25",
            )
            for idx in ranked_indices
            if scores[idx] > 0
        ]

    def _rerank(self, query: str, docs: list[Document]) -> list[Document]:
        if not docs:
            return []

        try:
            results = self.reranker.rerank(
                query=query,
                documents=[doc.page_content for doc in docs],
                top_n=min(self.settings.rerank_top_k, len(docs)),
            )
            reranked_docs: list[Document] = []
            for item in results:
                index = item.get("index")
                if index is None:
                    continue
                reranked_docs.append(docs[index])
            return reranked_docs or docs[: self.settings.rerank_top_k]
        except Exception:
            # Rerank 异常时回退到融合召回结果，避免服务中断。
            return docs[: self.settings.rerank_top_k]

    def _rrf(self, rank: int, k: int = 60) -> float:
        return 1.0 / (k + rank)
