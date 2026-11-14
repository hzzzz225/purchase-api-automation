import requests
from config.settings import BASE_URL, REQUEST_TIMEOUT
from utils.test_data import build_order_data


def test_create_order(purchase_api):
    order_data = build_order_data()

    response = purchase_api.create_order(order_data)

    assert response.status_code == 201

    result = response.json()
    assert result["code"] == 0

    assert result["data"]["total_amount"] == 250.0
    assert result["data"]["status"] == "PENDING"

def test_purchase_order_full_process(purchase_api, api_client):
    # 1. 查询入库前库存
    products_response = api_client.get("/api/products")
    assert products_response.status_code == 200

    products = products_response.json()["items"]
    product = next(item for item in products if item["id"] == 2001)
    stock_before = product["stock"]

    # 2. 创建订单
    order_data = {
        "supplier_id": 1001,
        "items": [
            {
                "product_id": 2001,
                "quantity": 10,
                "unit_price": 25.0
            }
        ],
        "remark": "分层封装后的采购流程测试"
    }

    create_response = purchase_api.create_order(order_data)

    assert create_response.status_code == 201

    order_id = create_response.json()["data"]["id"]

    # 3. 审核订单
    approve_response = purchase_api.approve_order(order_id)

    assert approve_response.status_code == 200
    assert approve_response.json()["data"]["status"] == "APPROVED"

    # 4. 采购入库
    receive_response = purchase_api.receive_order(order_id)

    assert receive_response.status_code == 200
    assert receive_response.json()["data"]["status"] == "RECEIVED"

    # 5. 查询入库后的库存
    products_after_response = api_client.get("/api/products")

    assert products_after_response.status_code == 200

    products_after = products_after_response.json()["items"]
    product_after = next(
        item for item in products_after
        if item["id"] == 2001
    )

    stock_after = product_after["stock"]

    assert stock_after == stock_before + 10


def test_duplicate_approve(token):
    headers = {"Authorization": f"Bearer {token}"}

    # 1. 创建新订单
    order_data = {
        "supplier_id": 1001,
        "items": [
            {
                "product_id": 2001,
                "quantity": 10,
                "unit_price": 25.0
            }
        ],
        "remark": "重复审核测试"
    }

    create_response = requests.post(
        f"{BASE_URL}/api/purchase-orders",
        json=order_data,
        headers=headers,
        timeout=REQUEST_TIMEOUT
    )

    assert create_response.status_code == 201
    order_id = create_response.json()["data"]["id"]

    # 2. 第一次审核
    first_approve = requests.post(
        f"{BASE_URL}/api/purchase-orders/{order_id}/approve",
        headers=headers,
        timeout=REQUEST_TIMEOUT
    )

    assert first_approve.status_code == 200
    assert first_approve.json()["data"]["status"] == "APPROVED"

    # 3. 第二次审核，预期被拒绝
    second_approve = requests.post(
        f"{BASE_URL}/api/purchase-orders/{order_id}/approve",
        headers=headers,
        timeout=REQUEST_TIMEOUT
    )

    assert second_approve.status_code == 409

    # 4. 再执行正常入库，验证订单状态没有被异常操作破坏
    receive_response = requests.post(
        f"{BASE_URL}/api/purchase-orders/{order_id}/receive",
        headers=headers,
        timeout=REQUEST_TIMEOUT
    )

    assert receive_response.status_code == 200
    assert receive_response.json()["data"]["status"] == "RECEIVED"

    print("重复审核测试通过")


def test_query_products(api_client):
    response = api_client.get("/api/products")

    assert response.status_code == 200

    result = response.json()

    assert "items" in result

    print("商品查询成功")
    print("商品数量：", len(result["items"]))


    