
import pytest


def test_create_order_and_verify_mysql(purchase_api, db):
    # 1. 准备采购订单数据
    order_data = {
        "supplier_id": 1001,
        "items": [
            {
                "product_id": 2001,
                "quantity": 10,
                "unit_price": 25
            }
        ],
        "remark": "第十六课API数据库联合测试"
    }

    # 2. 调用 API 创建订单
    response = purchase_api.create_order(order_data)

    # 3. 校验 API 响应
    assert response.status_code == 201

    response_data = response.json()

    assert response_data["code"] == 0

    order = response_data["data"]

    # 动态获取本次创建的订单 ID
    order_id = order["id"]

    assert order["status"] == "PENDING"
    assert order["total_amount"] == pytest.approx(250)

    # 4. 查询 MySQL 订单主表
    order_record = db.fetch_one(
        """
        SELECT id, supplier_id, status, total_amount, remark
        FROM purchase_orders
        WHERE id = %s
        """,
        (order_id,)
    )

    # 5. 校验订单主表数据
    assert order_record is not None
    assert order_record["id"] == order_id
    assert order_record["supplier_id"] == 1001
    assert order_record["status"] == "PENDING"
    assert order_record["total_amount"] == pytest.approx(250)
    assert order_record["remark"] == order_data["remark"]

    # 6. 查询 MySQL 订单明细表
    item_record = db.fetch_one(
        """
        SELECT order_id, product_id, quantity,
               unit_price, line_amount
        FROM purchase_order_items
        WHERE order_id = %s
        """,
        (order_id,)
    )

    # 7. 校验订单明细数据
    assert item_record is not None
    assert item_record["order_id"] == order_id
    assert item_record["product_id"] == 2001
    assert item_record["quantity"] == 10
    assert item_record["unit_price"] == pytest.approx(25)
    assert item_record["line_amount"] == pytest.approx(250)
