from pydantic import BaseModel, Field


class OrderStatusInput(BaseModel):
    """查询订单状态的输入。"""

    order_id: str = Field(description="订单编号，例如 ORD-1001")


class ProductInventoryInput(BaseModel):
    """查询库存的输入。"""

    product_name: str = Field(description="商品名称或 SKU 关键字")


class AfterSalesTicketInput(BaseModel):
    """创建售后工单的输入。"""

    order_id: str = Field(description="订单编号")
    issue_type: str = Field(description="问题类型，例如 退款、换货、物流异常")
    details: str = Field(description="问题详情")
