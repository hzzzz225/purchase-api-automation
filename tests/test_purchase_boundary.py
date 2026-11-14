
import allure
import pytest

from utils.test_data import build_order_data

pytestmark = pytest.mark.api

@allure.feature("采购订单管理")
@allure.story("采购订单数量边界测试")
@allure.title("采购订单数量边界校验: quantity={quantity}")
@pytest.mark.parametrize(
    "quantity, expected_status",
    [
        (10, 201),   # 正常值
        (1, 201),    # 最小有效值
        (0, 422),    # 下边界非法值
        (-1, 422),   # 负数非法值
    ]
)
def test_create_order_quantity_boundary(
    purchase_api, db, quantity, expected_status
):
    # 步骤1：准备测试数据
    with allure.step("1. 生成独立采购订单测试数据"):
        order_data = build_order_data(
            supplier_id=1001,
            product_id=2001,
            quantity=quantity,
            unit_price=25
        )

        remark = order_data["remark"]

        allure.attach(
            str(order_data),
            name="本次请求测试数据",
            attachment_type=allure.attachment_type.TEXT
        )

    # 步骤2：调用创建订单接口
    with allure.step("2. 发送创建采购订单请求"):
        response = purchase_api.create_order(order_data)

        allure.attach(
            response.text,
            name="接口响应内容",
            attachment_type=allure.attachment_type.JSON
        )

    # 步骤3：校验 HTTP 状态码
    with allure.step(
        f"3. 校验 HTTP 状态码，预期为 {expected_status}"
    ):
        assert response.status_code == expected_status

    # 步骤4：结束测试连接可能存在的旧读取事务
    with allure.step("4. 结束数据库旧读取事务"):
        db.connection.commit()

    # 步骤5：查询订单主表
    with allure.step("5. 查询 MySQL 采购订单主表"):
        order_record = db.fetch_one(
            """
            SELECT id, status, total_amount, remark
            FROM purchase_orders
            WHERE remark = %s
            """,
            (remark,)
        )

    if expected_status == 201:

        # 步骤6：校验正常创建结果
        with allure.step("6. 校验订单创建响应及主表数据"):
            response_data = response.json()["data"]

            assert response.json()["code"] == 0
            assert order_record is not None
            assert order_record["id"] == response_data["id"]
            assert order_record["status"] == "PENDING"

        # 步骤7：校验订单金额
        with allure.step("7. 校验采购订单总金额"):
            expected_amount = quantity * 25

            assert (
                float(order_record["total_amount"])
                == expected_amount
            )

        # 步骤8：查询并校验订单明细
        with allure.step("8. 查询 MySQL 采购订单明细"):
            item_record = db.fetch_one(
                """
                SELECT product_id, quantity, unit_price, line_amount
                FROM purchase_order_items
                WHERE order_id = %s
                """,
                (order_record["id"],)
            )

            assert item_record is not None
            assert item_record["product_id"] == 2001
            assert item_record["quantity"] == quantity
            assert float(item_record["line_amount"]) == expected_amount

    else:

        # 步骤9：校验非法数量没有产生订单
        with allure.step("9. 校验非法数量未创建采购订单"):
            assert order_record is None
