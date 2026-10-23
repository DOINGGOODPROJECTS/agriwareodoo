# Release Checklist — WMS-First AgriWare Connector

Tracks the release-preparation work done on `release/agriware-19.0-wms-first` (based on `eab9642`,
Phase H) against the conditions `docs/PRODUCTION_READINESS_REPORT.md` set for GO. Checked items
were verified in this pass, not assumed.

## Documentation corrections

- [x] `docs/API.md` — "lot/serial not supported" corrected to reflect Phase F, with the
  `lot_external_id` field documented in both receipt and dispatch validation tables.
- [x] `docs/QUICK_START.md` — corrected.
- [x] `docs/WMS_INTEGRATION.md` — corrected in both places it appeared.
- [x] `docs/COMMERCIAL_STRATEGY.md` — the root-cause instruction ("do not advertise... lot/serial
  support") corrected; this is what the stale website copy was following.
- [x] `agriware_connector/static/description/ICON_REQUIREMENTS.md` — "not yet created" corrected;
  `icon.png` confirmed to exist and match spec.
- [ ] **Live website copy** — proposed corrected English and French text prepared in
  `docs/WEBSITE_CONTENT_CORRECTIONS.md`. **Not applied** — the live website and its local source
  were not modified, per this task's own instruction. A maintainer with deploy access must apply
  these changes separately.

## New documentation

- [x] `CHANGELOG.md` — created, covering `19.0.1.0.0` → `19.0.1.7.0`.
- [x] `docs/ARCHITECTURE.md` — multi-company behavior section added (what's shared, what's
  isolated, shared-hosting implications).
- [x] `docs/RELEASE_NOTES_WMS_FIRST.md` — created.
- [x] `docs/RELEASE_APPROVAL_REPORT.md` — created.
- [x] `docs/WEBSITE_CONTENT_CORRECTIONS.md` — created.

## Installation guide

- [x] `docs/CUSTOMER_INSTALLATION_GUIDE.md` reviewed against this task's own 12-item list
  (supported environments, dependencies, installation, external system registration, API-key
  configuration, product/warehouse/supplier/lot sync, inventory import, receipt/dispatch sync) —
  already complete from Phase H; **no changes needed**.

## Dependency and maintainability review

- [x] `connector`/`component`/`component_event`/`queue_job` investigated — confirmed functionally
  unused (no `@job`, `Component`, or queue_job pattern anywhere in the codebase). **Recommendation:
  keep**, not remove — see `docs/RELEASE_APPROVAL_REPORT.md`'s Outstanding risks section for the
  full reasoning. Not removed in this pass.
- [x] `controllers/receipts.py`/`dispatches.py` duplication reviewed. **No refactor performed**, per
  this task's own instruction — documented as technical debt in
  `docs/RELEASE_APPROVAL_REPORT.md`.

## Package verification

- [x] Manifest: valid Python literal, all referenced `data` files exist, dependencies
  (`base`/`connector`/`stock`) correct, `license: "LGPL-3"` matches the repository `LICENSE` file.
- [x] All module XML files parse without error (`lxml` validation on every file).
- [x] `ir.model.access.csv` structurally consistent (8 columns throughout).
- [x] No secret, password, or real API key anywhere in git history (full-history search) — only a
  placeholder value in `.env.example`.
- [x] No unnecessary files **in the actual package**: `__pycache__/` and one stray
  `controllers/receipts.py.bak` exist in the local working tree but are **not tracked by git**
  (excluded by `.gitignore`) and would not be included in any archive built from this repository.
  Flagged for manual working-tree cleanup; not deleted by this pass since it wasn't created by this
  session's own work.
- [x] **Module version** — bumped to `19.0.2.0.0` in the Step 130 release-candidate pass, per that
  step's explicit instruction (left at `19.0.1.7.0` during Step 129 on purpose — see
  `docs/RELEASE_APPROVAL_REPORT.md`).

## Final testing

- [x] Full `agriware_connector` test suite re-run against this exact release-preparation commit:
  **271 passed, 0 failed, 0 errors** — the authoritative count from Phase H, not 307.
- [x] Fresh installation re-confirmed clean.
- [x] Upgrade path (published `19.0.1.0.0` → current code) re-confirmed clean, with pre-existing
  data intact, in Phase H; not re-run a third time in this pass since no application code changed.
- [x] Existing (legacy, numeric-ID) API behavior re-confirmed unaffected.

## Remaining before an actual release

1. Apply the website copy corrections in `docs/WEBSITE_CONTENT_CORRECTIONS.md` (requires deploy
   access this session does not have and was told not to use).
2. Decide and apply the actual release version number in the manifest.
3. Explicit approval to push/merge/publish — none of this has been done.
