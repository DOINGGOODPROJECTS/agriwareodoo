# AgriWare Connector API Reference

This document describes the REST API exposed by the AgriWare Connector module, how external
warehouse management systems (WMS) authenticate against it, and the request/response contract
for every endpoint.

## How an external WMS connects

```text
External WMS  --(HTTPS + API key)-->  AgriWare Connector  --(Odoo ORM)-->  Odoo 19  -->  PostgreSQL
```

1. An Odoo administrator creates a dedicated Odoo user for the external WMS integration (not a
   human login) and adds it to the **AgriWare API User** security group (or a group that implies
   it, such as **AgriWare Administrator**).
2. The administrator generates an API key for that user: **Settings → Users & Companies → Users →
   (select the integration user) → Account Security tab → New API Key**. Odoo only displays the
   key once; store it in the external system's secret manager, never in source control.
3. The external WMS sends that key as a Bearer token on every request to a protected endpoint.
4. The connector translates WMS actions into standard Odoo stock operations
   (`stock.picking` / `stock.move`): an incoming delivery becomes a **receipt**, an outgoing
   delivery becomes a **dispatch**. Both follow a two-step lifecycle — **create** (draft) then
   **validate** (confirms the operation in Odoo's stock workflow).

## Base URL

All endpoints are rooted at `/agriware/api/v1`. In local development this is
`http://localhost:8069/agriware/api/v1`.

## Authentication

| Endpoint type | `auth` mode | Requirement |
|---|---|---|
| Health check | `public` | None |
| All other endpoints | `bearer` | `Authorization: Bearer <odoo-api-key>` header |

The Bearer token is an **Odoo API key**, not a separate AgriWare credential. Odoo's HTTP layer
validates the key *before* any AgriWare controller code runs. If the header is missing, malformed,
or the key is invalid/revoked, Odoo itself returns a **plain-text HTML 401 response** (not JSON):

```http
HTTP/1.1 401 UNAUTHORIZED
Content-Type: text/html

<!doctype html>
<html lang=en>
<title>401 Unauthorized</title>
<h1>Unauthorized</h1>
<p>User not authenticated, use an API Key with a Bearer Authorization header.</p>
```

Clients must therefore check the HTTP status code first and only attempt to parse the body as
JSON when the status code indicates a controller-level response (see below).

## Authorization

Once authenticated, every non-public endpoint additionally requires the authenticated user to
belong to the **AgriWare API User** group (`agriware_connector.group_agriware_api_user`), or a
group that implies it (**AgriWare Administrator**). This check happens inside the controller, so
a valid API key alone is **not** sufficient — the key's owning user must also carry the group.
Requests from an authenticated user lacking the group receive a JSON 403 response:

```json
{"status": "error", "message": "Access denied: AgriWare API User role required"}
```

Record-level access is further scoped to the warehouses/companies the authenticated user has
access to (`warehouse.company_id in env.companies.ids`). There is currently no per-warehouse
allow-list — any warehouse within the user's allowed companies is reachable. Restricting a given
integration user to a specific subset of warehouses is a known limitation; see
[Known limitations](#known-limitations).

## Response envelope

All controller-level JSON responses (everything except the framework-level 401 above) share the
shape:

```json
{"status": "success", ...}
```
or
```json
{"status": "error", "message": "..."}
```

## HTTP status codes

| Code | Meaning | Produced by |
|---|---|---|
| 200 | Success (read, or validate) | Controller |
| 201 | Resource created | Controller (`POST /receipts`, `POST /dispatches`) |
| 400 | Malformed JSON or invalid/missing field | Controller |
| 401 | Missing, malformed, or invalid API key | Odoo framework (before controller runs) |
| 403 | Authenticated but not authorized, or action out of scope for this API | Controller |
| 404 | Referenced record (warehouse, partner, product, receipt, dispatch) not found | Controller |
| 409 | Conflict — duplicate reference, state mismatch, quantity mismatch, concurrent lock | Controller |
| 500 | Unexpected server-side error (logged, transaction rolled back) | Controller |

## External reference naming convention

`external_reference` is the idempotency key the WMS assigns to a receipt or dispatch (stored as
the Odoo picking's `origin`). To validate a receipt or dispatch through this API, its
`external_reference` **must** use the matching prefix:

| Operation | Required prefix |
|---|---|
| Receipt | `AGRIWARE-RCPT-` |
| Dispatch | `AGRIWARE-DISP-` |

This prevents the API from being used to validate draft stock operations that were not created
by AgriWare (e.g. pickings created manually in the Odoo UI). A validate call against a reference
without the correct prefix returns `403` with `"<Receipt|Dispatch> is not managed by AgriWare"`.
WMS integrations must choose `external_reference` values with the correct prefix from the start.

---

## Endpoints

### 1. `GET /agriware/api/v1/health`

Public health check. No authentication required.

**Response 200**
```json
{
  "status": "success",
  "service": "AgriWare Connector",
  "api_version": "1.0",
  "message": "AgriWare API is running"
}
```

---

### 2. `GET /agriware/api/v1/products`

Returns up to 100 products, ordered by id.

**Auth:** Bearer API key + AgriWare API User group.

**Response 200**
```json
{
  "status": "success",
  "count": 2,
  "products": [
    {"id": 14, "name": "Urea 50kg Bag", "default_code": "FERT-UREA-50", "barcode": "6161100000012", "active": true},
    {"id": 15, "name": "Maize Seed 25kg Bag", "default_code": "SEED-MAIZE-25", "barcode": "", "active": true}
  ]
}
```

**Errors:** `403` (not authorized), `500` (unexpected failure).

---

### 3. `GET /agriware/api/v1/warehouses`

Returns up to 100 warehouses, ordered by id.

**Auth:** Bearer API key + AgriWare API User group.

**Response 200**
```json
{
  "status": "success",
  "count": 1,
  "warehouses": [
    {"id": 1, "name": "Main Warehouse", "code": "WH", "company_id": 1, "company_name": "My Company"}
  ]
}
```

**Errors:** `403`, `500`.

---

### 4. `GET /agriware/api/v1/inventory`

Returns up to 100 non-zero stock quants in internal locations, ordered by id.

**Auth:** Bearer API key + AgriWare API User group.

**Response 200**
```json
{
  "status": "success",
  "count": 1,
  "inventory": [
    {
      "product_id": 14,
      "product_name": "Urea 50kg Bag",
      "location_id": 8,
      "location_name": "Main Warehouse/Stock",
      "quantity": 420.0,
      "reserved_quantity": 0.0,
      "unit": "kg"
    }
  ]
}
```

**Errors:** `403`, `500`.

---

### 5. `POST /agriware/api/v1/receipts`

Creates a draft incoming stock receipt (`stock.picking` of the warehouse's incoming type).

**Auth:** Bearer API key + AgriWare API User group + `create` rights on `stock.picking`/`stock.move`.

**Request body**
```json
{
  "external_reference": "AGRIWARE-RCPT-00042",
  "warehouse_id": 1,
  "supplier_id": 37,
  "products": [
    {"product_id": 14, "quantity": 500}
  ]
}
```

| Field | Type | Constraints |
|---|---|---|
| `external_reference` | string | Required, 1–128 chars, must use the `AGRIWARE-RCPT-` prefix if it will later be validated |
| `warehouse_id` | integer | Required, > 0, must resolve to a warehouse in the caller's companies |
| `supplier_id` | integer | Required, > 0, must resolve to an existing partner |
| `products` | array | Required, 1–100 entries |
| `products[].product_id` | integer | Required, > 0, must be a stock-tracked (`consu` + storable) product |
| `products[].quantity` | number | Required, `0 < quantity <= 1,000,000,000` |

**Response 201**
```json
{
  "status": "success",
  "receipt_id": 102,
  "receipt_reference": "WH/IN/00042",
  "external_reference": "AGRIWARE-RCPT-00042",
  "state": "draft"
}
```

**Errors**

| Code | Condition |
|---|---|
| 400 | Invalid JSON / not an object / invalid `external_reference`, `warehouse_id`, `supplier_id`, `products`, or a product line / product not stock-tracked |
| 403 | Not authorized, or insufficient Odoo create rights |
| 404 | Warehouse, supplier, or product not found |
| 409 | `external_reference` already used for this warehouse's incoming operations — response includes the existing `receipt_id` |
| 500 | Unexpected failure (transaction rolled back) |

Concurrent requests for the same `external_reference` are serialized with a PostgreSQL
transaction-scoped advisory lock, so only one receipt is ever created even if two identical
requests arrive at the same time; the second resolves to the `409` duplicate response.

---

### 6. `POST /agriware/api/v1/receipts/{receipt_id}/validate`

Confirms a draft receipt and records received quantities, then validates it in Odoo.

**Auth:** Bearer API key + AgriWare API User group + `read`/`write` rights on `stock.picking`, `write` on `stock.move`.

**Request body**
```json
{
  "external_reference": "AGRIWARE-RCPT-00042",
  "received_quantities": [
    {"product_id": 14, "quantity": 500}
  ]
}
```

| Field | Type | Constraints |
|---|---|---|
| `external_reference` | string | Required, must match the receipt's stored origin exactly, must use `AGRIWARE-RCPT-` prefix |
| `received_quantities` | array | Required, 1–100 entries, no duplicate `product_id` |
| `received_quantities[].product_id` | integer | Required, > 0 |
| `received_quantities[].quantity` | number | Required, finite, `0 < quantity <= 1,000,000,000` |

The set of products in `received_quantities` must exactly match the receipt's move lines, and
each quantity must exactly match the expected quantity (partial receipts are not yet supported).

**Response 200**
```json
{
  "status": "success",
  "receipt_id": 102,
  "receipt_reference": "WH/IN/00042",
  "external_reference": "AGRIWARE-RCPT-00042",
  "state": "done"
}
```

**Errors**

| Code | Condition |
|---|---|
| 400 | Invalid JSON / invalid fields / receipt has no active lines / products don't match receipt |
| 403 | Not authorized / insufficient rights / `external_reference` lacks the `AGRIWARE-RCPT-` prefix |
| 404 | Receipt not found (or not an incoming operation in the caller's companies) |
| 409 | `external_reference` mismatch, receipt already validated/cancelled/not in draft, quantity mismatch, or Odoo rejects the validation |
| 500 | Unexpected failure (transaction rolled back) |

The receipt row is locked (`SELECT ... FOR UPDATE NOWAIT`) for the duration of validation, so two
concurrent validate calls on the same receipt cannot both succeed.

---

### 7. `POST /agriware/api/v1/dispatches`

Creates a draft outgoing stock dispatch (`stock.picking` of the warehouse's outgoing type).

**Auth:** Bearer API key + AgriWare API User group + `create` rights on `stock.picking`/`stock.move`.

**Request body**
```json
{
  "external_reference": "AGRIWARE-DISP-00017",
  "warehouse_id": 1,
  "customer_id": 52,
  "products": [
    {"product_id": 14, "quantity": 120}
  ]
}
```

| Field | Type | Constraints |
|---|---|---|
| `external_reference` | string | Required, 1–128 chars, must use `AGRIWARE-DISP-` prefix if it will later be validated |
| `warehouse_id` | integer | Required, > 0, must resolve to a warehouse in the caller's companies |
| `customer_id` | integer | Required, > 0, must resolve to an existing partner |
| `products` | array | Required, 1–100 entries, no duplicate `product_id` |
| `products[].product_id` | integer | Required, > 0, must be a stock-tracked product visible to the warehouse's company |
| `products[].quantity` | number | Required, finite, `0 < quantity <= 1,000,000,000` |

**Response 201**
```json
{
  "status": "success",
  "dispatch_id": 58,
  "dispatch_reference": "WH/OUT/00017",
  "external_reference": "AGRIWARE-DISP-00017",
  "state": "draft"
}
```

**Errors:** same pattern as receipts creation (400 / 403 / 404 / 409 / 500), using
`"dispatch_id"` instead of `"receipt_id"` in the 409 duplicate payload. Duplicate creation is
protected by the same transaction-scoped advisory lock.

---

### 8. `POST /agriware/api/v1/dispatches/{dispatch_id}/validate`

Confirms a draft dispatch, reserves stock, records picked quantities, and validates it.

**Auth:** Bearer API key + AgriWare API User group + `read`/`write` rights on `stock.picking` and `stock.move`.

**Request body**
```json
{
  "external_reference": "AGRIWARE-DISP-00017",
  "dispatched_quantities": [
    {"product_id": 14, "quantity": 120}
  ]
}
```

| Field | Type | Constraints |
|---|---|---|
| `external_reference` | string | Required, must match the dispatch's stored origin exactly, must use `AGRIWARE-DISP-` prefix |
| `dispatched_quantities` | array | Required, 1–100 entries, no duplicate `product_id` |
| `dispatched_quantities[].product_id` | integer | Required, > 0 |
| `dispatched_quantities[].quantity` | number | Required, finite, `0 < quantity <= 1,000,000,000` |

Constraints: exact quantity match only (no partial dispatch), lot/serial-tracked products are not
yet supported, and the dispatch must be fully reserved before Odoo will validate it.

**Response 200**
```json
{
  "status": "success",
  "dispatch_id": 58,
  "dispatch_reference": "WH/OUT/00017",
  "external_reference": "AGRIWARE-DISP-00017",
  "state": "done"
}
```

**Errors**

| Code | Condition |
|---|---|
| 400 | Invalid JSON / invalid fields / no active move lines |
| 403 | Not authorized / insufficient rights / `external_reference` lacks the `AGRIWARE-DISP-` prefix |
| 404 | Dispatch not found (or not an outgoing operation in the caller's companies) |
| 409 | Lock unavailable (concurrent validation in progress), reference mismatch, state mismatch, product/quantity mismatch, lot/serial tracking present, insufficient reserved stock, or Odoo rejects the validation |
| 500 | Unexpected failure (transaction rolled back) |

---

## Known limitations

- No pagination: list endpoints (`products`, `warehouses`, `inventory`) hard-cap at 100 records.
- No per-warehouse access control: any user in the AgriWare API User group can act on any
  warehouse within their allowed companies — there is no way to restrict one integration user to
  a specific warehouse subset.
- Partial receipts and partial dispatches are not supported; quantities must match exactly.
- Lot/serial-tracked products are not supported for dispatch validation.
- Multiple move lines for the same product on one receipt are not supported.
