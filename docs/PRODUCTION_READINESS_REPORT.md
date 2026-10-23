# Production Readiness Report — AgriWare Connector

**Assessment date:** 2026-10-22. **Branch assessed:** `feature/wms-production-readiness`, based on
`feature/wms-transaction-sync` @ `8b88d50` (Phase G), itself based on `cad5357` (Phase F). This is
Phase H of the WMS-first roadmap.

## A. Executive summary

AgriWare Connector has grown, across Phases A–G, from a read-only catalog API with legacy
numeric-ID receipt/dispatch creation into a full WMS-first integration surface: product, warehouse,
supplier, UOM, lot/serial, staged inventory import, and receipt/dispatch synchronization, all
addressable by external IDs, all company- and external-system-isolated, all built on Odoo's own
native models rather than a parallel data store.

This assessment built a realistic agricultural scenario (external system `AGRI-WMS-TEST`,
warehouse `WH-ANYAMA`, products `CASSAVA-001`/`MAIZE-001`/`COCOA-001`, supplier `SUP-001`, lot
`MAIZE-LOT-001`) on a disposable Odoo 19 database and ran it through real HTTP requests end to end,
verified every result against actual PostgreSQL rows (not just API responses), ran the complete
271-test automated suite, performed a security penetration pass, measured real performance at
100/1,000/5,000-product scale, and verified both a fresh installation and two upgrade paths.

**No critical security or data-integrity defect was found.** The known limitations are all
previously-documented, deliberate scope boundaries, not oversights. Two significant **documentation**
problems were found: one existing doc file (`docs/API.md` and two others) and the **live marketing
website** both still describe lot/serial tracking as unsupported, which is no longer true as of
Phase F — this is a customer-facing inaccuracy, not a code defect, and this assessment did not
modify the website per its own instructions. See Section P for the full Go/No-Go reasoning.

## B. Architecture verification

Reviewed directly against every model, controller, security file, and test in the module.

**WMS-first consistency:** every write endpoint across all seven phases follows the identical
pattern — Bearer token → AgriWare API User group → `resolve_authorized_external_system()`
(server-derived, never client-supplied) → `agriware.external.id.mapping` resolution scoped to
`(company, external_system)`. No exception was found.

**Architectural inconsistencies identified:**
- Two coexisting idempotency mechanisms for receipts/dispatches: the legacy advisory-lock/
  `origin`-match (pre-Phase-A, untouched) and the new `agriware.wms.transaction` database
  constraint (Phase G, for the new schema only). This is a **documented, deliberate** split (see
  [WMS_TRANSACTION_SYNCHRONIZATION.md](WMS_TRANSACTION_SYNCHRONIZATION.md)), not an oversight, but
  it does mean a future contributor must understand which path a given request took.
- Security pattern per model is inconsistent **by design** (native `ir.model.access.csv` grant for
  `product.product`/`stock.lot`; gated `sudo()` for `stock.warehouse`/`res.partner`/
  `agriware.inventory.import`/`agriware.wms.transaction`), reasoned individually in each phase's own
  doc. Correct as implemented, but worth a single consolidated reference for new contributors
  rather than七 separate explanations.
- `/validate` endpoints remain numeric-`product_id`-only while creation gained external-ID support
  (Phase G's own deliberate choice) — a real asymmetry a new integrator will notice.

**Duplicate logic identified (real, not assumed):**
- `_authenticate()` (Bearer + group + external-system resolution) is near-identically duplicated
  across `products.py`, `warehouses.py`, `suppliers.py`, `inventory_import.py`, `lots.py`, and
  inlined without a named method in `receipts.py`/`dispatches.py`'s legacy paths — six-plus
  near-identical copies.
- `_uom_root()` (the Odoo-19 `parent_path`-based UOM-compatibility check) is duplicated verbatim in
  `inventory_import.py`, `receipts.py`, and `dispatches.py`.
- The idempotency pattern (`_canonical_hash()` + pre-check + savepoint + `IntegrityError` recovery)
  is duplicated across the same three files.
- This is consistent with the project's established per-controller-file style (no shared base
  class has been introduced at any phase), not a new problem — but it is real, growing duplication
  that a future refactor should address before adding an eighth near-identical copy.

**Missing integration points:**
- No endpoint ever deletes or deactivates a mapping (product/warehouse/supplier/lot/transaction) —
  create-then-update only, consistent across every phase.
- No webhook/push from Odoo back to the WMS — fully WMS-initiated, documented as deliberate from
  Phase A onward.

