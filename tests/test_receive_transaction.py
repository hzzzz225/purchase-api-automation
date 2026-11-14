import pytest
from utils.test_data import build_order_data

pytestmark = pytest.mark.api

def test_receive_order_and_duplicate_receive(purchase_api, db):
    # 1. 创建采购订单
    order_data = build_order_data(
    supplier_id=1001,
    product_id=2001,
    quantity=10,
    unit_price=25
)

    create_response = purchase_api.create_order(order_data)
    assert create_response.status_code == 201

    order = create_response.json()["data"]
    order_id = order["id"]

    # 2. 审核订单
    approve_response = purchase_api.approve_order(order_id)
    assert approve_response.status_code == 200

    # 3. 查询入库前商品库存
    product_id = 2001

    product_before = db.fetch_one(
        """
        SELECT stock
        FROM products
        WHERE id = %s
        """,
        (product_id,)
    )

    assert product_before is not None
    stock_before = product_before["stock"]

    # 4. 查询当前订单对应的库存流水数量
    movement_before = db.fetch_one(
        """
        SELECT COUNT(*) AS movement_count
        FROM stock_movements
        WHERE order_id = %s
        """,
        (order_id,)
    )

    movement_count_before = movement_before["movement_count"]

    # 结束当前只读事务，释放旧的一致性快照
    db.connection.commit()

    # 5. 执行入库
    receive_response = purchase_api.receive_order(order_id)
    assert receive_response.status_code == 200

    # 6. 查询入库后的商品库存
    product_after = db.fetch_one(
        """
        SELECT stock
        FROM products
        WHERE id = %s
        """,
        (product_id,)
    )

    stock_after = product_after["stock"]

    # 7. 查询入库后的库存流水
    movement_after = db.fetch_one(
        """
        SELECT COUNT(*) AS movement_count
        FROM stock_movements
        WHERE order_id = %s
        """,
        (order_id,)
    )

    movement_count_after = movement_after["movement_count"]

    movement_record = db.fetch_one(
        """
        SELECT product_id, order_id, quantity, movement_type
        FROM stock_movements
        WHERE order_id = %s
        """,
        (order_id,)
    )

    # 8. 校验正常入库结果
    assert stock_after == stock_before + 10
    assert movement_count_after == movement_count_before + 1

    assert movement_record is not None
    assert movement_record["product_id"] == product_id
    assert movement_record["order_id"] == order_id
    assert movement_record["quantity"] == 10

    # 9. 校验订单状态
    order_record = db.fetch_one(
        """
        SELECT status
        FROM purchase_orders
        WHERE id = %s
        """,
        (order_id,)
    )

    assert order_record["status"] == "RECEIVED"

    # 10. 再次执行入库，验证重复操作
    duplicate_response = purchase_api.receive_order(order_id)

    assert duplicate_response.status_code == 409

    # 11. 再次查询库存
    product_final = db.fetch_one(
        """
        SELECT stock
        FROM products
        WHERE id = %s
        """,
        (product_id,)
    )

    movement_final = db.fetch_one(
        """
        SELECT COUNT(*) AS movement_count
        FROM stock_movements
        WHERE order_id = %s
        """,
        (order_id,)
    )

    # 12. 校验重复入库没有改变数据库
    assert product_final["stock"] == stock_after
    assert movement_final["movement_count"] == movement_count_after
