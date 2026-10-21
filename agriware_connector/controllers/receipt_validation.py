import json
import logging
import math

from odoo import http
from odoo.http import request, Response
from odoo.exceptions import AccessError, UserError, ValidationError
from .api_security import require_agriware_api_user

_logger = logging.getLogger(__name__)


class AgriwareReceiptValidationAPI(http.Controller):

    @staticmethod
    def json_response(data, status=200):
        return Response(
            json.dumps(data),
            status=status,
            content_type="application/json",
        )

    @http.route(
        "/agriware/api/v1/receipts/<int:receipt_id>/validate",
        type="http",
        auth="bearer",
        methods=["POST"],
        csrf=False,
        save_session=False,
    )
    def validate_receipt(self, receipt_id, **kwargs):

        authorization = request.httprequest.headers.get(
            "Authorization", ""
        )

        if not authorization.startswith("Bearer "):
            return self.json_response({
                "status": "error",
                "message": "Bearer token required",
            }, 401)

        if not require_agriware_api_user():
            return self.json_response({
                "status": "error",
                "message": "Access denied: AgriWare API User role required",
            }, 403)

        try:
            payload = json.loads(
                request.httprequest.get_data(as_text=True)
            )
        except (ValueError, UnicodeDecodeError):
            return self.json_response({
                "status": "error",
                "message": "Invalid JSON",
            }, 400)

        if not isinstance(payload, dict):
            return self.json_response({
                "status": "error",
                "message": "Expected JSON object",
            }, 400)

        external_reference = payload.get("external_reference")
        received_quantities = payload.get("received_quantities")

        if (
            not isinstance(external_reference, str)
            or not external_reference.strip()
            or len(external_reference) > 128
        ):
            return self.json_response({
                "status": "error",
                "message": "Invalid external_reference",
            }, 400)

        external_reference = external_reference.strip()

        if (
            not isinstance(received_quantities, list)
            or not received_quantities
            or len(received_quantities) > 100
        ):
            return self.json_response({
                "status": "error",
                "message": "Invalid received_quantities",
            }, 400)

        quantities = {}

        for line in received_quantities:
            if not isinstance(line, dict):
                return self.json_response({
                    "status": "error",
                    "message": "Invalid received quantity line",
                }, 400)

            product_id = line.get("product_id")
            quantity = line.get("quantity")

            if (
                type(product_id) is not int
                or product_id <= 0
                or type(quantity) not in (int, float)
                or not math.isfinite(quantity)
                or quantity <= 0
                or quantity > 1000000000
                or product_id in quantities
            ):
                return self.json_response({
                    "status": "error",
                    "message": "Invalid or duplicate product quantity",
                }, 400)

            quantities[product_id] = quantity

        try:
            env = request.env
            Picking = env["stock.picking"]
            Move = env["stock.move"]

            if (
                not Picking.has_access("read")
                or not Picking.has_access("write")
                or not Move.has_access("write")
            ):
                return self.json_response({
                    "status": "error",
                    "message": "Insufficient permissions",
                }, 403)

            # Lock the receipt to prevent simultaneous validation.
            env.cr.execute(
                """
                SELECT id
                FROM stock_picking
                WHERE id = %s
                FOR UPDATE NOWAIT
                """,
                (receipt_id,),
            )

            locked = env.cr.fetchone()

            if not locked:
                return self.json_response({
                    "status": "error",
                    "message": "Receipt not found",
                }, 404)

            # Refresh cached data after acquiring the lock.
            env.invalidate_all()

            receipt = Picking.search([
                ("id", "=", receipt_id),
                ("company_id", "in", env.companies.ids),
                ("picking_type_id.code", "=", "incoming"),
            ], limit=1)

            if not receipt:
                return self.json_response({
                    "status": "error",
                    "message": "Receipt not found",
                }, 404)

            if receipt.origin != external_reference:
                return self.json_response({
                    "status": "error",
                    "message": "External reference mismatch",
                }, 409)

            if receipt.state == "done":
                return self.json_response({
                    "status": "error",
                    "message": "Receipt already validated",
                    "receipt_id": receipt.id,
                }, 409)

            if receipt.state == "cancel":
                return self.json_response({
                    "status": "error",
                    "message": "Receipt is cancelled",
                }, 409)

            if receipt.state != "draft":
                return self.json_response({
                    "status": "error",
                    "message": "Only draft receipts can be validated",
                }, 409)

            # This API must not validate unrelated Odoo receipts.
            if not external_reference.startswith("AGRIWARE-RCPT-"):
                return self.json_response({
                    "status": "error",
                    "message": "Receipt is not managed by AgriWare",
                }, 403)

            moves = receipt.move_ids.filtered(
                lambda m: m.state != "cancel"
            )

            if not moves:
                return self.json_response({
                    "status": "error",
                    "message": "Receipt has no active product lines",
                }, 400)

            # Phase 8 supports one move per product.
            move_products = [move.product_id.id for move in moves]

            if len(move_products) != len(set(move_products)):
                return self.json_response({
                    "status": "error",
                    "message": "Duplicate products in receipt are unsupported",
                }, 400)

            if set(move_products) != set(quantities):
                return self.json_response({
                    "status": "error",
                    "message": "Received products do not match receipt",
                }, 400)

            for move in moves:
                quantity = quantities[move.product_id.id]

                # Initial implementation supports exact receipt quantities.
                # Partial receipts will be handled in a later phase.
                if not move.product_uom.is_zero(
                    quantity - move.product_uom_qty
                ):
                    return self.json_response({
                        "status": "error",
                        "message": "Received quantity must match expected quantity",
                    }, 400)

            # Confirm the draft and explicitly record received quantities.
            receipt.action_confirm()

            for move in moves:
                move.quantity = quantities[move.product_id.id]

            result = receipt.button_validate()

            if receipt.state != "done":
                env.cr.rollback()
                return self.json_response({
                    "status": "error",
                    "message": "Receipt requires additional validation",
                }, 409)

            return self.json_response({
                "status": "success",
                "receipt_id": receipt.id,
                "receipt_reference": receipt.name,
                "external_reference": receipt.origin,
                "state": receipt.state,
            }, 200)

        except AccessError:
            request.env.cr.rollback()
            return self.json_response({
                "status": "error",
                "message": "Access denied",
            }, 403)

        except (UserError, ValidationError) as exc:
            request.env.cr.rollback()
            _logger.warning(
                "AgriWare receipt validation rejected: %s", exc
            )
            return self.json_response({
                "status": "error",
                "message": "Odoo rejected receipt validation",
            }, 409)

        except Exception:
            request.env.cr.rollback()
            _logger.exception(
                "AgriWare receipt validation failed"
            )
            return self.json_response({
                "status": "error",
                "message": "Unable to validate receipt",
            }, 500)
