from odoo.tests.common import tagged

from .common import AgriwareApiCommon


@tagged("-at_install", "post_install")
class TestAgriwareApiAuthorization(AgriwareApiCommon):
    """A valid API key is not enough: the owning user needs the AgriWare
    API User group (or a group that implies it)."""

    def test_plain_user_cannot_read_products(self):
        response = self._as_plain_user("/agriware/api/v1/products")
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()["status"], "error")

    def test_plain_user_cannot_read_warehouses(self):
        response = self._as_plain_user("/agriware/api/v1/warehouses")
        self.assertEqual(response.status_code, 403)

    def test_plain_user_cannot_read_inventory(self):
        response = self._as_plain_user("/agriware/api/v1/inventory")
        self.assertEqual(response.status_code, 403)

    def test_plain_user_cannot_create_receipt(self):
        response = self._as_plain_user(
            "/agriware/api/v1/receipts",
            json={
                "external_reference": "AGRIWARE-RCPT-AUTHZ-1",
                "warehouse_id": self.warehouse.id,
                "supplier_id": self.partner.id,
                "products": [{"product_id": self.product.id, "quantity": 10}],
            },
            method="POST",
        )
        self.assertEqual(response.status_code, 403)

    def test_plain_user_cannot_create_dispatch(self):
        response = self._as_plain_user(
            "/agriware/api/v1/dispatches",
            json={
                "external_reference": "AGRIWARE-DISP-AUTHZ-1",
                "warehouse_id": self.warehouse.id,
                "customer_id": self.partner.id,
                "products": [{"product_id": self.product.id, "quantity": 10}],
            },
            method="POST",
        )
        self.assertEqual(response.status_code, 403)

    def test_api_user_can_read_products(self):
        response = self._as_api_user("/agriware/api/v1/products")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "success")
