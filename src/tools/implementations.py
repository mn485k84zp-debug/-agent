from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from typing import Callable

from src.core.config import Settings
from src.core.exceptions import DeterministicToolError


def build_tool_functions(settings: Settings) -> dict[str, Callable[..., str]]:
    """构建工具函数集合。"""

    def lookup_order_status(order_id: str) -> str:
        """根据订单号查询订单状态、支付金额和物流单号。"""
        with sqlite3.connect(settings.sqlite_db_path) as conn:
            cursor = conn.execute(
                """
                SELECT order_id, order_status, payment_amount, logistics_tracking_no, created_at
                FROM orders
                WHERE order_id = ?
                """,
                (order_id,),
            )
            row = cursor.fetchone()

        if not row:
            raise DeterministicToolError(f"订单 {order_id} 不存在，请检查订单号。")

        return json.dumps(
            {
                "order_id": row[0],
                "order_status": row[1],
                "payment_amount": row[2],
                "logistics_tracking_no": row[3],
                "created_at": row[4],
            },
            ensure_ascii=False,
        )

    def lookup_product_inventory(product_name: str) -> str:
        """按商品名称关键字查询库存与售价。"""
        with sqlite3.connect(settings.sqlite_db_path) as conn:
            cursor = conn.execute(
                """
                SELECT product_name, sku, stock_qty, sale_price
                FROM products
                WHERE product_name LIKE ? OR sku LIKE ?
                ORDER BY stock_qty DESC
                LIMIT 5
                """,
                (f"%{product_name}%", f"%{product_name}%"),
            )
            rows = cursor.fetchall()

        if not rows:
            raise DeterministicToolError(f"没有找到与 {product_name} 相关的商品库存信息。")

        return json.dumps(
            [
                {
                    "product_name": row[0],
                    "sku": row[1],
                    "stock_qty": row[2],
                    "sale_price": row[3],
                }
                for row in rows
            ],
            ensure_ascii=False,
        )

    def create_after_sales_ticket(order_id: str, issue_type: str, details: str) -> str:
        """创建售后工单，并返回工单编号。"""
        ticket_path = settings.sqlite_db_path.parent / "after_sales_tickets.jsonl"
        ticket_id = f"TICKET-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        payload = {
            "ticket_id": ticket_id,
            "order_id": order_id,
            "issue_type": issue_type,
            "details": details,
            "created_at": datetime.now().isoformat(timespec="seconds"),
        }
        ticket_path.parent.mkdir(parents=True, exist_ok=True)
        with ticket_path.open("a", encoding="utf-8") as file:
            file.write(json.dumps(payload, ensure_ascii=False) + "\n")
        return json.dumps(payload, ensure_ascii=False)

    return {
        "lookup_order_status": lookup_order_status,
        "lookup_product_inventory": lookup_product_inventory,
        "create_after_sales_ticket": create_after_sales_ticket,
    }
