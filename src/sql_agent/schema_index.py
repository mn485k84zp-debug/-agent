from __future__ import annotations

import sqlite3

from langchain_chroma import Chroma
from langchain_core.documents import Document

from src.core.config import Settings
from src.llm.factory import build_embeddings


class SchemaIndexer:
    """数据库 Schema 向量索引器。"""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.embeddings = build_embeddings(settings)
        self.vectorstore = Chroma(
            collection_name="schema_index",
            persist_directory=str(settings.chroma_dir),
            embedding_function=self.embeddings,
        )

    def build(self) -> int:
        docs = self._introspect_tables()
        if not docs:
            return 0

        ids = [doc.metadata["table_name"] for doc in docs]
        try:
            self.vectorstore.delete(ids=ids)
        except Exception:
            pass
        self.vectorstore.add_documents(docs, ids=ids)
        return len(docs)

    def retrieve(self, query: str, top_k: int) -> list[Document]:
        return self.vectorstore.similarity_search(query=query, k=top_k)

    def _introspect_tables(self) -> list[Document]:
        docs: list[Document] = []
        with sqlite3.connect(self.settings.sqlite_db_path) as conn:
            tables = conn.execute(
                """
                SELECT name
                FROM sqlite_master
                WHERE type = 'table' AND name NOT LIKE 'sqlite_%'
                ORDER BY name
                """
            ).fetchall()

            for (table_name,) in tables:
                columns = conn.execute(f"PRAGMA table_info('{table_name}')").fetchall()
                column_lines = []
                for _, name, col_type, notnull, default_value, pk in columns:
                    comment = self._guess_column_comment(name)
                    column_lines.append(
                        f"- {name} {col_type} | notnull={notnull} | pk={pk} | default={default_value} | 说明={comment}"
                    )

                text = (
                    f"表名: {table_name}\n"
                    f"业务说明: {self._guess_table_comment(table_name)}\n"
                    "字段定义:\n"
                    + "\n".join(column_lines)
                )
                docs.append(
                    Document(
                        page_content=text,
                        metadata={"table_name": table_name},
                    )
                )
        return docs

    def _guess_table_comment(self, table_name: str) -> str:
        mapping = {
            "customers": "会员与客户基础信息",
            "products": "商品主数据、库存与售价",
            "orders": "订单主表，记录状态、金额与下单时间",
            "order_items": "订单明细表，记录订单中的商品项",
        }
        return mapping.get(table_name, "业务表")

    def _guess_column_comment(self, column_name: str) -> str:
        mapping = {
            "customer_id": "客户主键",
            "customer_name": "客户姓名",
            "membership_level": "会员等级",
            "order_id": "订单编号",
            "order_status": "订单状态",
            "payment_amount": "实付金额",
            "created_at": "创建时间",
            "product_id": "商品主键",
            "product_name": "商品名称",
            "sale_price": "售价",
            "stock_qty": "库存数量",
            "quantity": "购买数量",
        }
        return mapping.get(column_name, "业务字段")
