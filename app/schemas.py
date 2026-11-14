from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional

class LoginIn(BaseModel):
    username: str
    password: str

class OrderItemIn(BaseModel):
    product_id: int
    quantity: int = Field(gt=0, le=100000)
    unit_price: float = Field(gt=0, le=10000000)

class OrderCreateIn(BaseModel):
    supplier_id: int
    items: List[OrderItemIn] = Field(min_length=1)
    remark: Optional[str] = ""

class OrderUpdateIn(BaseModel):
    items: List[OrderItemIn] = Field(min_length=1)
    remark: Optional[str] = ""

class ReceiveIn(BaseModel):
    items: Optional[List[OrderItemIn]] = None

class OrderItemOut(BaseModel):
    product_id: int
    quantity: int
    unit_price: float
    line_amount: float
    model_config = ConfigDict(from_attributes=True)

class OrderOut(BaseModel):
    id: int
    supplier_id: int
    status: str
    total_amount: float
    remark: str
    items: List[OrderItemOut]
    model_config = ConfigDict(from_attributes=True)
