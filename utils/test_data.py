
from uuid import uuid4


def generate_test_remark(prefix="AUTO_TEST"):
    """
    为每次测试生成唯一标识。
    """
    return f"{prefix}_{uuid4().hex[:12]}"


def build_order_data(
    supplier_id=1001,
    product_id=2001,
    quantity=10,
    unit_price=25.0,
    remark=None
):
    if remark is None:
        remark = generate_test_remark()

    return {
        "supplier_id": supplier_id,
        "items": [
            {
                "product_id": product_id,
                "quantity": quantity,
                "unit_price": unit_price
            }
        ],
        "remark": remark
    }
