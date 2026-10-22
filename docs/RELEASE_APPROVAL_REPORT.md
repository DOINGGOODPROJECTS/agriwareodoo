# Release Approval Report — WMS-First AgriWare Connector

**Branch:** `release/agriware-19.0-wms-first`, based on `eab9642` (Phase H). **Current manifest
version:** `19.0.1.7.0` (unchanged — see Outstanding risks). **Prior production-readiness
conclusion:** Conditional GO (`docs/PRODUCTION_READINESS_REPORT.md`), conditioned on correcting
stale lot/serial documentation.

## Features (this release covers)

External ID mapping (Phase A); product, warehouse, supplier, and UOM synchronization (Phases B–D);
staged, human-reviewed initial inventory import (Phase E); lot and serial synchronization
(Phase F); WMS-first receipt/dispatch synchronization with transaction status retrieval (Phase G).
Full detail in `CHANGELOG.md` and `docs/RELEASE_NOTES_WMS_FIRST.md`.

## Security improvements

The API-key isolation vulnerability (unbound keys inheriting a bound key's authorization) was found
and fixed before Phase D, via dedicated per-bound-key integration users. Re-verified clean in this
pass via the existing dedicated regression suites (`test_api_key_isolation_security.py`,
`test_api_key_lifecycle_security.py`), included in the 271-test total below.

## Installation requirements

Unchanged from the published release: Odoo 19 Community; `connector`/`component`/
`component_event`/`queue_job` bundled, as before.

## Upgrade instructions

Standard Odoo module upgrade (`-u agriware_connector`). Verified in Phase H with real data created
under the actually-published `19.0.1.0.0` and confirmed intact after upgrading in place to the
current code — not re-verified a second time in this pass since no application code changed between
Phase H and this release-preparation work (only documentation).

## Known limitations

Carried from `docs/PRODUCTION_READINESS_REPORT.md` Section L, unchanged: no pagination, no partial
receipts/dispatches, no expiration-date tracking, no bulk/batch endpoints, manual native-adjustment
handoff for inventory imports, shared product catalog across companies (see
`docs/ARCHITECTURE.md`'s new Multi-company behavior section).

## Outstanding risks

**Dependency review (`connector`/`component`/`component_event`/`queue_job`), investigated, not
assumed:**
- Not required indirectly — searched the entire codebase for `@job`, `Component`, `AbstractComponent`,
  or any queue_job usage pattern: zero matches.
- Most likely explanation: reserved for future asynchronous/queued processing (bulk sync jobs,
  retry queues) that hasn't been built yet, not dead weight added by accident.
- Not required by Odoo Apps Marketplace packaging rules — Odoo imposes no such requirement for any
  module category; this was the project's own choice.
- **Recommendation: keep, do not remove**, per this task's own explicit instruction not to remove a
  dependency merely because it appears unused. Removing a marketplace-listed dependency after a
  public release is itself a breaking packaging change that would need its own version bump and
  changelog entry — not something to do opportunistically during documentation cleanup. Revisit if
  a future phase actually needs async processing (natural trigger), or in a dedicated, deliberate
  cleanup review if a reasonable amount of time passes with still no use for it.

**Code maintainability (`controllers/receipts.py`/`dispatches.py`), inspected, not refactored:**
- Both files now contain, in full: a legacy numeric-ID path (unchanged since Phase A) and a
  WMS-first external-ID path (Phase G) side by side, each with its own validation, resolution, and
  response-building logic.
- Duplicated across these two files (and, to a lesser extent, `controllers/inventory_import.py`):
  the `_uom_root()` UOM-compatibility check, the idempotency pattern
  (`_canonical_hash()`/pre-check/savepoint/`IntegrityError` recovery), and a near-identical
  `_authenticate()` shape repeated across six-plus controller files project-wide.
- **No refactor performed in this release-preparation pass**, per explicit instruction. **Future
  technical debt, documented for a dedicated pass:** extract a shared mixin or helper module for
  (a) Bearer+group+external-system authentication, (b) the UOM-root compatibility check, and
  (c) the hash-based idempotency pattern. This would remove the growing duplication without
  changing any external behavior — a good candidate for its own small, behavior-preserving phase
  rather than bundling it into a documentation/release-prep pass.

**Module version left unchanged (`19.0.1.7.0`), deliberately, not an oversight:** the
production-readiness assessment recommended `19.0.2.0.0` for the next public release. This
preparation pass did **not** apply that bump to the manifest — deciding and setting the actual
version that ships is a release-execution action, not a preparation one, and belongs to whoever
has the authority to actually publish this release. Bumping it here, unasked, would have been
exactly the kind of "declare it ready to ship" overreach this task's own "await explicit approval"
instruction guards against.

**Website copy not applied:** `docs/WEBSITE_CONTENT_CORRECTIONS.md` contains the proposed English
and French replacement text. The live website and its local Next.js source were not touched, per
explicit instruction — this remains a real, open item before the website itself stops contradicting
the shipped product.

## Package verification

Manifest valid; all `data` files present; all XML parses cleanly; `ir.model.access.csv`
structurally consistent; LGPL-3 license matches the repository's own `LICENSE` file; no secret ever
committed (full git-history search); no unnecessary file in the actual git-tracked package (a stray
local `__pycache__` and one `.bak` file exist in the working tree only, both excluded by
`.gitignore`, not shipped in any archive built from this repository).

## Test results

**271 passed, 0 failed, 0 errors** — re-run against this exact release-preparation commit, on a
fresh database, confirming the documentation-only changes in this pass did not and could not affect
application behavior. This is the authoritative count (see
`docs/PRODUCTION_READINESS_REPORT.md` Section D for the full reconciliation of why it is 271, not
307). Fresh installation confirmed clean in this pass; the upgrade path was confirmed clean in
Phase H and not re-run here since no code changed.

## Release recommendation

**Conditional GO, now narrowed to exactly two remaining conditions, both already resolved as far as
this session can resolve them:**

1. ~~Correct the stale lot/serial documentation~~ — **done** in this pass (four project docs
   corrected; the live website's correction is prepared and ready to apply, but applying it needs
   deploy access this session doesn't have and wasn't asked to use).
2. Set the actual release version number — **a decision for whoever executes the release**, with
   `19.0.2.0.0` recommended.

No security or data-integrity issue was found or left unresolved at any point in this assessment or
this release-preparation pass. **This release is ready from an engineering standpoint.** The two
items above are process/content steps for whoever has publishing authority, not further engineering
work.

**Per this task's own explicit instruction: nothing has been pushed, merged, deployed, or published
to Odoo Apps. The website has not been modified. This report is a recommendation awaiting explicit
approval, not an action taken.**
