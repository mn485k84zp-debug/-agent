from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(PROJECT_ROOT))

from src.core.config import get_settings


def main() -> None:
    settings = get_settings()

    with sqlite3.connect(settings.sqlite_db_path) as conn:
        conn.executescript(
            """
            DROP TABLE IF EXISTS order_items;
            DROP TABLE IF EXISTS orders;
            DROP TABLE IF EXISTS products;
            DROP TABLE IF EXISTS customers;

            CREATE TABLE customers (
                customer_id INTEGER PRIMARY KEY,
                customer_name TEXT NOT NULL,
                membership_level TEXT NOT NULL,
                city TEXT NOT NULL
            );

            CREATE TABLE products (
                product_id INTEGER PRIMARY KEY,
                sku TEXT NOT NULL,
                product_name TEXT NOT NULL,
                category TEXT NOT NULL,
                stock_qty INTEGER NOT NULL,
                sale_price REAL NOT NULL
            );

            CREATE TABLE orders (
                order_id TEXT PRIMARY KEY,
                customer_id INTEGER NOT NULL,
                order_status TEXT NOT NULL,
                payment_amount REAL NOT NULL,
                logistics_tracking_no TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY(customer_id) REFERENCES customers(customer_id)
            );

            CREATE TABLE order_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id TEXT NOT NULL,
                product_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL,
                unit_price REAL NOT NULL,
                FOREIGN KEY(order_id) REFERENCES orders(order_id),
                FOREIGN KEY(product_id) REFERENCES products(product_id)
            );
            """
        )

        conn.executemany(
            "INSERT INTO customers VALUES (?, ?, ?, ?)",
            [
                (1, "张敏", "gold", "上海"),
                (2, "王磊", "silver", "杭州"),
                (3, "李娜", "vip", "深圳"),
            ],
        )

        conn.executemany(
            "INSERT INTO products VALUES (?, ?, ?, ?, ?, ?)",
            [
                (1, "SKU-TSHIRT-001", "速干运动T恤", "服饰", 125, 99.0),
                (2, "SKU-SHOES-002", "轻量跑鞋", "鞋靴", 64, 399.0),
                (3, "SKU-BAG-003", "城市通勤双肩包", "箱包", 42, 259.0),
            ],
        )

        conn.executemany(
            "INSERT INTO orders VALUES (?, ?, ?, ?, ?, ?)",
            [
                ("ORD-1001", 1, "已发货", 498.0, "SF123456789", "2026-04-01 10:05:00"),
                ("ORD-1002", 2, "待发货", 99.0, None, "2026-04-02 14:20:00"),
                ("ORD-1003", 3, "已完成", 658.0, "YT987654321", "2026-04-03 09:15:00"),
                ("ORD-1004", 1, "已完成", 399.0, "JD112233445", "2026-04-05 20:30:00"),
            ],
        )

        conn.executemany(
            "INSERT INTO order_items (order_id, product_id, quantity, unit_price) VALUES (?, ?, ?, ?)",
            [
                ("ORD-1001", 2, 1, 399.0),
                ("ORD-1001", 1, 1, 99.0),
                ("ORD-1002", 1, 1, 99.0),
                ("ORD-1003", 3, 1, 259.0),
                ("ORD-1003", 2, 1, 399.0),
                ("ORD-1004", 2, 1, 399.0),
            ],
        )

        conn.commit()

    print(f"示例数据库已初始化: {settings.sqlite_db_path}")


if __name__ == "__main__":
    main()
