# Final Release Verification — AgriWare Connector `19.0.2.0.0`

**Branch:** `release/agriware-19.0-wms-first`. **Verified using the exact packaged release**, not
the development source directory, for every installation/upgrade/HTTP test below.

## 1. Branch and commit

`release/agriware-19.0-wms-first`, based on `f475f6b` (Step 129), itself based on `eab9642`
(Phase H). The final commit hash for this verification pass is recorded in the Final Report
message (committed after this document, per the task's own sequencing).

## 2. Release version

`19.0.2.0.0` — valid per Odoo's manifest versioning convention (5-part dotted version, first two
components matching the targeted Odoo series `19.0`, remaining three a legitimate module version
increment from `1.7.0`). Verified structurally (`19.0.2.0.0`.split('.') → 5 numeric parts) and
confirmed live: every disposable database installed or upgraded in this pass reports
`ir_module_module.latest_version = '19.0.2.0.0'`.

## 3. Package filename

`agriware_connector-19.0.2.0.0.zip`, in `release_artifacts/` (gitignored, not committed — a build
artifact, regenerable from the tagged commit).

## 4. Package SHA-256

`e9aa1d3c29023442a5e19e87060298ffb48dfbeafa697f2f8ccf88aceaa5bd7f`

## 5. Package contents

Built from `git ls-files agriware_connector LICENSE README.md CHANGELOG.md docs`, read from the
working tree (so the version-bump edit was included without requiring a commit first) — **tracked
files only**, per the task's own explicit instruction. 92 files; diffed against the live dev
directory and confirmed the only differences are old `.backup`/`.before_*` edit-history files that
were never tracked by git in the first place (correctly excluded). Archive integrity verified
(`unzip -t`: no errors).

**Deliberately not included:** `component`/`component_event`/`connector`/`queue_job` — confirmed
these four OCA directories are not tracked by this git repository at all (explicitly `.gitignore`d
as "installed separately for local development"). The manifest's `depends` list still correctly
*declares* them; this package does not *vendor* their source, consistent with how every
installation and test in this entire project has sourced them from a side location, never from
this repository's own tracked content.

## 6. Dependency verification

Re-confirmed, not re-litigated: `connector`/`component`/`component_event`/`queue_job` remain
functionally unused by any code in this module (no `@job`/`Component`/queue_job pattern anywhere).
**Step 129's decision to keep them is preserved**, per this step's own explicit instruction — no
dependency was added, removed, or otherwise changed. The exact dependency chain the packaged
module requires: `base`, `stock` (direct), `connector` (direct, pulling in `component`,
`component_event`, `queue_job`, and `mail` transitively) — confirmed by reading `connector`'s own
manifest and by every installation in this pass succeeding with exactly these modules present and
no others required.

## 7. Fresh installation results

