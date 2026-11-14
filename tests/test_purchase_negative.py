
import requests
import pytest

from config.settings import BASE_URL, REQUEST_TIMEOUT
from utils.test_data import build_order_data

pytestmark = pytest.mark.ui

@pytest.mark.parametrize(
    "invalid_case",
    ["missing_quantity", "wrong_quantity_type"]
)
def test_create_order_invalid_parameters(
    api_client, db, invalid_case
):
    # 1. 生成唯一测试数据
    order_data = build_order_data(
        supplier_id=1001,
        product_id=2001,
        quantity=10,
        unit_price=25
    )

    remark = order_data["remark"]

    # 2. 构造异常参数
    if invalid_case == "missing_quantity":
        del order_data["items"][0]["quantity"]

    elif invalid_case == "wrong_quantity_type":
        order_data["items"][0]["quantity"] = "abc"

    # 3. 发送请求
    response = api_client.post(
        "/api/purchase-orders",
        json=order_data
    )

    # 4. 校验参数校验失败
    assert response.status_code == 422

    # 5. 校验数据库没有产生订单
    db.connection.commit()

    order_record = db.fetch_one(
        """
        SELECT id
        FROM purchase_orders
        WHERE remark = %s
        """,
        (remark,)
    )

    assert order_record is None


@pytest.mark.parametrize(
    "auth_header",
    [
        None,
        "Bearer invalid-test-token"
    ],
    ids=["missing_token", "invalid_token"]
)
def test_create_order_authentication_failure(
    db, auth_header
):
    # 1. 生成有效业务数据
    order_data = build_order_data(
        supplier_id=1001,
        product_id=2001,
        quantity=10,
        unit_price=25
    )

    remark = order_data["remark"]

    # 2. 构造请求头
    headers = {}

    if auth_header is not None:
        headers["Authorization"] = auth_header

    # 3. 不使用已登录的 ApiClient，直接发送请求
    response = requests.post(
        f"{BASE_URL}/api/purchase-orders",
        json=order_data,
        headers=headers,
        timeout=REQUEST_TIMEOUT
    )

    # 4. 未认证请求必须被拒绝
    assert response.status_code in (401, 403)

    # 5. 校验没有创建订单
    db.connection.commit()

    order_record = db.fetch_one(
        """
        SELECT id
        FROM purchase_orders
        WHERE remark = %s
        """,
        (remark,)
    )

    assert order_record is None
