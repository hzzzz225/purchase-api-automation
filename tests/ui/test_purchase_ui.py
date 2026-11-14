
import json
from uuid import uuid4

import allure
import pytest

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select

from utils.database import Database
from utils.cleanup import cleanup_auto_test_data

from tests.ui.pages.purchase_page import (
    LoginPage,
    PurchasePage
)

pytestmark = pytest.mark.ui

BASE_URL = "http://127.0.0.1:8000"

SUPPLIER_ID = 1001
PRODUCT_ID = 2001
ORDER_QUANTITY = 10


@pytest.fixture
def db():
    """创建 MySQL 测试数据库连接"""

    database = Database()

    try:
        yield database
    finally:
        database.close()


@pytest.fixture
def driver():
    """创建 Selenium 浏览器实例"""

    browser = webdriver.Chrome()

    browser.maximize_window()

    try:
        yield browser
    finally:
        browser.quit()


@pytest.fixture
def test_context(db):
    """
    准备唯一测试备注，并在测试结束后清理
    只清理本次 UI 测试创建的订单。
    """

    product = db.fetch_one(
        "SELECT stock FROM products WHERE id = %s",
        (PRODUCT_ID,)
    )

    assert product is not None, "测试商品不存在"

    stock_before = product["stock"]

    # 结束查询事务，避免后续读取旧快照
    db.connection.commit()

    remark = f"AUTO_TEST_UI_{uuid4().hex[:12]}"

    yield {
        "remark": remark,
        "stock_before": stock_before
    }

    # 只清理本次唯一备注对应的订单
    result = cleanup_auto_test_data(
        db,
        remark_prefix=remark
    )

    print("\n========== UI 测试数据清理 ==========")
    print(json.dumps(result, ensure_ascii=False, indent=2))

    # 验证测试订单已删除
    remaining = db.fetch_one(
        """
        SELECT COUNT(*) AS total
        FROM purchase_orders
        WHERE remark = %s
        """,
        (remark,)
    )

    db.connection.commit()

    assert remaining["total"] == 0, "测试订单清理失败"

    # 验证库存恢复到测试前的值
    stock_after = db.fetch_one(
        "SELECT stock FROM products WHERE id = %s",
        (PRODUCT_ID,)
    )

    db.connection.commit()

    assert stock_after["stock"] == stock_before, (
        f"库存恢复异常，原库存={stock_before}，"
        f"清理后库存={stock_after['stock']}"
    )


@allure.feature("采购业务 UI 自动化")
@allure.story("采购订单完整业务流程")
@allure.title("UI自动化：登录、创建、审核、入库及数据库验证")
def test_purchase_order_ui_lifecycle(
    driver,
    db,
    test_context
):
    """
    完整业务流程：

    登录
      -> 创建采购订单
      -> 审核
      -> 入库
      -> MySQL 数据验证
      -> 自动清理
    """

    remark = test_context["remark"]
    stock_before = test_context["stock_before"]

    with allure.step("步骤1：打开采购管理页面"):
        driver.get(f"{BASE_URL}/ui")

        assert "采购管理" in driver.title

    with allure.step("步骤2：登录系统"):
        login_page = LoginPage(driver)

        result = login_page.login(
            "tester",
            "Test1234"
        )

        assert result == "登录成功"

    purchase_page = PurchasePage(driver)

    with allure.step("步骤3：确认页面商品库存与数据库一致"):
        Select(
            driver.find_element(By.ID, "product-id")
        ).select_by_value(str(PRODUCT_ID))

        stock_text = purchase_page.get_stock_info()

        assert str(stock_before) in stock_text, (
            f"页面库存与测试数据库不一致："
            f"页面={stock_text}，数据库={stock_before}"
        )

    with allure.step("步骤4：创建采购订单"):

        order_id = purchase_page.create_order(
            supplier_id=SUPPLIER_ID,
            product_id=PRODUCT_ID,
            quantity=ORDER_QUANTITY,
            remark=remark
        )

        assert order_id > 0

        assert purchase_page.get_order_status() == "PENDING"

    with allure.step("步骤5：审核采购订单"):

        status = purchase_page.approve_order()

        assert status == "APPROVED"

    with allure.step("步骤6：执行采购入库"):

        status = purchase_page.receive_order()

        assert status == "RECEIVED"

    with allure.step("步骤7：验证 MySQL 订单主表"):

        # 结束之前可能存在的事务
        db.connection.commit()

        order = db.fetch_one(
            """
            SELECT id, supplier_id, status, total_amount, remark
            FROM purchase_orders
            WHERE id = %s
            """,
            (order_id,)
        )

        assert order is not None
        assert order["supplier_id"] == SUPPLIER_ID
        assert order["status"] == "RECEIVED"
        assert order["remark"] == remark
        assert float(order["total_amount"]) == 250.0

    with allure.step("步骤8：验证 MySQL 订单明细"):

        items = db.fetch_all(
            """
            SELECT product_id, quantity, unit_price, line_amount
            FROM purchase_order_items
            WHERE order_id = %s
            """,
            (order_id,)
        )

        assert len(items) == 1
        assert items[0]["product_id"] == PRODUCT_ID
        assert items[0]["quantity"] == ORDER_QUANTITY
        assert float(items[0]["unit_price"]) == 25.0
        assert float(items[0]["line_amount"]) == 250.0

    with allure.step("步骤9：验证库存变化"):

        product = db.fetch_one(
            "SELECT stock FROM products WHERE id = %s",
            (PRODUCT_ID,)
        )

        expected_stock = stock_before + ORDER_QUANTITY

        assert product["stock"] == expected_stock

    with allure.step("步骤10：验证库存流水"):

        movements = db.fetch_all(
            """
            SELECT product_id, order_id, quantity, movement_type
            FROM stock_movements
            WHERE order_id = %s
            """,
            (order_id,)
        )

        assert len(movements) == 1

        assert movements[0]["product_id"] == PRODUCT_ID
        assert movements[0]["quantity"] == ORDER_QUANTITY
        assert movements[0]["movement_type"] == "PURCHASE_IN"

    db.connection.commit()

    allure.attach(
        json.dumps(
            {
                "order_id": order_id,
                "remark": remark,
                "status": order["status"],
                "total_amount": float(order["total_amount"]),
                "stock_before": stock_before,
                "stock_after": product["stock"],
                "quantity": ORDER_QUANTITY,
                "movement_count": len(movements)
            },
            ensure_ascii=False,
            indent=2
        ),
        name="采购订单数据库验证结果",
        attachment_type=allure.attachment_type.JSON
    )
