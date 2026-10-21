import hashlib
import json
import logging

from odoo import http
from odoo.http import request, Response
from odoo.exceptions import AccessError
from .api_security import require_agriware_api_user

_logger = logging.getLogger(__name__)


class AgriwareReceiptsAPI(http.Controller):

    @staticmethod
    def json_response(data, status=200):
        return Response(
            json.dumps(data),
            status=status,
            content_type="application/json",
        )

    @http.route(
        "/agriware/api/v1/receipts",
        type="http",
        auth="bearer",
        methods=["POST"],
        csrf=False,
        save_session=False,
    )
    def create_receipt(self, **kwargs):

        # Require an API key, not a browser session.
        authorization = request.httprequest.headers.get(
            "Authorization", ""
        )
        if not authorization.startswith("Bearer "):
            return self.json_response(
                {"status": "error", "message": "Bearer token required"},
                401,
            )

        if not require_agriware_api_user():
            return self.json_response(
                {
                    "status": "error",
                    "message": "Access denied: AgriWare API User role required",
                },
                403,
            )

        try:
            payload = json.loads(
                request.httprequest.get_data(as_text=True)
            )
        except (ValueError, UnicodeDecodeError):
            return self.json_response(
                {"status": "error", "message": "Invalid JSON"},
                400,
            )

        if not isinstance(payload, dict):
            return self.json_response(
                {"status": "error", "message": "Expected JSON object"},
                400,
            )

        external_reference = payload.get("external_reference")
        warehouse_id = payload.get("warehouse_id")
        supplier_id = payload.get("supplier_id")
        products = payload.get("products")

        if (
            not isinstance(external_reference, str)
            or not external_reference.strip()
            or len(external_reference) > 128
        ):
            return self.json_response(
                {"status": "error", "message": "Invalid external_reference"},
                400,
            )

        external_reference = external_reference.strip()

        if (
            type(warehouse_id) is not int
            or type(supplier_id) is not int
            or warehouse_id <= 0
            or supplier_id <= 0
        ):
            return self.json_response(
                {"status": "error", "message": "Invalid warehouse or supplier"},
                400,
            )

        if not isinstance(products, list) or not products:
            return self.json_response(
                {"status": "error", "message": "Products list required"},
                400,
            )

        if len(products) > 100:
            return self.json_response(
                {"status": "error", "message": "Too many product lines"},
                400,
            )

        try:
            env = request.env

            # Require explicit inventory permissions.
            Picking = env["stock.picking"]
            Move = env["stock.move"]

            if not Picking.has_access("create") or not Move.has_access(
                "create"
            ):
                return self.json_response(
                    {"status": "error", "message": "Insufficient permissions"},
                    403,
                )

            warehouse = env["stock.warehouse"].search([
                ("id", "=", warehouse_id),
                ("company_id", "in", env.companies.ids),
            ], limit=1)

            if not warehouse:
                return self.json_response(
                    {"status": "error", "message": "Warehouse not found"},
                    404,
                )

            supplier = env["res.partner"].search([
                ("id", "=", supplier_id),
            ], limit=1)

            if not supplier:
                return self.json_response(
                    {"status": "error", "message": "Supplier not found"},
                    404,
                )

            picking_type = warehouse.in_type_id

            if not picking_type:
                return self.json_response(
                    {"status": "error", "message": "Incoming operation unavailable"},
                    400,
                )

            # Validate every product before creating any records.
            move_values = []

            for line in products:
                if not isinstance(line, dict):
                    return self.json_response(
                        {"status": "error", "message": "Invalid product line"},
                        400,
                    )

                product_id = line.get("product_id")
                quantity = line.get("quantity")

                if (
                    type(product_id) is not int
                    or product_id <= 0
                    or type(quantity) not in (int, float)
                    or not (0 < quantity <= 1000000000)
                ):
                    return self.json_response(
                        {"status": "error", "message": "Invalid product or quantity"},
                        400,
                    )

                product = env["product.product"].search([
                    ("id", "=", product_id),
                    ("company_id", "in", [False, warehouse.company_id.id]),
                ], limit=1)

                if not product:
                    return self.json_response(
                        {"status": "error", "message": "Product not found"},
                        404,
                    )

                if product.type != "consu" or not product.is_storable:
                    return self.json_response(
                        {"status": "error", "message": "Product must be stock-tracked"},
                        400,
                    )

                move_values.append({
                    "product_id": product.id,
                    "product_uom_qty": quantity,
                    "product_uom": product.uom_id.id,
                    "location_id": picking_type.default_location_src_id.id,
                    "location_dest_id": picking_type.default_location_dest_id.id,
                    "company_id": warehouse.company_id.id,
                })

            # Serialize concurrent requests for the same external
            # reference so the duplicate check below cannot race.
            # The lock is transaction-scoped and releases automatically
            # on commit or rollback.
            lock_key = int.from_bytes(
                hashlib.sha256(
                    f"agriware_receipt:{picking_type.id}:"
                    f"{external_reference}".encode()
                ).digest()[:8],
                "big",
                signed=True,
            )
            env.cr.execute(
                "SELECT pg_advisory_xact_lock(%s)", (lock_key,)
            )

            existing = Picking.search([
                ("origin", "=", external_reference),
                ("picking_type_id", "=", picking_type.id),
            ], limit=1)

            if existing:
                return self.json_response({
                    "status": "error",
                    "message": "External reference already exists",
                    "receipt_id": existing.id,
                }, 409)

            picking = Picking.create({
                "partner_id": supplier.id,
                "picking_type_id": picking_type.id,
                "location_id": picking_type.default_location_src_id.id,
                "location_dest_id": picking_type.default_location_dest_id.id,
                "origin": external_reference,
                "company_id": warehouse.company_id.id,
            })

            for values in move_values:
                values["picking_id"] = picking.id

            Move.create(move_values)

            return self.json_response({
                "status": "success",
                "receipt_id": picking.id,
                "receipt_reference": picking.name,
                "external_reference": external_reference,
                "state": picking.state,
            }, 201)

        except AccessError:
            request.env.cr.rollback()
            return self.json_response(
                {"status": "error", "message": "Access denied"},
                403,
            )

        except Exception:
            request.env.cr.rollback()
            _logger.exception("AgriWare receipt creation failed")
            return self.json_response(
                {"status": "error", "message": "Unable to create receipt"},
                500,
            )