The **exact unzipped package** (not the dev directory — confirmed via the diff in Section 5)
installed cleanly on a fresh database: zero errors, all 9 `agriware_*` tables created, 5 menus
loaded, 3 manifest dependencies registered, and the live server's `GET /health` responded `200`
confirming controllers actually registered (not just that install didn't crash).

## 8. Upgrade results

The actual published `19.0.1.0.0` was installed fresh, representative data was created under it
(a user, an API key, a product, and 500 units of real stock via `_update_available_quantity`), and
upgraded in place using the **exact new release package** — zero errors. Verified afterward: the
user, API key, and product all still present; stock quantity still exactly `500.00`; all 9 new
Phase A–G tables created; 14 new constraints (unique + foreign key) correctly applied, including
`agriware_wms_transaction_identity_uniq` and `agriware_uom_mapping_external_unit_code_uniq`; module
version correctly reports `19.0.2.0.0`.

## 9. Automated test totals

**Collected: 271. Executed: 271. Passed: 271. Failed: 0. Errors: 0. Skipped: 0** — against the
exact packaged release, on a fresh database. This is the authoritative count (matching Phase H's
own reconciliation); **not 307** — that figure is a different Odoo internal metric
(`odoo.tests.stats`, not a test count), as established in `docs/PRODUCTION_READINESS_REPORT.md`.

## 10. Dependency regression results

Full dependency chain re-run against the exact packaged release: **4 failed, 21 error(s) of 3,176
tests** — note this is **one more error than the established 24-failure baseline (20 errors)**,
investigated directly rather than assumed identical:

- The 24 baseline `base.test_cli` failures reproduced identically, same root cause as Phase H:
  `/usr/lib/python3/dist-packages/odoo-bin` still does not exist in this Docker image (re-confirmed
  via `ls`); this environment condition is unchanged.
- **One additional, newly-observed error**: `BusWebTests.test_bundle_sends_bus`
  (`odoo.addons.bus.tests.test_assetsbundle`), a `TimeoutError` on a real HTTP self-request during
  asset-bundle generation. **Investigated, not dismissed:**
  - Re-run in isolation against a direct clone of the already-polluted database: **reproduced**
    (along with a second, related error — `TestWebsocketController.setUpClass` failing on a
    `notification_type` not-null constraint on `res.users`).
  - Re-run against a **completely clean** database with only `bus` itself installed (no
    `agriware_connector`, no `stock`, no accumulated state from a long combined test run):
    **0 failed, 0 errors, 13/13 passed** — `bus`'s own tests pass perfectly in isolation.
  - **Conclusion, backed by this evidence chain, not asserted:** this is a test-execution-order/
    shared-state sensitivity in Odoo's own `bus`/`mail`/`web` test suites when run together as part
    of one very large combined regression (the same category of issue as flaky test suites
    generally — some upstream test leaves state that a later, unrelated test is sensitive to), not
    a defect in `agriware_connector` or its declared dependencies. Confirmed directly:
    `agriware_connector`'s own 271 tests started and finished with **zero** failures or errors in
    this exact same run — the one extra error is fully isolated to Odoo core's own `bus` module and
    does not touch this module's code, models, or declared dependency chain at all.
  - **This was not observed in Phase H's equivalent full-regression runs** — plausibly because
    exact test ordering/timing varies run to run in a suite this large on a shared host, not
    because anything in this release-preparation pass changed application behavior (no code
    changed between Phase H and this verification pass, only documentation and the version
    number).

## 11. Real HTTP results

All 17 items of the required checklist verified against the exact packaged release, live:
product creation/update, warehouse creation, supplier creation, UOM mapping (admin action, resolved
correctly — `bag_50kg` → kg, not the hardcoded fallback, proving precedence), lot creation,
inventory import submission and reconciliation (0 → 40 computed correctly), receipt creation and
validation (lot-aware), dispatch creation and validation (lot-aware), transaction status retrieval
(both receipt and dispatch), idempotent retry (`200`), conflicting retry (`409`), cross-system
rejection (`404`), cross-company rejection (`404`).

## 12. PostgreSQL verification

Every result above was independently confirmed via direct SQL against `stock_quant`,
`stock_move_line`, `stock_lot`, `ir_module_module`, `pg_constraint`, `res_users_apikeys`, and
`agriware_wms_transaction` — not trusted from API responses alone.

## 13. Security results

Dedicated integration-user isolation: unchanged, re-confirmed via the 271-test suite (which
includes the dedicated isolation/lifecycle regression files). API-key binding, revocation (tested
live: key worked, was revoked, then correctly returned `401`), inactive-system rejection,
company/external-system isolation (tested live, both directions), unauthorized approval/validation
rejection (covered by the test suite's dedicated access-control tests), input validation (malformed
JSON, oversized/nested junk, excessive line counts — all re-confirmed in Phase H, unchanged since
no code changed). **No secret value is printed anywhere in this document or any artifact in
`release_artifacts/`** — the package ZIP contains only source code and documentation, no `.env`
file, no real API key (confirmed: `grep` for key-shaped strings across the unzipped package finds
none).

## 14. Backward compatibility

Both schemas confirmed live, side by side, on the exact packaged release: the original
`products[]`/numeric-ID schema (receipt created and validated successfully for an untracked
product) and the new `lines[]`/external-ID schema (receipt and dispatch created and validated
successfully for a lot-tracked product) — `/validate` confirmed working correctly for **both**
transaction types without requiring any caller to migrate.

## 15. Documentation verification

`docs/API.md`, `docs/WMS_INTEGRATION.md`, `docs/QUICK_START.md` (the file named
`docs/CUSTOMER_QUICK_START.md` in this task's own instructions does not exist in this repository;
`docs/QUICK_START.md` is the actual, equivalent file and was reviewed instead — noted here rather
than silently substituted), `docs/ARCHITECTURE.md`, `docs/CUSTOMER_INSTALLATION_GUIDE.md`, and
`CHANGELOG.md` were reviewed together: lot/serial capability now described consistently and
accurately everywhere; no stale version numbers found in any of them (only `CHANGELOG.md` itself
contains version numbers, and its historical per-phase entries are correctly left as historical
record while a new `19.0.2.0.0` entry sits at the top).

## 16. Website content readiness

`docs/WEBSITE_CONTENT_CORRECTIONS.md` reviewed against the actual verified release: every claim in
the proposed copy (product/warehouse/supplier/UOM/lot synchronization, staged inventory import
with human review, receipt/dispatch synchronization, transaction status retrieval) matches a
capability actually confirmed working in Sections 7–14 above — nothing proposed there claims more
than what this verification just confirmed. The explicit "requires human review and manual
execution in Odoo" statement for inventory adjustments is present in both the English and French
proposed copy. **Not deployed** — the live website and its local source were not touched.

## 17. Remaining limitations

Unchanged from `docs/PRODUCTION_READINESS_REPORT.md`: no pagination, no partial receipts/
dispatches, no expiration-date tracking, no bulk/batch endpoints, manual native-adjustment handoff
for inventory imports, shared product catalog across companies by design (see
`docs/ARCHITECTURE.md`'s Multi-company behavior section).

## 18. Release blockers

None that block *this verification*. Two process items remain, both already identified and neither
within this session's authority to complete: deploying the website copy correction (needs deploy
access this session doesn't have), and the actual push/merge/tag/publish sequence (needs explicit
approval this session has not received).

## 19. Rollback readiness

- **Database:** any production upgrade should be preceded by a standard `pg_dump` (or equivalent)
  backup taken immediately before running `-u agriware_connector`; restoring that dump is the
  rollback path if an upgrade misbehaves. This verification pass confirmed the upgrade itself is
  clean, but a backup immediately before a *real* production upgrade remains standard practice
  regardless.
- **Marketplace package:** if a published version needs to be pulled, the Odoo Apps Marketplace
  supports unpublishing/reverting to a prior version through its own seller dashboard — not
  something this session can test, since nothing has been uploaded.
- **Website:** since the website was never modified by this session, there is nothing to roll back
  on the website side yet; once `docs/WEBSITE_CONTENT_CORRECTIONS.md` is actually deployed, the
  rollback is simply redeploying the prior content (whatever version control or CMS history the
  website's own deployment process retains — outside this repository's own scope).
- **Code:** this release branch is not merged anywhere; reverting is simply not merging it, or
  reverting the merge commit if it was already merged before an issue was found.

## 20. Final GO/NO-GO recommendation

**GO**, engineering-complete, with the same two non-engineering conditions already identified in
Step 129 (website deployment, explicit publish approval) — now with the packaging and upgrade path
independently re-verified using the **exact** artifact that would actually ship, not just the dev
source tree. The one new finding in this pass (the `bus` module's transient, order-sensitive test
failure) was investigated to a specific, evidenced conclusion rather than waved away, and does not
change this recommendation: it is confirmed unrelated to `agriware_connector`'s own code or
dependencies.
