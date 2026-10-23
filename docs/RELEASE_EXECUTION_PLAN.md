# Release Execution Plan — WMS-First AgriWare Connector (`19.0.2.0.0`)

**This document describes a proposed sequence. Nothing in it has been executed.** Every step below
requires explicit, separate approval before being carried out — this plan itself is not that
approval.

## Proposed release sequence

1. **Obtain final approval** from whoever has authority over this repository, the Odoo Apps
   Marketplace listing, and the live website — explicitly, for this specific release, not inferred
   from this report being produced.
2. **Back up relevant production systems** — the real Odoo database(s) this module is installed
   on in production, and the live website's current deployed state, so step 8's deployment (and any
   other step) can be rolled back cleanly if needed. Confirm the backup is restorable, not just
   taken.
3. **Merge approved changes** — `release/agriware-19.0-wms-first` into `19.0` (the Odoo-19-series
   branch this repository uses), via whatever review process this project normally requires (pull
   request, second reviewer, etc.). `main` is merged from `19.0` separately, per this repository's
   own existing convention (confirmed: `main` and `19.0` have tracked the same commit throughout
   this entire assessment).
4. **Push approved branches** to the remote.
5. **Create a Git tag** — proposed `v19.0.2.0.0`, on the merge commit on `19.0`, annotated with a
   message referencing this release's `CHANGELOG.md` entry.
6. **Publish a GitHub release** from that tag, with `docs/RELEASE_NOTES_WMS_FIRST.md`'s content (or
   a summary of it) as the release description, and the release ZIP
   (`agriware_connector-19.0.2.0.0.zip`, already built and checksummed in `release_artifacts/`)
   attached as a release asset.
7. **Upload the marketplace package** to the Odoo Apps Marketplace, using the same ZIP (or a
   marketplace-specific rebuild from the same tagged commit, if the marketplace pipeline requires
   its own packaging step — confirm this before relying on the ZIP in `release_artifacts/` directly).
8. **Deploy the corrected website copy** from `docs/WEBSITE_CONTENT_CORRECTIONS.md` — both English
   and French — through the website's own normal deployment process (this assessment has no access
   to perform this step itself).
9. **Verify the public installation** — install the newly-published marketplace package on a fresh
   Odoo 19 instance from the actual public listing (not a local file), confirming it matches the
   verification already performed in `docs/FINAL_RELEASE_VERIFICATION.md`.
10. **Verify public documentation** — confirm the GitHub release page, the marketplace listing's own
    description, and any linked docs render correctly and match what's actually shipped.
11. **Verify website functionality** — load the live pages after deployment, confirm the corrected
    copy is live, confirm the (deliberately disabled) contact form still renders its own
    "submission disabled" notice rather than silently appearing functional.
12. **Monitor for release issues** — watch for installation failures, API errors, or support
    requests in the period immediately following publication, using whatever support channel this
    project already has in place (see `docs/SUPPORT.md`).

## Rollback triggers

Any of the following should pause or reverse the sequence above, at whichever step it's discovered:

- A fresh installation of the **published** marketplace package fails, where this assessment's own
  local verification succeeded — indicates a packaging/upload discrepancy, not a code defect; do
  not attempt to patch it live, re-package and re-verify instead.
- A customer reports data loss, an unexpected stock change, or an inventory import being applied
  without human review — this would contradict this release's own core safety guarantee and should
  halt further rollout immediately pending investigation.
- A security report of any kind (credential exposure, cross-company data access beyond the
  documented, deliberate shared-product-catalog behavior, privilege escalation).
- The website deployment (step 8) introduces a claim that still doesn't match the shipped code —
  re-verify against `docs/FINAL_RELEASE_VERIFICATION.md` before publishing, not after.

## Rollback procedure

See `docs/RELEASE_NOTES_WMS_FIRST.md`... actually, see the dedicated rollback procedure in
`docs/FINAL_RELEASE_VERIFICATION.md`'s Rollback readiness section for the concrete steps (database
restore point, marketplace version revert, website revert) — not duplicated here to avoid two
documents drifting out of sync with each other.

## Explicitly not done by this plan or this assessment

Nothing above has been executed. No branch has been merged, no tag created, no package uploaded, no
website deployed. This document exists so that whoever does execute the release has a sequence to
follow and specific rollback triggers to watch for — not as a record of actions taken.
