from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Callable

from langchain_core.tools import StructuredTool

from src.core.config import Settings
from src.llm.factory import build_embeddings
from src.tools.implementations import build_tool_functions
from src.tools.schemas import AfterSalesTicketInput, OrderStatusInput, ProductInventoryInput


@dataclass
class ManagedTool:
    """工具定义与检索描述。"""

    name: str
    description: str
    args_schema: type
    func: Callable[..., str]

    def to_langchain_tool(self) -> StructuredTool:
        return StructuredTool.from_function(
            func=self.func,
            name=self.name,
            description=self.description,
            args_schema=self.args_schema,
            return_direct=False,
        )

    @property
    def searchable_text(self) -> str:
        return f"{self.name}\n{self.description}\n{self.args_schema.model_json_schema()}"


class ToolRegistry:
    """Tool RAG 注册中心。"""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.embeddings = build_embeddings(settings)
        functions = build_tool_functions(settings)

        self.tools = {
            "lookup_order_status": ManagedTool(
                name="lookup_order_status",
                description="查询电商订单状态、支付金额和物流单号。适用于用户追问具体订单进度。",
                args_schema=OrderStatusInput,
                func=functions["lookup_order_status"],
            ),
            "lookup_product_inventory": ManagedTool(
                name="lookup_product_inventory",
                description="查询商品库存和售价。适用于用户咨询商品是否有货、剩余库存和价格。",
                args_schema=ProductInventoryInput,
                func=functions["lookup_product_inventory"],
            ),
            "create_after_sales_ticket": ManagedTool(
                name="create_after_sales_ticket",
                description="创建售后工单。适用于退款、换货、物流异常等场景。",
                args_schema=AfterSalesTicketInput,
                func=functions["create_after_sales_ticket"],
            ),
        }
        self._tool_vectors = {
            name: self.embeddings.embed_query(tool.searchable_text)
            for name, tool in self.tools.items()
        }

    def retrieve(self, query: str, top_k: int | None = None) -> list[StructuredTool]:
        top_k = top_k or self.settings.tool_route_top_k
        query_vector = self.embeddings.embed_query(query)
        scored = []
        for name, vector in self._tool_vectors.items():
            scored.append((name, cosine_similarity(query_vector, vector)))
        scored.sort(key=lambda x: x[1], reverse=True)
        return [self.tools[name].to_langchain_tool() for name, _ in scored[:top_k]]


def cosine_similarity(vector_a: list[float], vector_b: list[float]) -> float:
    numerator = sum(a * b for a, b in zip(vector_a, vector_b))
    left = math.sqrt(sum(a * a for a in vector_a))
    right = math.sqrt(sum(b * b for b in vector_b))
    if left == 0 or right == 0:
        return 0.0
    return numerator / (left * right)
