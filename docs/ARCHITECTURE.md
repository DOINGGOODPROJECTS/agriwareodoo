# AgriWare Connector — Architecture

**This document covers two things, kept clearly separate:**

1. **Current architecture** — verified directly against the code in this repository (controllers,
   models, security files, tests) as of this writing. Everything in that section exists and works.
2. **Target (WMS-first) architecture** — the proposed direction agreed for AgriWare Connector's next
   development phase. **Every statement in that section is a design proposal. Nothing in it is
   implemented.** See [WMS_FIRST_INTEGRATION_PLAN.md](WMS_FIRST_INTEGRATION_PLAN.md) for the detailed
   functional design and [API_ROADMAP.md](API_ROADMAP.md) for the phased build plan.

## Approved decisions

The WMS-first direction in this document has been reviewed and approved. The following specific
decisions are recorded as approved, not as open proposals:

1. The WMS is the primary source of warehouse operational data.
2. Odoo remains responsible for ERP-specific accounting, invoicing, sales, and purchasing.
3. Existing API endpoints must remain compatible — no existing route's request/response shape
   changes, ever, as part of this work.
4. Future `PATCH` endpoints will identify records using external IDs, not Odoo database IDs (the
   design and rejected alternative are in
   [WMS_FIRST_INTEGRATION_PLAN.md](WMS_FIRST_INTEGRATION_PLAN.md#why-external-ids-not-odoo-ids-in-the-url-path)).
5. External IDs are scoped by company, external system, and record model.
6. Product synchronization (Phase B) may precede full UOM mapping (Phase D), but any unsupported
   unit must be rejected explicitly (`400`), never silently guessed or dropped.
7. Full UOM mapping will use a **database-backed model** in Phase D — this supersedes the earlier,
   now-rejected option of a static in-code dictionary considered in
   [API_ROADMAP.md](API_ROADMAP.md#phase-d--supplier-integration-and-uom-mapping).
8. Configurable per-company field ownership is deferred — the fixed allow-list design in this
   document's [Data Ownership Matrix](#data-ownership-matrix) is what ships first.
9. All WMS-facing write operations must use explicit field allow-lists — never a block-list.
10. Initial inventory adjustments must require human review and approval inside Odoo — the API
    never calls `action_apply_inventory()` itself (see
    [WMS_FIRST_INTEGRATION_PLAN.md](WMS_FIRST_INTEGRATION_PLAN.md#initial-inventory-import)).

**What remains open** (explicitly not resolved by this approval): whether an existing API key
should bind to a specific external system — see
[EXTERNAL_ID_MAPPING.md](EXTERNAL_ID_MAPPING.md#api-key-binding-reviewed-not-implemented) for the
review and why it's deferred rather than decided here.

## Part 1 — Current architecture (implemented, verified)

### What exists today

Verified by reading `agriware_connector/controllers/`, `agriware_connector/models/`,
`agriware_connector/security/`, and `agriware_connector/tests/` directly:

- **Models:** `agriware.api.key` (self-service API key management), `agriware.connection`
  (an unused, hidden model from an earlier design — see
  [Known limitations](API.md#known-limitations)); `agriware.external.system` and
  `agriware.external.id.mapping` (Phase A's external-ID mapping infrastructure — see
  [EXTERNAL_ID_MAPPING.md](EXTERNAL_ID_MAPPING.md)); and, as of Phase D,
  `agriware.uom.mapping` (database-backed unit mapping — see [UOM_MAPPING.md](UOM_MAPPING.md)); and,
  as of Phase E, `agriware.inventory.import`/`.line` (staged WMS stock observations — see
  [INITIAL_INVENTORY_IMPORT.md](INITIAL_INVENTORY_IMPORT.md)). Phase F adds no new model of its
  own — it reuses Odoo's native `stock.lot` directly, mapped through the same Phase A service (see
  [LOT_BATCH_SYNCHRONIZATION.md](LOT_BATCH_SYNCHRONIZATION.md)). As of Phase G,
  `agriware.wms.transaction` (receipt/dispatch identity for the new WMS-first creation path — see
  [WMS_TRANSACTION_SYNCHRONIZATION.md](WMS_TRANSACTION_SYNCHRONIZATION.md)).
  Product (Phase B), warehouse (Phase C), supplier (Phase D), initial inventory import (Phase E),
  lot/serial synchronization (Phase F), and WMS-first receipt/dispatch synchronization (Phase G)
  are all implemented — see each phase's own reference document.
- **Security fix (post-Phase B):** a real authorization-isolation vulnerability was found and
  fixed — an API key generated with no external-system binding could inherit authorization from an
  unrelated bound key sharing its company, reproduced via a real HTTP request before being fixed.
  See [PRODUCT_SYNCHRONIZATION.md's API key binding section](PRODUCT_SYNCHRONIZATION.md#api-key-binding)
  for the full writeup. Every write endpoint built since (warehouses, suppliers) inherits the fix
  automatically, since all of them resolve authorization the same way.
- **Controllers (8 routes, all confirmed in code):**
  - `GET /health` — public.
  - `GET /products`, `GET /warehouses`, `GET /inventory` — **read-only**, capped at 100 records,
    no filtering, no pagination.
  - `POST /receipts`, `POST /receipts/{id}/validate` — create and confirm incoming stock.
  - `POST /dispatches`, `POST /dispatches/{id}/validate` — create and confirm outgoing stock.
  - **There is no endpoint to create or update a product, warehouse, or supplier.** Every receipt
    and dispatch call requires the caller to already know Odoo's own internal integer IDs
    (`product_id`, `warehouse_id`, `supplier_id`) — confirmed by reading
    `controllers/receipts.py` and `controllers/dispatches.py` directly.
- **Authentication:** Bearer token = a real Odoo API key (`res.users.apikeys`), validated by Odoo's
  own framework before controller code runs. Additionally requires the **AgriWare API User** group.
- **Security groups:** **AgriWare Administrator** (manage API keys) implies **AgriWare API User**
  (call the REST API), which implies `stock.group_stock_user`. Company isolation is enforced both
  by explicit `company_id in env.companies.ids` filters in controller queries and by an `ir.rule`
  record rule on `agriware.api.key` itself.
- **Duplicate protection:** a PostgreSQL transaction-scoped advisory lock keyed on
  `external_reference`, used only for receipt/dispatch creation today.
- **Tests:** 8 test files (`test_authentication.py`, `test_authorization.py`,
  `test_catalog_endpoints.py`, `test_receipts.py`, `test_dispatches.py`, `test_api_keys.py`,
  `test_menu_visibility.py`, plus `common.py`) — covering exactly the capabilities above, nothing
  more.

### Current architecture diagram

```text
External WMS  --(HTTPS + API key, WMS-initiated)-->  AgriWare Connector  --(Odoo ORM)-->  Odoo 19  -->  PostgreSQL
```

Every request is initiated by the external WMS; Odoo never calls out to the WMS. All data lives in
Odoo's own database — the connector adds no separate datastore. This part of the architecture is
**not changing** — see [Part 2](#part-2--target-wms-first-architecture-proposed--not-implemented).

## Part 2 — Target (WMS-first) architecture (PROPOSED — NOT IMPLEMENTED)

### The problem this solves

Today, a business can only use AgriWare Connector if its products, warehouses, and suppliers
**already exist inside Odoo**, created through Odoo's own UI. A business that already runs its
warehouse operations in an external WMS — with its own product catalog, its own warehouse codes,
its own supplier list — currently has to re-create all of that by hand inside Odoo before the API
becomes useful at all. That's backwards for a business whose WMS is their real system of record.

### The three roles

```text
┌─────────────────────┐        ┌───────────────────────┐        ┌─────────────────────┐
│    CUSTOMER WMS      │        │   AGRIWARE CONNECTOR   │        │      ODOO 19         │
│                      │        │                        │        │                      │
│ Primary source of    │──────▶│ Secure integration and  │──────▶│ ERP: accounting,     │
│ warehouse operational│  REST │ synchronization layer   │  ORM  │ invoicing,           │
│ data: products,      │  API  │                        │        │ purchasing, sales,   │
│ warehouses, physical │       │ Maps WMS identifiers to │       │ and the inventory    │
│ stock, lots, receipt/│       │ Odoo records; enforces  │       │ engine that actually │
│ dispatch confirmations│      │ data-ownership rules;   │       │ executes stock moves │
│                      │◀──────│ never bypasses Odoo's   │       │                      │
└─────────────────────┘  Resp. │ own inventory workflow  │       └─────────────────────┘
                          erses └───────────────────────┘
```

- **Customer WMS** — becomes the primary source of warehouse *operational* data: what products
  exist, what warehouses exist, what's physically on the shelf, which lots/batches are in play, and
  confirmation that a receipt or dispatch physically happened. The WMS still **initiates every
  request** — this does not change.
- **AgriWare Connector** — becomes an explicit synchronization layer, not just a pass-through API.
  It translates the WMS's own identifiers into Odoo records (creating them on first sight, updating
  them on change), enforces which side owns which field (Part 2's
  [Data Ownership Matrix](#data-ownership-matrix) below), and always acts *through* Odoo's own
  supported processes (the stock move engine, the inventory-adjustment mechanism) — never by
  writing directly to low-level tables like `stock.quant` quantities.
- **Odoo 19** — keeps doing what it already does well: accounting, invoicing, purchasing, sales,
  and executing the actual stock-move engine. Odoo remains the ERP of record for financial data;
  it becomes a *receiver and processor* of warehouse data rather than the place that data
  originates.

**Important clarification — this does not mean building N vendor-specific integrations.** AgriWare
Connector remains **one generic REST API**. A WMS that can call REST and JSON speaks to the exact
same endpoints regardless of vendor. AgriWare Connector does not need, and will not gain, direct
proprietary-protocol access to any specific WMS vendor's own API — a WMS that can't speak this
generic API needs a custom adapter (an existing, already-documented paid service — see
[PROFESSIONAL_SERVICES.md](PROFESSIONAL_SERVICES.md)), built as a separate translation layer in
front of this same unchanged API, not as new code inside AgriWare Connector itself.

### Data Ownership Matrix

| Data | Owner | Notes |
|---|---|---|
| External product identity (the WMS's own product ID/SKU) | **WMS** | Odoo-side product record is created/updated to mirror it, never the reverse. |
| Warehouse identity (the WMS's own warehouse/site code) | **WMS** | Same pattern: Odoo's `stock.warehouse` record mirrors it. |
| Physical stock observations (what's actually on the shelf) | **WMS** | The WMS is the one with eyes on the physical warehouse. |
| Lot and batch information | **WMS** | The WMS assigns/tracks lot numbers; Odoo mirrors them for its own stock-move engine. |
| Warehouse receipt confirmations | **WMS** | The WMS confirms a physical receipt happened; Odoo validates the corresponding `stock.picking`. |
| Warehouse dispatch confirmations | **WMS** | Same pattern for outgoing stock. |
| Accounting configuration (chart of accounts, journals) | **Odoo** | Never touched by any WMS-facing endpoint. |
| Tax settings | **Odoo** | Never exposed to the API at all. |
| Financial reporting | **Odoo** | Out of scope for this integration entirely. |
| Customer invoices | **Odoo** | Out of scope — AgriWare Connector has no invoicing endpoints, proposed or otherwise. |
| ERP-specific commercial settings (payment terms, pricelists) | **Odoo** | Not writable by any proposed endpoint. |

**Enforcement principle:** every proposed write endpoint (Phase 3/5 below) exposes an explicit
**allow-list** of WMS-owned fields only — never a block-list of "fields to exclude." A field not on
the allow-list cannot be set by the API, full stop, regardless of what the request body contains.
This is the mechanism that prevents a WMS payload from ever touching accounting/tax/invoicing data,
even by accident or a malformed request.

**On "future configurable ownership policies":** the allow-list above is deliberately fixed and
simple for the first implementation phases (ownership *is* the rule, not *configurable per
customer*). A per-company configuration layer (e.g., "this customer's WMS may also set a public
product description field") is a legitimate future enhancement once the fixed version has been
used in production by at least one real integration — it is **not** part of the initial roadmap
(see [API_ROADMAP.md](API_ROADMAP.md)) and is called out as an open decision in the final report.

### Capability status matrix

| Capability | Status |
|---|---|
| Read products, warehouses, inventory | **Implemented** |
| Create/validate receipts, dispatches (by Odoo internal ID) | **Implemented** |
| Self-service API key management | **Implemented** |
| Company isolation, duplicate-transaction protection | **Implemented** |
| External ID mapping (WMS ID ↔ Odoo ID) | **Implemented** (Phase A — infrastructure only, no REST endpoints yet; see [EXTERNAL_ID_MAPPING.md](EXTERNAL_ID_MAPPING.md)) |
| Create/update products via API | **Implemented** (Phase B — see [PRODUCT_SYNCHRONIZATION.md](PRODUCT_SYNCHRONIZATION.md)) |
| Create/update warehouses via API | **Implemented** (Phase C — see [WAREHOUSE_SYNCHRONIZATION.md](WAREHOUSE_SYNCHRONIZATION.md)); existing-warehouse adoption is designed but not implemented |
| Create/update suppliers via API | **Implemented** (Phase D — see [SUPPLIER_SYNCHRONIZATION.md](SUPPLIER_SYNCHRONIZATION.md)); existing-partner adoption designed but not implemented |
| Unit-of-measure mapping | **Implemented** (Phase D — see [UOM_MAPPING.md](UOM_MAPPING.md)) — database-backed, admin-managed, layered on top of Phase B's hardcoded fallback |
| Initial inventory import / reconciliation | **Implemented** (Phase E — see [INITIAL_INVENTORY_IMPORT.md](INITIAL_INVENTORY_IMPORT.md)) — staged and human-reviewed only; native apply-to-stock handoff is manual, by design, not automated |
| Lot/serial support | **Implemented** (Phase F — see [LOT_BATCH_SYNCHRONIZATION.md](LOT_BATCH_SYNCHRONIZATION.md)); the blanket rejection of a tracked product with no lot_external_id remains in place unchanged — only a product whose line now names its lot/serial is accepted |
| Receipts/dispatches addressable by external ID (not just Odoo ID) | **Implemented** (Phase G — see [WMS_TRANSACTION_SYNCHRONIZATION.md](WMS_TRANSACTION_SYNCHRONIZATION.md)); additive alongside the original numeric-ID schema, which is unchanged |

### Security model (current, extended by proposal)

Unchanged principles that every new endpoint must also follow: Bearer-token authentication via
real Odoo API keys, the AgriWare API User/Administrator group split, company-scoped queries, and
controller-level `has_access()` checks before any write (exactly as `receipts.py` already does for
`stock.picking`/`stock.move`). Full detail on how this extends to the new models and endpoints is
in [WMS_FIRST_INTEGRATION_PLAN.md](WMS_FIRST_INTEGRATION_PLAN.md#security-and-multi-company-design).
