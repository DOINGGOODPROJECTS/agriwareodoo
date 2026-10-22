# API Roadmap

**Status: PROPOSED. NOT YET IMPLEMENTED.** This document specifies request/response schemas for
endpoints that do not exist yet, and a phased plan for building them. See
[ARCHITECTURE.md](ARCHITECTURE.md) for why, and
[WMS_FIRST_INTEGRATION_PLAN.md](WMS_FIRST_INTEGRATION_PLAN.md) for the detailed functional design
each schema below implements.

All proposed endpoints keep the existing prefix, `/agriware/api/v1/` — **no new version segment is
introduced**; see [API compatibility & versioning](#api-compatibility--versioning) for why.

## Proposed endpoint schemas

### `POST /agriware/api/v1/products`

Request:
```json
{
  "external_system": "primary_wms",
  "external_id": "WMS-PRODUCT-001",
  "name": "Cassava 50kg Bag",
  "default_code": "CASS-50",
  "barcode": "6161100000099",
  "uom_code": "kg"
}
```
Response `201`:
```json
{
  "status": "success",
  "product_id": 101,
  "external_id": "WMS-PRODUCT-001",
  "name": "Cassava 50kg Bag"
}
```
Response `409` (external_id already mapped):
```json
{"status": "error", "message": "external_id already mapped", "product_id": 101}
```

### `PATCH /agriware/api/v1/products/{external_id}`

Request (partial — only fields to change):
```json
{"name": "Cassava 50kg Bag (updated)", "barcode": "6161100000100"}
```
Response `200`:
```json
{"status": "success", "product_id": 101, "external_id": "WMS-PRODUCT-001"}
```
Response `404` (no such external_id mapped for this company/system):
```json
{"status": "error", "message": "No product mapped for this external_id"}
```

### `POST /agriware/api/v1/warehouses`

Request:
```json
{"external_system": "primary_wms", "external_id": "WMS-WH-ANYAMA", "name": "Anyama Depot", "code": "ANY"}
```
Response `201`:
```json
{"status": "success", "warehouse_id": 3, "external_id": "WMS-WH-ANYAMA", "name": "Anyama Depot"}
```

### `PATCH /agriware/api/v1/warehouses/{external_id}`

Same shape as the product `PATCH` — partial body, allow-listed fields only (`name`, `code`).

### `POST /agriware/api/v1/suppliers`

Request:
```json
{
  "external_system": "primary_wms",
  "external_id": "WMS-SUPPLIER-014",
  "name": "Cooperative Agricole d'Anyama",
  "email": "contact@example.ci",
  "phone": "+225 07 00 00 0000",
  "country_code": "CI"
}
```
Response `201`:
```json
{"status": "success", "supplier_id": 37, "external_id": "WMS-SUPPLIER-014", "name": "Cooperative Agricole d'Anyama"}
```

### `PATCH /agriware/api/v1/suppliers/{external_id}`

Same partial-update shape as products/warehouses, allow-listed fields only.

### `POST /agriware/api/v1/lots`

Request:
```json
{
  "external_system": "primary_wms",
  "external_id": "WMS-LOT-2026-0042",
  "product_external_id": "WMS-PRODUCT-001",
  "name": "LOT-0042"
}
```
Response `201`:
```json
{"status": "success", "lot_id": 15, "external_id": "WMS-LOT-2026-0042", "product_id": 101}
```
Response `404` (product external_id not found):
```json
{"status": "error", "message": "No product mapped for product_external_id"}
```

### `GET /agriware/api/v1/lots`

Query parameters: `product_external_id` (optional filter). Response `200`:
```json
{
  "status": "success",
  "count": 1,
  "lots": [{"lot_id": 15, "external_id": "WMS-LOT-2026-0042", "product_id": 101, "product_external_id": "WMS-PRODUCT-001"}]
}
```

### `POST /agriware/api/v1/inventory-adjustments`

Request:
```json
{
  "external_reference": "AGRIWARE-ADJ-2026-10-01",
  "warehouse_external_id": "WMS-WH-ANYAMA",
  "lines": [
    {"product_external_id": "WMS-PRODUCT-001", "counted_quantity": 5000}
  ]
}
```
Response `201` (adjustment recorded, **not yet applied** — see
[WMS_FIRST_INTEGRATION_PLAN.md](WMS_FIRST_INTEGRATION_PLAN.md#initial-inventory-import)):
```json
{
  "status": "success",
  "import_log_id": 9,
  "external_reference": "AGRIWARE-ADJ-2026-10-01",
  "state": "pending_approval",
  "lines_recorded": 1
}
```
Response `409` (duplicate `external_reference`):
```json
{"status": "error", "message": "external_reference already submitted", "import_log_id": 9}
```

### Additive fields on existing endpoints (no new routes)

`POST /receipts`, `POST /dispatches`, and their `/validate` counterparts gain **optional**
alternative identifier fields, used only if the corresponding numeric field is absent:

| Existing numeric field | New optional alternative |
|---|---|
| `warehouse_id` | `warehouse_external_id` |
| `supplier_id` | `supplier_external_id` |
| `customer_id` | `customer_external_id` |
| `products[].product_id` | `products[].product_external_id` |
| *(new)* | `products[].lot_external_id` (optional, only for lot-tracked products once Phase F ships) |

Sending both the numeric and external-ID form for the same field is a caller error (`400`), not a
silent precedence rule.

## Development roadmap

### Phase A — External ID mapping and data ownership

**Status: IMPLEMENTED** (branch `feature/wms-external-id-mapping`, not yet merged). See
[EXTERNAL_ID_MAPPING.md](EXTERNAL_ID_MAPPING.md) for full documentation of what shipped.

- **Technical tasks:** ~~create the generic mapping model~~ done, plus an explicit
  `agriware.external.system` model (not originally scoped this precisely, but needed so mappings
  can be scoped independently of any one API key's lifecycle — see
  [EXTERNAL_ID_MAPPING.md](EXTERNAL_ID_MAPPING.md#external-system-identity)); the
  resolve/create/update/remove service as model methods on
  `agriware.external.id.mapping`, not a separate mixin.
- **Files changed:** `models/external_system.py`, `models/external_id_mapping.py` (new);
  `models/__init__.py`; `security/agriware_security.xml`, `security/ir.model.access.csv`;
  `views/external_system_views.xml` (new); `tests/test_external_systems.py`,
  `tests/test_external_id_mapping.py` (new); `tests/__init__.py`; `__manifest__.py` (data entry +
  version bump).
- **Database models:** `agriware.external.system`, `agriware.external.id.mapping` (both new).
- **API endpoints:** none — confirmed, this phase shipped no REST routes, exactly as scoped.
- **Security requirements:** implemented as designed — company-scoped `ir.rule` on both new models;
  `ir.model.access.csv` grants the Administrator group full access to `external.system` and
  **read-only** access to `external.id.mapping`; the API User group has no direct grant on either
  model (service-mediated only, via `sudo()` after an explicit group+company check).
- **Automated tests:** 23 new tests (7 for `external.system`, 16 for the mapping service and
  model), covering every scenario originally listed for this phase plus the full approval-task
  checklist (duplicate codes, duplicate external IDs, duplicate Odoo-record mappings, different
  systems/companies sharing an ID, invalid targets, unsupported models, cross-company access,
  concurrent creation via the DB constraint, and the admin/API-User access boundary). All 84 tests
  in the module (61 pre-existing + 23 new) pass against a fresh throwaway database.
- **Dependencies:** none beyond what's already installed — confirmed.
- **Risks, as anticipated:** none materialized against the schema itself. One real implementation
  bug was caught by testing against the actual installed Odoo 19 build, not assumed: this Odoo
  version's `models.BaseModel` defines its own internal `_check_access(operation)` hook used by
  every `search()`/`write()` call; naming the mapping model's own authorization helper the same
  thing silently overrode Odoo's own access-control dispatch for that model. Renamed to
  `_check_mapping_access` once the test suite caught it. This is exactly the kind of thing "verify
  against the installed Odoo version" was meant to surface.
- **Acceptance criteria:** met — verified directly: a mapping can be created, retrieved, and a
  duplicate is handled without creating a second row; company A cannot see or create against
  company B's mappings (tested, not assumed); the database constraints — not just the
  application-level pre-check — are what actually stop a forced duplicate insert.

### Phase B — Product creation and updates

**Status: IMPLEMENTED** (branch `feature/wms-product-sync`, based on Phase A, not yet merged). See
[PRODUCT_SYNCHRONIZATION.md](PRODUCT_SYNCHRONIZATION.md) for the full as-built reference.

- **Technical tasks:** done, plus one addition not originally scoped here: binding an
  `agriware.api.key` to an `agriware.external.system` (Phase 3 of the implementation task), since
  "resolve external system from the authenticated key" required it and nothing had built that
  binding yet. UOM resolution shipped as a small hardcoded set now (not the Phase D table) — the
  sequencing question is resolved: Phase B shipped first, Phase D's richer table remains future
  work, exactly as flagged as an open decision.
- **Files changed:** `controllers/products.py` (new); `controllers/__init__.py`,
  `controllers/api_security.py` (added `resolve_authorized_external_system()`); `models/api_key.py`
  (added `external_system_id`, its company constraint, and
  `resolve_authorized_external_system()`); `wizards/api_key_generate_wizard.py` and
  `views/api_key_views.xml` (expose the binding at generation time); `security/ir.model.access.csv`
  (two new grants — see Risks); `tests/test_product_sync.py` (new); `tests/__init__.py`;
  `__manifest__.py` (version bump).
- **Database models:** none new — reuses `product.product` and Phase A's mapping model, as planned.
- **API endpoints:** `POST /products`, `PATCH /products/{external_id}`, exactly as planned.
- **Security requirements:** implemented as **explicit, auditable `ir.model.access.csv` grants**
  (not a `sudo()` bypass) — see Risks for why both `product.product` and `product.template` needed
  a grant, not just the former.
- **Automated tests:** 22 new tests — create, duplicate rejection (including a forced-race
  variant), update, 404 on unknown external_id, allow-list enforcement, **explicit rejection**
  (not silent ignoring — a deliberate refinement, see
  [PRODUCT_SYNCHRONIZATION.md](PRODUCT_SYNCHRONIZATION.md#supported-product-fields)), plus the full
  API-key-binding security matrix (valid/missing/invalid/revoked/expired/unbound keys, inactive
  external system, cross-company, cross-system). All 106 tests in the module pass (84 pre-existing
  + 22 new).
- **Dependencies:** Phase A — confirmed sufficient, nothing else was needed.
- **Risks, as anticipated vs. actual:** anticipated "low, closely mirrors existing patterns" — not
  quite true in practice. Two real issues surfaced only by testing against the installed Odoo 19,
  not by code review: (1) `stock.group_stock_user` (implied by AgriWare API User) has **no**
  `product.product` create/write access at all, unlike `stock.picking`/`stock.move` — had to be
  granted explicitly; (2) granting `product.product` access alone wasn't sufficient either —
  creating a `product.product` without an existing template also needs `create` access to the
  underlying `product.template` (delegation inheritance), only discovered when every product-
  creation test failed with an ACL error naming `product.template`, not `product.product`.
- **Acceptance criteria:** met, and demonstrated live — see
  [PRODUCT_SYNCHRONIZATION.md's Verification performed](PRODUCT_SYNCHRONIZATION.md#verification-performed)
  for the real HTTP request/response sequence (create Cassava → update it → repeat the create →
  `409`, no duplicate) with direct PostgreSQL row verification, not just API response trust.

### Phase C — Warehouse creation and mapping

**Status: IMPLEMENTED** (branch `feature/wms-warehouse-sync`, based on Phase B, not yet merged).
See [WAREHOUSE_SYNCHRONIZATION.md](WAREHOUSE_SYNCHRONIZATION.md) for the full as-built reference.

- **Technical tasks:** done, plus one addition not originally scoped: existing-warehouse adoption
  (reviewed per the task's own Phase 9, designed in detail, deliberately **not** implemented — the
  task explicitly permits documenting rather than shipping an unsafe shortcut).
- **Files changed:** `controllers/warehouses.py` (new); `controllers/__init__.py`;
  `tests/test_warehouse_sync.py` (new); `tests/__init__.py`; `__manifest__.py` (version bump). No
  `security/ir.model.access.csv` changes — see Security requirements below for why this phase
  deliberately diverged from Phase B's pattern there.
- **Database models:** none new — reuses `stock.warehouse` and Phase A's mapping model, as planned.
- **API endpoints:** `POST /warehouses`, `PATCH /warehouses/{external_id}`, exactly as planned.
  `code` ended up excluded from `PATCH` (see Risks).
- **Security requirements:** **not** `has_access()` as originally sketched. `stock.warehouse`
  creation cascades into `stock.location`, `stock.picking.type`, `stock.route`, `stock.rule`, and
  `ir.sequence` — confirmed by reading `stock.warehouse.create()` directly — and none of those
  models has any native create access for the AgriWare API User group (verified empirically,
  the same way the Phase B product.template gap was found). Granting broad access across all of
  them to match Phase B's pattern would hand the API User group standing write access to routing/
  picking-type configuration, which Phase 7 explicitly forbids. Instead: the controller performs
  the same explicit auth + resolved-external-system check as every other write endpoint, then calls
  `stock.warehouse.sudo().create(...)` — a single, narrow, already-gated operation, not a general
  capability. See [WAREHOUSE_SYNCHRONIZATION.md's Security section](WAREHOUSE_SYNCHRONIZATION.md#security)
  for the full reasoning.
- **Automated tests:** 26 new tests — creation, native location/picking-type generation, update,
  duplicate name/code/external_id handling (three distinct conflict sources, not one), the
  `code`-immutability rejection, the full API-key-binding security matrix, cross-company isolation,
  and confirmation that Phase A/B's existing endpoints and tests are entirely unaffected. All 132
  tests in the module pass (106 pre-existing + 26 new) — notably, **zero failures on the first full
  run**, unlike Phase B, because the product.template-style ACL lesson was checked for up front
  before writing the controller rather than discovered by a failing test.
- **Dependencies:** Phase A — confirmed sufficient.
- **Risks, as anticipated vs. actual:** anticipated "needs explicit testing that auto-created
  records don't produce surprises" — confirmed true and tested directly (real `stock_location` and
  picking-type rows verified via SQL, not just trusted from the API response). One risk not
  anticipated in the original sketch: `code` changes after creation turned out to be a genuine
  data-integrity hazard (a warehouse's auto-generated locations are named from its code at creation
  time, with no re-propagation on a later change) — resolved by excluding `code` from `PATCH`
  entirely, per the task's own "reject the change rather than risk data corruption" instruction.
- **Acceptance criteria:** met, and demonstrated live — see
  [WAREHOUSE_SYNCHRONIZATION.md's Verification performed](WAREHOUSE_SYNCHRONIZATION.md#verification-performed)
  for the real HTTP sequence (create Anyama Warehouse → update it → repeat the create → `409`) with
  direct PostgreSQL verification that the native location tree and picking types genuinely exist,
  not just that the warehouse row does.

### Phase D — Supplier integration and UOM mapping

- **Technical tasks:** `POST`/`PATCH /suppliers` (and the `customer_rank` variant — see
  [WMS_FIRST_INTEGRATION_PLAN.md](WMS_FIRST_INTEGRATION_PLAN.md#4-supplier-creation-and-updates));
  the UOM mapping model and its admin-seeded lookup data.
  <br>Also: Country lookup resolution needed for the `country_code` field (ISO 3166-1 alpha-2 codes
  map to Odoo's own `res.country` table, which already contains this).
- **Files likely to change:** new `controllers/suppliers.py`; new `models/uom_mapping.py`; new
  `data/uom_mapping_data.xml` (seed data for common units: kg, ton, liter, unit, bag).
- **Database models:** `agriware.uom.mapping` (new) — **approved as a database-backed model**, not
  a static in-code dictionary (an earlier version of this document left that as an open
  implementer's choice; it's since been resolved — see
  [ARCHITECTURE.md's Approved decisions](ARCHITECTURE.md#approved-decisions), item 7). A real model
  lets administrators extend the mapping without a code change, and gives it the same
  company-scoping and access-control treatment as every other new model in this plan.
- **API endpoints:** `POST /suppliers`, `PATCH /suppliers/{external_id}`.
- **Security requirements:** `has_access()` on `res.partner`.
- **Automated tests:** same create/update/conflict shape; a specific test for an unmapped UOM
  code returning a clear `400`, not a silent fallback.
- **Dependencies:** Phase A.
- **Risks:** `res.partner` is a widely-shared model across all of Odoo (contacts, CRM, etc.) —
  needs careful review that nothing written here leaks into unrelated Odoo features in
  unexpected ways.
- **Acceptance criteria:** a supplier created via the API appears correctly as a vendor option on a
  purchase order created manually in Odoo's own UI (confirms it's a well-formed `res.partner`, not
  a shadow record).

### Phase E — Initial inventory import and reconciliation

- **Technical tasks:** `POST /inventory-adjustments`; the `agriware.inventory.import.log` model;
  the `inventory_mode` quant-creation logic (not `action_apply_inventory()` — see
  [WMS_FIRST_INTEGRATION_PLAN.md](WMS_FIRST_INTEGRATION_PLAN.md#initial-inventory-import)).
- **Files likely to change:** new `controllers/inventory_adjustments.py`; new
  `models/inventory_import_log.py`; a view for the Odoo-side approval screen (reusing Odoo's native
  Inventory Adjustments UI — likely no new view needed at all, just confirming the native one shows
  these correctly).
- **Database models:** `agriware.inventory.import.log` (new).
- **API endpoints:** `POST /inventory-adjustments`.
- **Security requirements:** `has_access('create')` on `stock.quant`; company-scoped warehouse
  resolution identical to receipts/dispatches.
- **Automated tests:** batch validated-before-write (an invalid line fails the whole batch);
  duplicate `external_reference` rejection; confirmation that `action_apply_inventory()` is never
  called by the controller itself; confirmation a human applying it manually afterward produces the
  expected `stock.move`.
- **Dependencies:** Phases A, B (products must resolve via external ID), C (warehouses).
- **Risks:** **the highest-risk phase in this roadmap.** A bug here risks corrupting real inventory
  counts for a production business. Recommend this phase gets the most test coverage and the most
  cautious rollout (e.g., require the approval step for every batch, with no "auto-apply" flag at
  all in the first version, even as an option).
- **Acceptance criteria:** a 50-line test batch is submitted, appears as pending differences in
  Odoo's native Inventory Adjustments screen, and after a human clicks Apply there, stock
  quantities match the submitted counts exactly — with zero direct `stock.quant.quantity` writes
  anywhere in the code path (verified by code review, not just testing).

### Phase F — Lot and batch integration

- **Technical tasks:** `POST`/`GET /lots`; the additive `lot_external_id` field on receipt/dispatch
  product lines; **removal of the current blanket lot/serial rejection, replaced with real
  handling** — this is the one place existing behavior intentionally changes, and only for
  lot-tracked products specifically (non-tracked products are entirely unaffected).
- **Files likely to change:** new `controllers/lots.py`; `controllers/receipts.py`,
  `controllers/dispatches.py`, `controllers/receipt_validation.py`,
  `controllers/dispatch_validation.py` (the four files containing today's rejection logic).
- **Database models:** none new (reuses `stock.lot` + Phase A's mapping model).
- **API endpoints:** `POST /lots`, `GET /lots`; additive fields on the four existing transaction
  endpoints.
- **Security requirements:** `has_access()` on `stock.lot`.
- **Automated tests:** everything in the *existing* lot-rejection test suite must still pass
  unchanged for non-lot-tracked products; new tests for the lot-tracked path end-to-end; a test
  confirming a lot cannot be over-allocated beyond its recorded quantity.
- **Dependencies:** Phases A, B (lots belong to products).
- **Risks:** this phase touches the most existing, already-shipped code (the four transaction
  controllers) — regression risk is real. The existing rejection tests must be run and pass before
  and after every change in this phase, not just at the end.
- **Acceptance criteria:** a lot-tracked product can now be received and dispatched by external lot
  ID end-to-end; a non-lot-tracked product's behavior is byte-for-byte unchanged, confirmed by the
  existing test suite passing with zero modifications to those specific test assertions.

### Phase G — Transaction integration enhancements

- **Technical tasks:** the additive `*_external_id` fields on `POST /receipts`/`/dispatches`
  (independent of lots — this is the general "resolve by external ID instead of Odoo ID" feature
  for warehouse/supplier/customer/product references).
- **Files likely to change:** `controllers/receipts.py`, `controllers/dispatches.py`.
- **Database models:** none new.
- **API endpoints:** no new routes — additive optional fields only on existing ones.
- **Security requirements:** no change beyond what Phases A-D already established (resolution
  reuses the same mapping lookups).
- **Automated tests:** a test matrix of "numeric ID only" (today's behavior, must be unchanged), 
  "external ID only" (new), and "both provided" (`400`, explicit conflict).
- **Dependencies:** Phases A-D.
- **Risks:** low, if Phases A-D are solid — this phase is mostly wiring.
- **Acceptance criteria:** an existing WMS integration using only numeric IDs continues to work with
  zero code changes on its side; a new WMS-first integration can create a receipt referencing only
  external IDs it created in earlier phases, never touching an Odoo-internal number.

### Phase H — ERP workflow integration testing

- **Technical tasks:** no new code — this phase is validation that everything built in A-G
  interacts correctly with Odoo's own ERP functions (the parts explicitly **not** touched by any
  phase): a product created via the API can be invoiced normally; a supplier created via the API
  can receive a normal Odoo-created purchase order; accounting entries post correctly from
  API-created stock moves exactly as they do from manually-created ones.
- **Files likely to change:** none (test files only).
- **Database models:** none new.
- **API endpoints:** none new.
- **Security requirements:** none new — this phase verifies the ownership-matrix boundary actually
  holds (nothing WMS-created ever touches accounting config).
- **Automated tests:** end-to-end scenarios spanning a product/supplier created via the API through
  to a real Odoo invoice, run against a throwaway database per the project's existing test
  conventions.
- **Dependencies:** Phases A-G complete.
- **Risks:** this is where a subtle ownership-matrix violation would surface (e.g., a field
  accidentally left writable that shouldn't be) — treat any finding here as a blocker, not a
  follow-up item.
- **Acceptance criteria:** a full customer scenario — WMS creates products/warehouse/supplier,
  imports initial stock, receives and dispatches goods including a lot-tracked one — produces
  correct, auditable Odoo accounting entries with no manual data entry required on the Odoo side
  beyond the initial inventory-adjustment approval clicks.

## API compatibility & versioning

- **Every existing route's request/response shape is unchanged** across all eight phases. Confirmed
  by design, not just intention: Phases A-E and most of F/G add only new routes or strictly
  *optional, additive* fields on existing ones; the only phase that touches existing controller
  files in a way that changes behavior (Phase F, the lot-rejection removal) only changes behavior
  for the specific product-tracking case that previously always failed — a client that never sends
  a lot-tracked product sees no change at all.
- **No existing route is renamed or removed.** The `/agriware/api/v1/` prefix is unchanged
  throughout; **no `v2` is introduced** by this roadmap, because nothing in it breaks an existing
  request/response contract.
- **Recommended module version bump:** Odoo module versions follow
  `odoo_major.odoo_minor.module_major.module_minor.module_patch` (the current manifest version is
  `19.0.1.0.0`). Since every phase is additive, each phase should bump the **module_minor** segment
  (e.g. Phase A → `19.0.1.1.0`, Phase B → `19.0.1.2.0`, and so on), reserving a **module_major** bump
  (`19.0.2.0.0`) for if/when a genuinely breaking change is ever needed — which this roadmap does
  not plan to introduce.
- **Existing API clients require zero changes** to keep working through every phase in this
  roadmap — this is treated as a hard constraint, not a best-effort goal, and Phase G's test matrix
  exists specifically to keep proving it with each change.