**A real, previously-undocumented finding:** `connector` (and its own transitive dependencies
`component`, `component_event`, `queue_job`) is declared in the manifest and bundled with every
install, but **nothing in Phases A–G actually uses it** — confirmed by searching the entire
codebase for `@job`, `Component`, or any queue_job pattern: zero matches. This is presumably a
forward-looking dependency for future asynchronous processing, but today it is installed complexity
with no functional benefit.

**Data ownership conflicts:** none found. The WMS-owns/Odoo-owns matrix
([ARCHITECTURE.md](ARCHITECTURE.md#data-ownership-matrix)) is enforced by allow-lists on every
write endpoint, confirmed by direct code review of all seven phases' controllers — no endpoint
exposes a pricing, accounting, tax, or valuation field anywhere, and this was re-confirmed live (a
`list_price`/`standard_price` injection attempt on product creation was rejected as an unsupported
field — see Section G).

**A genuine multi-tenancy characteristic, confirmed live, not assumed:** products are deliberately
shared (`company_id = False`, Phase B's own design decision) — this means **any** company in the
same database can read **any other** company's product catalog via `GET /products`, by Odoo's own
standard semantics for shared records, not a bug introduced by this module. Confirmed directly:
a second test company's freshly-generated, correctly-scoped API key successfully listed the first
company's three products by name. This is appropriate for a single business group running multiple
legal entities on one Odoo instance (this architecture's evident target), but would be a real
cross-tenant disclosure if two **unrelated** customers were ever hosted in the same database without
further scoping work. `GET /warehouses` was also checked and found correctly isolated (warehouses
are never shared — Odoo's own native multi-company record rule, not an explicit filter in this
module's code, is what enforces it, since the controller's own query has no company domain at all;
this is fragile in the sense that adding `sudo()` to that query later would silently remove the
protection, though it is not a current defect).

## C. Feature verification matrix

| Capability | Status | Verified live this assessment |
|---|---|---|
| External system / dedicated integration user / bound key onboarding | ✅ | Yes — zero developer intervention required |
| Product sync (create/update/duplicate/UOM/company isolation/field rejection) | ✅ | Yes |
| Warehouse sync (native locations/picking types/duplicate/isolation) | ✅ | Yes |
| Supplier sync (external resolution/company ownership/shared-partner restriction) | ✅ | Yes |
| UOM handling (kg/g/ton, compatible/incompatible, packaging restriction, rounding) | ✅ | Yes |
| Lot/serial sync (creation/product match/duplicate/wrong-product rejection) | ✅ | Yes |
| Initial inventory import (staging/reconciliation/stale-detection/approval safety) | ✅ | Yes |
| Receipt sync (WMS-first + legacy, validate, lot-aware, stock increase) | ✅ | Yes |
| Dispatch sync (WMS-first + legacy, validate, lot-aware, stock decrease, lot isolation) | ✅ | Yes |
| Idempotency (all seven record types) | ✅ | Yes |
| Security (key lifecycle, cross-company, cross-system, injection, malformed input) | ✅ | Yes |
| Multi-company isolation (write) | ✅ | Yes |
| Multi-company isolation (catalog read) | ⚠️ shared by design | Yes — see Section B |

## D. Automated test results

**The previous report's "307 tests passed" needs correction, with the discrepancy fully traced,
not dismissed.** Three independent counts were cross-checked:

1. `grep -c '    def test_' agriware_connector/tests/test_*.py` → **271** actual test method
   definitions in source.
2. Unique `"Starting <Class>.<method> ..."` INFO log lines for `agriware_connector` tests in a full
   run → **271**, each appearing exactly once (no retries, no duplicates).
3. The `odoo.tests.result` summary line → `"... of 271 tests"`.

All three agree: **271 is the real, authoritative total.** The **307** figure came from a different
log line, `odoo.tests.stats`, traced directly in Odoo's own `odoo/tests/result.py`: it counts
entries in an internal `stats` dict keyed by `test.id()`, populated via `stopTest()` across
potentially multiple merged `OdooTestResult` objects (Odoo runs `-at_install` and `post_install`
tagged tests as separate passes that get merged). It is a performance/diagnostic aggregate, not a
count of distinct test methods, and should not have been quoted as "tests passed" in the Phase F/G
reports — that was an error in how this assessment's own prior reports characterized that number,
now corrected.

**Final, verified count: 271 passed, 0 failed, 0 errors, 0 skipped — on three separate databases**
(fresh install, fresh install + `-u` upgrade, and install-on-existing-`stock`-database), each run
independently in this assessment.

**The 24 recurring `base.test_cli` failures were investigated, not dismissed.** Concrete,
reproducible evidence:
- `test_help`, `test_help_subcommand`, `test_unknown_command`, `test_shell`,
  `test_upgrade_code_example`, `test_upgrade_code_help` (18 of the 24) all fail because they invoke
  `['/usr/bin/python3', '/usr/lib/python3/dist-packages/odoo-bin', ...]` as a subprocess —
  **confirmed directly:** `/usr/lib/python3/dist-packages/odoo-bin` does not exist in this Docker
  image (`ls` returns "No such file or directory"); the actual entry point is `/usr/bin/odoo`, a
  different file, installed by this image's own packaging. This is a packaging difference in the
  Docker image under test, unrelated to Odoo's application logic or to `agriware_connector` in any
  way.
- `test_upgrade_code_migrations [18.1-00-sql-constraint.py]` fails for an unrelated reason: it
  asserts that re-running a specific **upstream Odoo core** migration script against **upstream
  Odoo core's own files** produces no further changes, and in this exact nightly build, it does.
  This is a core-team concern about Odoo's own migration-script idempotency, with zero relationship
  to this module.
- **Conclusion, now backed by reproducible evidence rather than assumption:** both failure
  categories are genuinely environment/packaging artifacts of this specific Docker image, not
  defects in Odoo's application logic and certainly not in `agriware_connector`. Confirmed identical
  (same 4 failed + 20 errors, same test names) across every regression run performed in Phases
  E through H.

## E. Real HTTP test results

Full end-to-end scenario executed over real HTTP against a live, disposable Odoo 19 server (not
`odoo shell`, not direct ORM calls except where explicitly noted as test setup):

- Onboarding: external system created, bound key generated, dedicated integration user
  auto-created (`agriware-api-service-1-...@agriware.local`), authentication verified (valid key
  `200`, invalid key `401`, no-header `401`), health check `200`.
- Warehouse `WH-ANYAMA`, supplier `SUP-001`, products `CASSAVA-001`/`MAIZE-001`/`COCOA-001` created;
  duplicate product rejected (`409`); financial-field injection (`list_price`, `standard_price`)
  rejected (`400`).
- Lot `MAIZE-LOT-001` created against `MAIZE-001` (set to lot-tracked via direct backend action,
  as the API itself never changes tracking mode); incorrect lot/product combination rejected
  (`422`).
- UOM: kg (exact), grams→kg (2,500,000g → exactly 2,500.0kg), tonnes→kg (2.5t → exactly 2,500.0kg),
  incompatible unit (liters against a kg product, `422`), unconfigured packaging unit (`bag_50kg`,
  `400`, never guessed), fractional precision (1,234.567g → correctly rounded to 1.24kg per Odoo's
  own "Product Unit" precision).
- Inventory import: four imports staged; `stock_quant` confirmed to have **zero rows** despite all
  four successful submissions; one approved (quant count still `0` immediately after); one
  rejected; one driven through a real stale-data cycle (stock changed to 999 after submission,
  first approval correctly flipped to `stale` with refreshed numbers, second approval succeeded).
- Receipt of 3,000kg maize under `MAIZE-LOT-001`, validated, stock confirmed increased to exactly
  3,000 under the correct lot.
- A second maize lot (`MAIZE-LOT-002`) seeded with 1,000kg independently; a dispatch of 1,000kg
  specifically from `MAIZE-LOT-001` validated; confirmed via SQL that lot 1 decreased from 3,000 to
  2,000 while lot 2 remained **exactly** 1,000 — unrelated-lot isolation confirmed, not assumed.
- Idempotency: identical repeat (`200`), conflicting repeat (`409`); malformed JSON (`400`);
  unsupported-field/oversized-nested-junk injection (`400`); excessive line count over the 100-line
  cap (`400`).
- Multi-company: a second company's independently-generated, correctly-bound key could not resolve
  the first company's warehouse (`404`) or transaction status (`404`) — write and transaction-status
  isolation confirmed; catalog-read sharing confirmed and explained in Section B.

## F. PostgreSQL verification

Every claim above was independently confirmed with direct SQL against `stock_quant`,
`stock_move_line`, `stock_lot`, `stock_picking`, `agriware_external_id_mapping`,
`agriware_wms_transaction`, and `res_users_apikeys` — never trusted from the API response alone.

## G. Security assessment

| Test | Result |
|---|---|
| Invalid API key | `401` |
| Revoked API key | `401` (confirmed via `action_revoke()` then a live request) |
| Unbound API key | `403` on write endpoints; `200` on `GET` endpoints (correct, documented behavior) |
| Inactive external system | `403` |
| Cross-company access (write) | `404` (indistinguishable from "doesn't exist," by design) |
| Cross-system access (write, same company) | `404` |
| Cross-company/system transaction status | `404` |
| Unsupported field injection (financial fields) | `400`, rejected by allow-list |
| Malformed JSON | `400` |
| Oversized/deeply-nested junk field | `400`, rejected at the allow-list stage before any deep parsing |
| Excessive line count (150 lines, cap is 100) | `400` |
| Privilege escalation (unauthorized inventory approval) | `AccessError`, confirmed in unit tests (non-manager user) |
| Unauthorized stock validation | Covered by the same Bearer/group/binding chain as creation |

**API-key lifecycle**, re-confirmed (not re-litigated from scratch — the underlying fix and its
dedicated regression suite, `test_api_key_isolation_security.py` and
`test_api_key_lifecycle_security.py`, 17 tests, were re-run clean as part of the 271-test total):
creation, rotation (fresh dedicated user each time), revocation (immediate loss of authorization),
external-system deactivation (immediate), and the core guarantee — **a second token can never
inherit an unrelated integration's access**, because every *bound* key gets its own, never-shared
dedicated integration user.

No secret key value was printed or committed by this assessment; all raw keys generated during
testing exist only in disposable, already-dropped databases.

## H. Performance measurements

Measured on this assessment's own disposable, single-worker (`--workers=0`) Odoo instance, on a
shared development host with other background Odoo processes running concurrently (a full
regression suite and an upgrade test were running at the same time as most of this measurement) —
**these are real, reproducible numbers from this exact run, not invented, but they reflect a
contended, non-isolated environment, not a clean dedicated benchmark or a production multi-worker
deployment.**

| Operation | n | Elapsed | Throughput | Avg latency | Errors |
|---|---|---|---|---|---|
| Product sync | 100 | 18.5s | 5.4/s | 185ms | 0 |
| Product sync | 1,000 | 185.7s | 5.4/s | 186ms | 0 |
| Product sync | 5,000 | 781.6s | 6.4/s | 156ms | 0 |
| Warehouse sync | 50 | 17.5s | 2.9/s | 349ms | 0 |
| Supplier sync | 100 | 7.8s | 12.9/s | 78ms | 0 |
| Lot sync | 100 | 8.4s | 12.0/s | 84ms | 0 (corrected run) |
| Inventory import | 50 | 3.5s | 14.3/s | 70ms | 0 |
| Receipt creation | 50 | 8.5s | 5.9/s | 170ms | 0 |
| Dispatch creation | 50 | 7.0s | 7.1/s | 140ms | 0 |
| Status retrieval | 100 | 4.3s | 23.4/s | 43ms | 0 |

**Memory:** 114.4MB before the load run, 106.8MB after ~6,700 total requests including the
5,000-product batch — stable, no leak observed at this scale.

**A methodology note, reported honestly rather than hidden:** the first lot-sync measurement
attempt recorded 100/100 errors — not a product defect. The test product had never been switched to
lot-tracked mode (a step this API deliberately never performs itself); every request correctly
received `422`. Corrected by setting tracking via a direct backend action (as a real administrator
would) and re-measuring — the corrected figure above is the one that should be used.

**Throughput scales roughly linearly with n** (no quadratic blowup observed from 100 → 5,000
products), and **warehouse creation is the slowest per-record operation** (expected: it cascades
into native locations, picking types, routes, and sequences, not a single row insert).

## I. Fresh installation results

A completely fresh Odoo 19 database, `-i agriware_connector` directly (pulling in `stock` and the
`connector` suite as dependencies): installed cleanly, zero errors, all menus/views/models present.

**Installation on a database that already had `stock` installed with demo data** (35 demo products,
2 demo warehouses): `agriware_connector` installed cleanly alongside it — zero errors, all 35 demo
products and both demo warehouses confirmed present and untouched afterward.

## J. Upgrade results

**True version upgrade**, as the task specifically asked for: the actual previously-published
module state (git commit `444b587`, manifest version `19.0.1.0.0`) was installed fresh, real data
was created under it (a user, an API key, a product), and then upgraded in place (`-u
agriware_connector`) to the current Phase G code (`19.0.1.7.0`) — **zero errors**, the pre-upgrade
user/key/product all confirmed still present afterward, every new Phase A–G table
(`agriware_external_system`, `agriware_inventory_import(_line)`, `agriware_uom_mapping`,
`agriware_wms_transaction`, etc.) confirmed created, and the full 271-test suite re-run against the
**upgraded** database — 271 passed, 0 failed, 0 errors, identical to the fresh-install result.

## K. Backward compatibility

The original, pre-Phase-A legacy receipt/dispatch schema (`products[]`, raw numeric IDs) is
byte-for-byte unchanged and was re-verified working in this assessment. All 271 tests — including
every pre-Phase-A test file — pass unmodified. No test was weakened, removed, or had its assertions
loosened at any point across Phases A–H.

## L. Known limitations

Carried forward from each phase's own documentation, not repeated in full here — see
[CUSTOMER_INSTALLATION_GUIDE.md](CUSTOMER_INSTALLATION_GUIDE.md) for the customer-facing summary.
Newly identified by this assessment:
- `connector`/`component`/`component_event`/`queue_job` are required but functionally unused today.
- Significant `_authenticate()`/`_uom_root()`/idempotency-helper duplication across controller
  files (a maintainability concern, not a functional one).
- Product/warehouse-template catalog data is shared across all companies in one database by
  design — a real consideration for prospective customers evaluating a shared-hosting deployment.

## M. Outstanding defects

**No functional code defect remains unresolved.** Two real bugs were found and fixed *during*
Phases F and G themselves (a dispatch double-reservation bug, and a `/validate` guard that would
have silently stranded Phase G receipts) — both are already fixed, regression-tested, and included
in the 271-test total; they are not outstanding.

**Documentation/content defects, outstanding, not fixed by this assessment:**
- The live marketing website (`website/src/content/en.ts`) states **"Lot/serial-tracked products
  are not supported"** — false since Phase F. Per this task's own instruction, the website was not
  modified; this is reported, not corrected.
- Three existing project docs (`docs/API.md`, `docs/QUICK_START.md`, `docs/WMS_INTEGRATION.md`)
  contain the same stale claim. These are project docs, not the live website, but fixing them was
  outside this phase's explicitly-scoped deliverables (create two new docs, not edit every old
  one) — flagged here as a recommended, low-risk follow-up.
- No `CHANGELOG.md` exists at the repository root.
- `agriware_connector/static/description/ICON_REQUIREMENTS.md` still says "Not yet created," but
  `icon.png` exists and meets the stated spec — a stale internal note, cosmetic only.

## N. Release packaging assessment

- Manifest structure, `license: "LGPL-3"`, and the repository's own `LICENSE` file are consistent
  (GNU LGPL v3, confirmed by reading both).
- Required dependencies (`base`, `connector`, `stock`) declared correctly; the three OCA modules
  `connector` pulls in are present in the repository and bundle correctly (confirmed by every
  install in this assessment succeeding).
- `.gitignore` correctly excludes `.env*` (except `.env.example`), `*.pem`, `*.key`; confirmed via
  full git history search that no real secret, password, or API key was ever committed — only the
  placeholder in `.env.example`.
- Screenshots and icon exist, are the correct format, and are referenced correctly from the
  manifest; `apps_listing_screenshot.png` resolves to a real, valid 1024×424 PNG.
- **The published marketplace version (`19.0.1.0.0`) is seven phases of functionality (A–G) behind
  the current development version (`19.0.1.7.0`)** — a real customer downloading from the
  marketplace today would get none of the WMS-first capability this entire assessment just verified.

## O. Recommended version number

**`19.0.2.0.0`** for the next public release. Rationale: the manifest's own versioning convention
bumped the third digit once per phase (`1.0.0` → `1.7.0` across Phases A–G); a release that bundles
all seven phases together represents a genuinely new capability generation (WMS-first addressing
for every record type, not just read-only catalog access), which the module's own precedent (and
standard semver-adjacent practice) suggests marking with a minor-version bump rather than another
patch-level increment.

## P. Go / No-Go recommendation

**Conditional GO**, not an unconditional one.

**What supports GO:** zero critical security or data-integrity defects found or left unresolved;
271/271 tests pass on three independently-verified database states (fresh, upgraded, and
layered-on-existing-stock); the core inventory-safety invariant (no automatic stock modification)
was independently re-verified via direct SQL at every relevant step, not just trusted; a real,
representative agricultural end-to-end scenario completed successfully over genuine HTTP; the
original API-key-isolation vulnerability remains fixed and covered by dedicated regression tests;
backward compatibility is complete and verified, not assumed.

**What makes it conditional, not unconditional:** the live website and three project docs actively
misstate a shipped capability (lot/serial support) as absent — publishing a marketplace release
while the public-facing website says the opposite of what the code does is a real customer-trust
problem, even though it is not a security or data-integrity issue. **Recommendation: update the
website copy and the three stale docs before or immediately alongside the next marketplace release**
— this is content work, not further engineering risk, and does not require re-running any of the
verification in this report.

**Do not** treat this report as authorization to publish, push, merge, or deploy anything — per the
task's own explicit instruction, none of that has been done, and all of it awaits separate,
explicit approval.
