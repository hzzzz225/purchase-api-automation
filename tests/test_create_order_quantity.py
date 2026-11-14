
import pytest
from utils.test_data import build_order_data


@pytest.mark.parametrize(
    "quantity, expected_status",
    [
        (10, 201),
        (1, 201),
        (0, 422),
        (-1, 422)
    ]
)
def test_create_order_with_different_quantity(
    purchase_api,
    quantity,
    expected_status
):
    order_data = build_order_data(quantity=quantity)

    response = purchase_api.create_order(order_data)

    assert response.status_code == expected_status
