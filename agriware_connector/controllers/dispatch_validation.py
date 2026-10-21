import json
import logging
import math

from psycopg2 import errors

from odoo import http
from odoo.http import request, Response
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools.float_utils import float_compare
from .api_security import require_agriware_api_user

_logger = logging.getLogger(__name__)


class AgriwareDispatchValidationAPI(http.Controller):

    @staticmethod
    def json_response(data, status=200):
        return Response(
            json.dumps(data),
            status=status,
            content_type="application/json",
        )

    @http.route(
        "/agriware/api/v1/dispatches/<int:dispatch_id>/validate",
        type="http",
        auth="bearer",
        methods=["POST"],
        csrf=False,
        save_session=False,
    )
    def validate_dispatch(self, dispatch_id, **kwargs):

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
        dispatched_quantities = payload.get("dispatched_quantities")

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
            not isinstance(dispatched_quantities, list)
            or not dispatched_quantities
            or len(dispatched_quantities) > 100
        ):
            return self.json_response({
                "status": "error",
                "message": "Invalid dispatched_quantities",
            }, 400)

        quantities = {}

        for line in dispatched_quantities:

            if not isinstance(line, dict):
                return self.json_response({
                    "status": "error",
                    "message": "Invalid dispatch line",
                }, 400)

            product_id = line.get("product_id")
            quantity = line.get("quantity")

            if (
                type(product_id) is not int
                or product_id <= 0
                or type(quantity) not in (int, float)
                or not math.isfinite(quantity)
                or not (0 < quantity <= 1000000000)
                or product_id in quantities
            ):
                return self.json_response({
                    "status": "error",
                    "message": "Invalid or duplicate product quantity",
                }, 400)

            quantities[product_id] = quantity

        env = request.env

        def error_response(message, status):
            env.cr.rollback()
            return self.json_response({
                "status": "error",
                "message": message,
            }, status)

        try:
            Picking = env["stock.picking"]
            Move = env["stock.move"]

            if not (
                Picking.has_access("read")
                and Picking.has_access("write")
                and Move.has_access("read")
                and Move.has_access("write")
            ):
                return error_response(
                    "Insufficient permissions", 403
                )

            # Prevent simultaneous validation of this dispatch.
            try:
                with env.cr.savepoint():
                    env.cr.execute(
                        """
                        SELECT id
                        FROM stock_picking
                        WHERE id = %s
                        FOR UPDATE NOWAIT
                        """,
                        (dispatch_id,),
                    )
                    locked = env.cr.fetchone()

            except errors.LockNotAvailable:
                return error_response(
                    "Dispatch is being processed", 409
                )

            if not locked:
                return error_response(
                    "Dispatch not found", 404
                )

            env.invalidate_all()

            dispatch = Picking.search([
                ("id", "=", dispatch_id),
                ("company_id", "in", env.companies.ids),
                ("picking_type_id.code", "=", "outgoing"),
            ], limit=1)

            if not dispatch:
                return error_response(
                    "Outgoing dispatch not found", 404
                )

            if dispatch.origin != external_reference:
                return error_response(
                    "External reference mismatch", 409
                )

            if dispatch.state == "done":
                return error_response(
                    "Dispatch already validated", 409
                )

            if dispatch.state == "cancel":
                return error_response(
                    "Dispatch is cancelled", 409
                )

            if dispatch.state != "draft":
                return error_response(
                    "Only draft dispatches are supported", 409
                )

            # This API must not validate unrelated Odoo deliveries.
            if not external_reference.startswith("AGRIWARE-DISP-"):
                return error_response(
                    "Dispatch is not managed by AgriWare", 403
                )

            moves = dispatch.move_ids.filtered(
                lambda move: move.state != "cancel"
            )

            if not moves:
                return error_response(
                    "Dispatch contains no active movements", 409
                )

            if len(moves) != len(quantities):
                return error_response(
                    "Dispatched products do not match order", 409
                )

            for move in moves:

                product = move.product_id

                if product.id not in quantities:
                    return error_response(
                        "Product mismatch", 409
                    )

                if product.tracking != "none":
                    return error_response(
                        "Lot or serial tracking is not supported yet",
                        409,
                    )

                expected = move.product_uom_qty
                received = quantities[product.id]

                if float_compare(
                    expected,
                    received,
                    precision_rounding=move.product_uom.rounding,
                ) != 0:
                    return error_response(
                        "Partial dispatches are not supported", 409
                    )

            # Confirm and reserve through Odoo's standard workflow.
            dispatch.action_confirm()
            dispatch.action_assign()

            env.invalidate_all()

            moves = dispatch.move_ids.filtered(
                lambda move: move.state != "cancel"
            )

            # A dispatch must be fully reserved before validation.
            for move in moves:

                reserved = sum(
                    move.move_line_ids.mapped("quantity")
                )

                if float_compare(
                    reserved,
                    move.product_uom_qty,
                    precision_rounding=move.product_uom.rounding,
                ) < 0:
                    return error_response(
                        "Insufficient reserved stock", 409
                    )

            for move in moves:
                move.picked = True

            result = dispatch.button_validate()

            env.invalidate_all()

            if dispatch.state != "done":
                return error_response(
                    "Odoo did not complete the dispatch", 409
                )

            return self.json_response({
                "status": "success",
                "dispatch_id": dispatch.id,
                "dispatch_reference": dispatch.name,
                "external_reference": dispatch.origin,
                "state": dispatch.state,
            }, 200)

        except AccessError:
            return error_response("Access denied", 403)

        except (UserError, ValidationError) as exc:
            _logger.warning(
                "AgriWare dispatch validation rejected: %s",
                exc,
            )
            return error_response(
                "Odoo rejected dispatch validation", 409
            )

        except Exception:
            env.cr.rollback()
            _logger.exception(
                "AgriWare dispatch validation failed"
            )
            return self.json_response({
                "status": "error",
                "message": "Unable to validate dispatch",
            }, 500)
