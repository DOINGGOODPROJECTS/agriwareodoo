import hashlib
import json
import logging

import psycopg2

from odoo import http
from odoo.http import request, Response
from odoo.exceptions import AccessError, ValidationError
from .api_security import require_agriware_api_user, resolve_authorized_external_system
from .products import SUPPORTED_UNITS as HARDCODED_UNITS

_logger = logging.getLogger(__name__)

TOP_LEVEL_ALLOWED_FIELDS = {"external_reference", "warehouse_external_id", "lines"}
LINE_ALLOWED_FIELDS = {"product_external_id", "quantity", "unit"}

# Mirrors receipts.py's existing cap on a single request's line count.
MAX_LINES = 500


class AgriwareInventoryImportAPI(http.Controller):

    @staticmethod
    def json_response(data, status=200):
        return Response(
            json.dumps(data),
            status=status,
            content_type="application/json",
        )

    def _authenticate(self):
        """Identical in spirit to every other Phase B/C/D endpoint's
        _authenticate() -- see controllers/products.py for the full
        reasoning behind resolve_authorized_external_system().
        """
        authorization = request.httprequest.headers.get("Authorization", "")
        if not authorization.startswith("Bearer "):
            return None, self.json_response(
                {"status": "error", "message": "Bearer token required"}, 401,
            )

        if not require_agriware_api_user():
            return None, self.json_response({
                "status": "error",
                "message": "Access denied: AgriWare API User role required",
            }, 403)

        try:
            external_system = resolve_authorized_external_system()
        except ValidationError as exc:
            return None, self.json_response(
                {"status": "error", "message": str(exc)}, 403,
            )

        if not external_system:
            return None, self.json_response({
                "status": "error",
                "message": (
                    "This API key is not authorized for inventory import: "
                    "it is not bound to an active external system."
                ),
            }, 403)

        return external_system, None

    @staticmethod
    def _canonical_hash(external_reference, warehouse_external_id, lines):
        """A stable fingerprint of the request's meaningful content, used
        to tell an identical retry (idempotent) from a conflicting reuse
        of the same external_reference (409) -- see Phase 13.
        """
        canonical = {
            "external_reference": external_reference,
            "warehouse_external_id": warehouse_external_id,
            "lines": sorted(
                [line["product_external_id"], line["quantity"], line["unit"]]
                for line in lines
            ),
        }
        blob = json.dumps(canonical, sort_keys=True).encode()
        return hashlib.sha256(blob).hexdigest()

    @http.route(
        "/agriware/api/v1/inventory-adjustments",
        type="http",
        auth="bearer",
        methods=["POST"],
        csrf=False,
        save_session=False,
    )
    def create_inventory_import(self, **kwargs):

        external_system, error = self._authenticate()
        if error:
            return error

        try:
            payload = json.loads(request.httprequest.get_data(as_text=True))
        except (ValueError, UnicodeDecodeError):
            return self.json_response(
                {"status": "error", "message": "Invalid JSON"}, 400,
            )

        if not isinstance(payload, dict):
            return self.json_response(
                {"status": "error", "message": "Expected JSON object"}, 400,
            )

        unknown_fields = set(payload.keys()) - TOP_LEVEL_ALLOWED_FIELDS
        if unknown_fields:
            return self.json_response({
                "status": "error",
                "message": "Unsupported field(s): %s" % ", ".join(sorted(unknown_fields)),
            }, 400)

        external_reference = payload.get("external_reference")
        warehouse_external_id = payload.get("warehouse_external_id")
        lines = payload.get("lines")

        if (
            not isinstance(external_reference, str)
            or not external_reference.strip()
            or len(external_reference) > 128
        ):
            return self.json_response(
                {"status": "error", "message": "Invalid external_reference"}, 400,
            )
        external_reference = external_reference.strip()

        if not isinstance(warehouse_external_id, str) or not warehouse_external_id.strip():
            return self.json_response(
                {"status": "error", "message": "Invalid warehouse_external_id"}, 400,
            )
        warehouse_external_id = warehouse_external_id.strip()

        if not isinstance(lines, list) or not lines:
            return self.json_response(
                {"status": "error", "message": "lines must be a non-empty list"}, 400,
            )

        if len(lines) > MAX_LINES:
            return self.json_response(
                {"status": "error", "message": "Too many lines"}, 400,
            )

        for line in lines:
            if not isinstance(line, dict):
                return self.json_response(
                    {"status": "error", "message": "Invalid line"}, 400,
                )
            unknown = set(line.keys()) - LINE_ALLOWED_FIELDS
            if unknown:
                return self.json_response({
                    "status": "error",
                    "message": "Unsupported line field(s): %s" % ", ".join(sorted(unknown)),
                }, 400)

            product_external_id = line.get("product_external_id")
            quantity = line.get("quantity")
            unit = line.get("unit")

            if not isinstance(product_external_id, str) or not product_external_id.strip():
                return self.json_response(
                    {"status": "error", "message": "Invalid product_external_id"}, 400,
                )
            if (
                type(quantity) not in (int, float)
                or isinstance(quantity, bool)
                or quantity < 0
            ):
                return self.json_response({
                    "status": "error",
                    "message": "quantity must be a non-negative number",
                }, 400)
            if not isinstance(unit, str) or not unit.strip():
                return self.json_response(
                    {"status": "error", "message": "Invalid unit"}, 400,
                )

        try:
            env = request.env
            company = external_system.company_id
            Mapping = env["agriware.external.id.mapping"]
            Import = env["agriware.inventory.import"]
            UomMapping = env["agriware.uom.mapping"]

            request_hash = self._canonical_hash(
                external_reference, warehouse_external_id, lines,
            )

            # Idempotency pre-check (Phase 13): a retried identical
            # request returns the existing import, not a new one or an
            # error. A retried request with *different* content for the
            # same external_reference is a conflict.
            existing = Import.sudo().search([
                ("company_id", "=", company.id),
                ("external_system_id", "=", external_system.id),
                ("external_reference", "=", external_reference),
            ], limit=1)
            if existing:
                return self._existing_response(existing, request_hash, external_reference)

            warehouse_mapping = Mapping.resolve_mapping(
                company, external_system, "stock.warehouse", warehouse_external_id,
            )
            if not warehouse_mapping:
                return self.json_response(
                    {"status": "error", "message": "Warehouse not found"}, 404,
                )
            warehouse = env["stock.warehouse"].sudo().browse(warehouse_mapping.res_id)
            if not warehouse.exists() or warehouse.company_id != company:
                return self.json_response(
                    {"status": "error", "message": "Warehouse not found"}, 404,
                )

            # Phase 7: only ever the warehouse's own single, unambiguous
            # internal stock location -- never a child location, never
            # an arbitrary distribution across several. See
            # docs/INITIAL_INVENTORY_IMPORT.md's Location mapping section.
            location = warehouse.lot_stock_id
            if not location:
                return self.json_response({
                    "status": "error",
                    "message": "Warehouse has no unambiguous stock location configured",
                }, 422)

            line_values = []
            for line in lines:
                product_external_id = line["product_external_id"].strip()
                quantity = float(line["quantity"])
                unit_code = line["unit"].strip()

                product_mapping = Mapping.resolve_mapping(
                    company, external_system, "product.product", product_external_id,
                )
                if not product_mapping:
                    return self.json_response({
                        "status": "error",
                        "message": "Product not found: %s" % product_external_id,
                    }, 404)
                product = env["product.product"].sudo().browse(product_mapping.res_id)
                if not product.exists() or (
                    product.company_id and product.company_id != company
                ):
                    return self.json_response({
                        "status": "error",
                        "message": "Product not found: %s" % product_external_id,
                    }, 404)

                # Phase 14: lot/serial-tracked products are out of scope
                # until Phase F -- reject the whole import rather than
                # silently aggregating lot-level stock into one number.
                if product.tracking != "none":
                    return self.json_response({
                        "status": "error",
                        "message": (
                            "Product %s requires lot/serial tracking; "
                            "lot-level inventory import is not supported "
                            "until Phase F." % product_external_id
                        ),
                    }, 422)

                resolved_uom = UomMapping.resolve_unit(company, external_system, unit_code)
                if not resolved_uom:
                    if unit_code.lower() not in HARDCODED_UNITS:
                        return self.json_response({
                            "status": "error",
                            "message": "Unsupported unit: %r" % (unit_code,),
                        }, 400)
                    resolved_uom = env.ref(HARDCODED_UNITS[unit_code.lower()])

                product_uom = product.uom_id

                # Odoo's own uom.uom._compute_quantity() does not itself
                # refuse a cross-category conversion (verified directly
                # against this installation's uom/models/uom_uom.py) --
                # it will happily compute a number using mismatched
                # factors. This explicit compatibility check is therefore
                # load-bearing, not defensive boilerplate: without it,
                # "reject incompatible conversions" would not hold.
                #
                # Odoo 19 redesigned UOM entirely -- there is no
                # uom.category model or category_id field any more
                # (verified directly against this installation's
                # uom/models/uom_uom.py). UOMs instead form a
                # self-referencing tree via relative_uom_id/parent_path;
                # two units are convertible iff they share the same root
                # ancestor (e.g. kg and g both root at "g"; L roots at
                # "ml" -- a different tree entirely).
                if self._uom_root(resolved_uom) != self._uom_root(product_uom):
                    return self.json_response({
                        "status": "error",
                        "message": (
                            "Unit %r is not compatible with product %s's "
                            "unit (%s)" % (
                                unit_code, product_external_id, product_uom.name,
                            )
                        ),
                    }, 422)

                normalized_quantity = resolved_uom._compute_quantity(
                    quantity, product_uom, round=True,
                )

                current_qty = sum(env["stock.quant"].sudo().search([
                    ("product_id", "=", product.id),
                    ("location_id", "=", location.id),
                ]).mapped("quantity"))

                line_values.append((0, 0, {
                    "product_id": product.id,
                    "location_id": location.id,
                    "uom_id": product_uom.id,
                    "external_unit_code": unit_code,
                    "original_reported_quantity": quantity,
                    "reported_quantity": normalized_quantity,
                    "current_odoo_quantity": current_qty,
                    "proposed_difference": normalized_quantity - current_qty,
                }))

            try:
                with env.cr.savepoint():
                    inventory_import = Import.sudo().create({
                        "company_id": company.id,
                        "external_system_id": external_system.id,
                        "external_reference": external_reference,
                        "warehouse_id": warehouse.id,
                        "location_id": location.id,
                        "request_hash": request_hash,
                        "submitted_by": env.user.id,
                        "line_ids": line_values,
                    })
            except psycopg2.IntegrityError:
                # Lost a race against a concurrent request for the same
                # external_reference. Our own insert was rolled back by
                # the savepoint above; the other request's row is now
                # the source of truth.
                request.env.cr.rollback()
                existing = Import.sudo().search([
                    ("company_id", "=", company.id),
                    ("external_system_id", "=", external_system.id),
                    ("external_reference", "=", external_reference),
                ], limit=1)
                if not existing:
                    raise
                return self._existing_response(existing, request_hash, external_reference)

            return self.json_response({
                "status": "success",
                "import_id": inventory_import.id,
                "external_reference": external_reference,
                "state": inventory_import.state,
                "lines": [
                    {
                        "product_external_id": lines[i]["product_external_id"],
                        "reported_quantity": line.reported_quantity,
                        "current_odoo_quantity": line.current_odoo_quantity,
                        "proposed_difference": line.proposed_difference,
                    }
                    for i, line in enumerate(inventory_import.line_ids)
                ],
            }, 201)

        except AccessError:
            request.env.cr.rollback()
            return self.json_response(
                {"status": "error", "message": "Access denied"}, 403,
            )

        except Exception:
            request.env.cr.rollback()
            _logger.exception("AgriWare inventory import failed")
            return self.json_response(
                {"status": "error", "message": "Unable to create inventory import"}, 500,
            )

    @staticmethod
    def _uom_root(uom):
        """The id of ``uom``'s root ancestor in Odoo 19's self-referencing
        UOM tree (relative_uom_id/parent_path) -- the modern replacement
        for the old category_id field. Two UOMs are convertible iff this
        matches for both.
        """
        return int(uom.parent_path.split("/")[0])

    def _existing_response(self, existing, request_hash, external_reference):
        if existing.request_hash == request_hash:
            return self.json_response({
                "status": "success",
                "import_id": existing.id,
                "external_reference": external_reference,
                "state": existing.state,
                "note": "Idempotent repeat of an already-submitted import.",
            }, 200)
        return self.json_response({
            "status": "error",
            "message": "external_reference already used with different content",
            "import_id": existing.id,
        }, 409)
