from fastapi import FastAPI, Depends, HTTPException, Header, Query
from sqlalchemy.orm import Session
from sqlalchemy import select
from .database import Base, engine, get_db
from .models import Supplier, Product, PurchaseOrder, PurchaseOrderItem, StockMovement
from .schemas import LoginIn, OrderCreateIn, OrderUpdateIn
from typing import Optional
from fastapi import Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pathlib import Path
from fastapi.responses import FileResponse

app = FastAPI(
    title="Purchase Training API",
    description="具有真实状态流转和 MySQL 持久化的采购业务模拟服务。所有数据仅用于自动化测试练习。",
    version="1.0.0"
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent


@app.get("/ui", include_in_schema=False)
def purchase_ui():
    ui_file = PROJECT_ROOT / "tests" / "ui" / "purchase.html"
    return FileResponse(ui_file, media_type="text/html")

Base.metadata.create_all(bind=engine)
TOKENS = {"training-token": "tester", "admin-training-token": "admin"}

security = HTTPBearer()

def require_user(
    credentials: HTTPAuthorizationCredentials = Security(security)
):
    token = credentials.credentials

    if token not in TOKENS:
        raise HTTPException(401, "Invalid token")

    return TOKENS[token]

def seed(db: Session):
    if db.scalar(select(Supplier.id).limit(1)) is not None:
        return
    db.add_all([
        Supplier(id=1001, name="星河办公用品有限公司", contact="张先生"),
        Supplier(id=1002, name="远航电子供应商", contact="李女士")
    ])
    db.add_all([
        Product(id=2001, name="A4打印纸", sku="PAPER-A4", unit_price=25.0, stock=100),
        Product(id=2002, name="无线键盘", sku="KB-WL", unit_price=89.0, stock=30),
        Product(id=2003, name="办公显示器", sku="MON-24", unit_price=699.0, stock=12)
    ])
    db.commit()

with next(get_db()) as init_db:
    seed(init_db)

@app.get("/health")
def health():
    return {"status": "ok", "service": "purchase-training-api"}

@app.post("/api/auth/login")
def login(payload: LoginIn):
    if payload.username == "tester" and payload.password == "Test1234":
        return {"access_token": "training-token", "token_type": "bearer"}
    if payload.username == "admin" and payload.password == "Admin1234":
        return {"access_token": "admin-training-token", "token_type": "bearer"}
    raise HTTPException(401, "用户名或密码错误")

@app.get("/api/suppliers")
def suppliers(db: Session = Depends(get_db), user=Depends(require_user)):
    rows = db.scalars(select(Supplier).order_by(Supplier.id)).all()
    return {"items": [{"id": x.id, "name": x.name, "contact": x.contact, "status": x.status} for x in rows]}

@app.get("/api/products")
def products(db: Session = Depends(get_db), user=Depends(require_user)):
    rows = db.scalars(select(Product).order_by(Product.id)).all()
    return {"items": [{"id": x.id, "name": x.name, "sku": x.sku, "unit_price": x.unit_price, "stock": x.stock, "status": x.status} for x in rows]}

def build_items(db: Session, item_inputs):
    result, total = [], 0.0
    for item in item_inputs:
        product = db.get(Product, item.product_id)
        if not product or product.status != "ACTIVE":
            raise HTTPException(400, f"商品 {item.product_id} 不存在或已停用")
        line = round(item.quantity * item.unit_price, 2)
        result.append(PurchaseOrderItem(
            product_id=item.product_id, quantity=item.quantity,
            unit_price=item.unit_price, line_amount=line
        ))
        total += line
    return result, round(total, 2)

def serialize_order(order):
    return {
        "id": order.id, "supplier_id": order.supplier_id, "status": order.status,
        "total_amount": order.total_amount, "remark": order.remark,
        "items": [{"product_id": x.product_id, "quantity": x.quantity,
                   "unit_price": x.unit_price, "line_amount": x.line_amount} for x in order.items]
    }

@app.post("/api/purchase-orders", status_code=201)
def create_order(payload: OrderCreateIn, db: Session = Depends(get_db), user=Depends(require_user)):
    supplier = db.get(Supplier, payload.supplier_id)
    if not supplier or supplier.status != "ACTIVE":
        raise HTTPException(400, "供应商不存在或已停用")
    items, total = build_items(db, payload.items)
    order = PurchaseOrder(supplier_id=payload.supplier_id, status="PENDING",
                          total_amount=total, remark=payload.remark or "")
    order.items = items
    db.add(order)
    db.commit()
    db.refresh(order)
    return {"code": 0, "message": "创建成功", "data": serialize_order(order)}

@app.get("/api/purchase-orders")
def list_orders(status: Optional[str] = None, page: int = Query(1, ge=1),
                page_size: int = Query(10, ge=1, le=100),
                db: Session = Depends(get_db), user=Depends(require_user)):
    stmt = select(PurchaseOrder).order_by(PurchaseOrder.id.desc())
    if status:
        stmt = stmt.where(PurchaseOrder.status == status)
    rows = db.scalars(stmt).all()
    start = (page - 1) * page_size
    return {"total": len(rows), "page": page, "page_size": page_size,
            "items": [serialize_order(x) for x in rows[start:start+page_size]]}

@app.get("/api/purchase-orders/{order_id}")
def get_order(order_id: int, db: Session = Depends(get_db), user=Depends(require_user)):
    order = db.get(PurchaseOrder, order_id)
    if not order:
        raise HTTPException(404, "采购订单不存在")
    return {"data": serialize_order(order)}

@app.put("/api/purchase-orders/{order_id}")
def update_order(order_id: int, payload: OrderUpdateIn, db: Session = Depends(get_db), user=Depends(require_user)):
    order = db.get(PurchaseOrder, order_id)
    if not order:
        raise HTTPException(404, "采购订单不存在")
    if order.status != "PENDING":
        raise HTTPException(409, "只有待审核订单可以修改")
    items, total = build_items(db, payload.items)
    order.items = items
    order.total_amount = total
    order.remark = payload.remark or ""
    db.commit()
    db.refresh(order)
    return {"data": serialize_order(order)}

@app.post("/api/purchase-orders/{order_id}/approve")
def approve_order(order_id: int, db: Session = Depends(get_db), user=Depends(require_user)):
    order = db.get(PurchaseOrder, order_id)
    if not order:
        raise HTTPException(404, "采购订单不存在")
    if order.status != "PENDING":
        raise HTTPException(409, f"当前状态 {order.status} 不允许审核")
    order.status = "APPROVED"
    db.commit()
    return {"message": "审核成功", "data": serialize_order(order)}

@app.post("/api/purchase-orders/{order_id}/receive")
def receive_order(order_id: int, db: Session = Depends(get_db), user=Depends(require_user)):
    order = db.get(PurchaseOrder, order_id)
    if not order:
        raise HTTPException(404, "采购订单不存在")
    if order.status != "APPROVED":
        raise HTTPException(409, f"当前状态 {order.status} 不允许入库")
    for item in order.items:
        product = db.get(Product, item.product_id)
        product.stock += item.quantity
        db.add(StockMovement(product_id=product.id, order_id=order.id,
                             quantity=item.quantity, movement_type="PURCHASE_IN"))
    order.status = "RECEIVED"
    db.commit()
    db.refresh(order)
    return {"message": "入库成功", "data": serialize_order(order)}

@app.post("/api/purchase-orders/{order_id}/cancel")
def cancel_order(order_id: int, db: Session = Depends(get_db), user=Depends(require_user)):
    order = db.get(PurchaseOrder, order_id)
    if not order:
        raise HTTPException(404, "采购订单不存在")
    if order.status not in ("PENDING", "APPROVED"):
        raise HTTPException(409, f"当前状态 {order.status} 不允许取消")
    order.status = "CANCELLED"
    db.commit()
    return {"message": "取消成功", "data": serialize_order(order)}

@app.get("/api/stock-movements")
def stock_movements(product_id: Optional[int] = None, db: Session = Depends(get_db), user=Depends(require_user)):
    stmt = select(StockMovement).order_by(StockMovement.id.desc())
    if product_id:
        stmt = stmt.where(StockMovement.product_id == product_id)
    rows = db.scalars(stmt).all()
    return {"items": [{"id": x.id, "product_id": x.product_id, "order_id": x.order_id,
                       "quantity": x.quantity, "movement_type": x.movement_type} for x in rows]}
