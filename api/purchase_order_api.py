
class PurchaseOrderApi:

    def __init__(self, client):
        self.client = client

    def create_order(self, order_data):
        """
        创建采购订单
        """
        return self.client.post(
            "/api/purchase-orders",
            json=order_data
        )

    def approve_order(self, order_id):
        """
        审核采购订单
        """
        return self.client.post(
            f"/api/purchase-orders/{order_id}/approve"
        )

    def receive_order(self, order_id):
        """
        采购订单入库
        """
        return self.client.post(
            f"/api/purchase-orders/{order_id}/receive"
        )
