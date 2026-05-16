import sqlite3
import random
from datetime import datetime, timedelta

# 连接数据库，自动生成测试库文件
conn = sqlite3.connect('test_ecommerce.db')
cursor = conn.cursor()

# 建订单表
cursor.execute('''
CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_time DATETIME,
    product_category TEXT,
    amount FLOAT,
    user_id INTEGER
)
''')

# 建商品表
cursor.execute('''
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    category TEXT,
    price FLOAT,
    stock INTEGER
)
''')

# 插入3个月的测试订单数据
categories = ['电子产品', '服装', '食品', '家居']
start_date = datetime.now() - timedelta(days=90)
for i in range(300):
    order_time = start_date + timedelta(days=random.randint(0, 90), hours=random.randint(0,23))
    category = random.choice(categories)
    amount = round(random.uniform(50, 1000), 2)
    cursor.execute('INSERT INTO orders (order_time, product_category, amount, user_id) VALUES (?, ?, ?, ?)',
                   (order_time.strftime('%Y-%m-%d %H:%M:%S'), category, amount, random.randint(1, 100)))

# 插入测试商品数据
products = [
    ('iPhone 15', '电子产品', 5999, 100),
    ('纯棉T恤', '服装', 99, 500),
   ('进口车厘子', '食品', 129, 200),
   ('收纳箱', '家居', 49, 300)
]
for p in products:
    cursor.execute('INSERT INTO products (name, category, price, stock) VALUES (?, ?, ?, ?)', p)

conn.commit()
conn.close()
print("测试数据库初始化完成！")