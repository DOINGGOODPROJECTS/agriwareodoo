# Release Notes — WMS-First AgriWare Connector

**For:** customers and prospects evaluating whether to upgrade from the currently-published
`19.0.1.0.0` marketplace release. **This release is `19.0.2.0.0`** — finalized in this
release-candidate pass (Step 130), per the recommendation in
[PRODUCTION_READINESS_REPORT.md's Section O](PRODUCTION_READINESS_REPORT.md#o-recommended-version-number).

## What's new

This release turns AgriWare Connector from a read-only catalog + legacy-transaction API into a full
**WMS-first** integration surface — your WMS can now be the primary source of product, warehouse,
supplier, and traceability data, with Odoo mirroring it, not the other way around.

- **Product, warehouse, and supplier synchronization** — create and update all three directly from
  your WMS, addressed by your own external IDs. Pricing, accounting, and tax fields are never
  exposed to any of these endpoints — an allow-list, not a block-list, so there's no field a future
  Odoo install could accidentally expose by this module forgetting to block it.
- **Unit-of-measure mapping** — map your WMS's own unit codes to real Odoo units through an
  admin-only screen. This module never invents a conversion factor; it only references units you
  (or Odoo itself) already configured.
- **Lot and serial number synchronization** — create and resolve native Odoo lots, tied to a
  specific product, with duplicate and wrong-product-combination protection. Receipts, dispatches,
  and inventory imports can all reference a specific lot by your own external ID.
- **Staged initial inventory import** — submit what your WMS believes is on hand; Odoo compares it
  against actual stock and stages the difference for a human Inventory Manager to review.
  **This never changes real stock by itself** — applying a reviewed count still takes one manual
  step in Odoo's own native Inventory Adjustment screen, every time, by design.
- **Receipt and dispatch synchronization, externalized** — the original numeric-ID creation flow is
  completely unchanged; a new, parallel schema lets you address warehouse, supplier, product, unit,
  and lot entirely by your own external IDs instead.
- **Transaction status retrieval** — look up a receipt or dispatch's current state by your own
  external reference, without needing to track Odoo's internal numeric IDs yourself.

## Security improvements

- **A real authorization-isolation vulnerability was found and fixed** before any of the above
  shipped: an API key with no external-system binding could previously inherit authorization from
  an unrelated key bound to the same company. Fixed by giving every bound key its own, never-shared
  dedicated integration user — confirmed closed via real HTTP reproduction, and covered by two
  dedicated regression suites that re-run clean with every change since.
- Every new write endpoint re-derives its authorization from the authenticated key itself, never
  from anything the client sends in the request body.

## Installation requirements

Unchanged: Odoo 19 Community, with `connector`/`component`/`component_event`/`queue_job` bundled as
before. No new external dependency was introduced by this entire body of work.

## Upgrade instructions

Upgrading from `19.0.1.0.0` is a standard Odoo module upgrade (`-u agriware_connector`, or
**Apps → Upgrade** from the UI) — **verified directly** in this release-preparation pass: the
published version was installed fresh, real data was created under it, upgraded in place to the
current code, and every pre-existing record was confirmed still present afterward, with the full
test suite re-passing against the upgraded database. No manual data migration step is required.

## Known limitations

See [CUSTOMER_INSTALLATION_GUIDE.md](CUSTOMER_INSTALLATION_GUIDE.md) for the full, customer-facing
list. In short: no pagination on list endpoints, no partial receipts/dispatches, no expiration-date
tracking, no bulk/batch endpoints, and the final "apply approved count to real stock" step for
inventory imports remains a deliberate manual action in Odoo's own UI, not something this API
automates.

**A genuine multi-company consideration, not a defect:** products are shared across every company
in the same Odoo database by design — see
[ARCHITECTURE.md's Multi-company behavior section](ARCHITECTURE.md#multi-company-behavior--whats-shared-vs-isolated-verified-directly-phase-h)
before considering this module for a shared-hosting deployment of unrelated customers.
