
from collections import defaultdict
from pymysql.cursors import DictCursor


def cleanup_auto_test_data(db, remark_prefix="AUTO_TEST_"):
    """
    清理指定前缀的自动化测试订单。

    已入库订单先恢复库存，再删除业务记录。
    所有操作在同一个事务中执行。
    """

    if not remark_prefix.startswith("AUTO_TEST_"):
        raise ValueError("清理前缀必须以 AUTO_TEST_ 开头")

    connection = db.connection

    # 结束之前可能存在的只读事务
    connection.commit()

    params = (len(remark_prefix), remark_prefix)

    try:
        connection.begin()

        with connection.cursor(DictCursor) as cursor:

            # 1. 查询并锁定测试订单
            cursor.execute(
                """
                SELECT id, status
                FROM purchase_orders
                WHERE LEFT(remark, %s) = %s
                FOR UPDATE
                """,
                params
            )

            orders = cursor.fetchall()

            if not orders:
                connection.commit()
                return {
                    "orders": 0,
                    "items": 0,
                    "movements": 0,
                    "restored_stock": {},
                    "message": "没有需要清理的测试订单"
                }

            # 2. 查询订单明细
            cursor.execute(
                """
                SELECT order_id, product_id, SUM(quantity) AS quantity
                FROM purchase_order_items
                WHERE order_id IN (
                    SELECT id
                    FROM purchase_orders
                    WHERE LEFT(remark, %s) = %s
                )
                GROUP BY order_id, product_id
                """,
                params
            )

            item_rows = cursor.fetchall()

            expected = defaultdict(int)

            for row in item_rows:
                expected[
                    (row["order_id"], row["product_id"])
                ] += row["quantity"]

            # 3. 查询库存流水
            cursor.execute(
                """
                SELECT order_id, product_id, quantity, movement_type
                FROM stock_movements
                WHERE order_id IN (
                    SELECT id
                    FROM purchase_orders
                    WHERE LEFT(remark, %s) = %s
                )
                FOR UPDATE
                """,
                params
            )

            movements = cursor.fetchall()

            actual = defaultdict(int)

            for movement in movements:

                if movement["movement_type"] != "PURCHASE_IN":
                    raise ValueError(
                        f"发现非预期库存流水："
                        f"{movement['movement_type']}"
                    )

                actual[
                    (
                        movement["order_id"],
                        movement["product_id"]
                    )
                ] += movement["quantity"]

            # 4. 校验订单状态和库存流水
            for order in orders:

                order_id = order["id"]
                status = order["status"]

                order_expected = {
                    key: value
                    for key, value in expected.items()
                    if key[0] == order_id
                }

                order_actual = {
                    key: value
                    for key, value in actual.items()
                    if key[0] == order_id
                }

                if status == "RECEIVED":

                    if order_expected != order_actual:
                        raise ValueError(
                            f"订单 {order_id} 明细和库存流水不一致"
                        )

                elif status in ("PENDING", "APPROVED"):

                    if order_actual:
                        raise ValueError(
                            f"未入库订单 {order_id} 存在库存流水"
                        )

                else:
                    raise ValueError(
                        f"订单 {order_id} 状态异常：{status}"
                    )

            # 5. 恢复已入库订单库存
            restore_stock = defaultdict(int)

            for (order_id, product_id), quantity in actual.items():
                restore_stock[product_id] += quantity

            for product_id, quantity in restore_stock.items():

                cursor.execute(
                    """
                    UPDATE products
                    SET stock = stock - %s
                    WHERE id = %s AND stock >= %s
                    """,
                    (quantity, product_id, quantity)
                )

                if cursor.rowcount != 1:
                    raise ValueError(
                        f"商品 {product_id} 库存不足或不存在"
                    )

            # 6. 按外键依赖顺序删除

            cursor.execute(
                """
                DELETE FROM stock_movements
                WHERE order_id IN (
                    SELECT id
                    FROM purchase_orders
                    WHERE LEFT(remark, %s) = %s
                )
                """,
                params
            )

            movement_count = cursor.rowcount

            cursor.execute(
                """
                DELETE FROM purchase_order_items
                WHERE order_id IN (
                    SELECT id
                    FROM purchase_orders
                    WHERE LEFT(remark, %s) = %s
                )
                """,
                params
            )

            item_count = cursor.rowcount

            cursor.execute(
                """
                DELETE FROM purchase_orders
                WHERE LEFT(remark, %s) = %s
                """,
                params
            )

            order_count = cursor.rowcount

        connection.commit()

        return {
            "orders": order_count,
            "items": item_count,
            "movements": movement_count,
            "restored_stock": dict(restore_stock),
            "message": "测试数据清理成功"
        }

    except Exception:
        connection.rollback()
        raise
