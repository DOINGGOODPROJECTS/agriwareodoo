# Publication Package — AgriWare Connector `19.0.2.0.0`

**Everything in this document is prepared content, not executed action.** Nothing here has been
run against the real GitHub remote, the Odoo Apps Marketplace, or the live website. See
`docs/RELEASE_CHECKLIST.md` (Step 10's publication checklist) for exactly which of the actions
below require your explicit, separate approval before anyone carries them out.

## 1. Release commit and working tree

Verified: `release/agriware-19.0-wms-first` @ `030b7f7`, clean working tree, package
`agriware_connector-19.0.2.0.0.zip` (SHA-256 `e9aa1d3c29023442a5e19e87060298ffb48dfbeafa697f2f8ccf88aceaa5bd7f`)
confirmed to match this exact commit byte-for-byte (re-verified: no drift since Step 130).

## 2. GitHub remote and branch state

- Remote: `origin` → `git@github.com:DOINGGOODPROJECTS/agriwareodoo.git` (confirmed reachable via a
  read-only `git ls-remote` — no push attempted).
- `main` and `19.0` are, and have always been, **byte-for-byte identical histories** on this
  remote (confirmed via `git ls-remote` and a full local history diff) — both currently at
  `444b587`, matching this session's local record from the very first verification step onward.
  `19.0` appears to be the Odoo-series-named branch (likely what marketplace/CI tooling expects to
  find), kept as a mirror of `main` rather than a genuinely separate line of development.
- **Branch protection rules could not be verified from this session** — no `gh` CLI is installed,
  and querying GitHub's protection-rules API requires authenticated, repo-admin-scoped access this
  session doesn't have and wasn't asked to obtain. **Action needed from you (or whoever has GitHub
  admin access):** confirm directly in the repository's Settings → Branches whether `main`/`19.0`
  require a pull request, status checks, or specific reviewers before merging, so the procedure
  below can be adjusted if a direct merge isn't actually permitted.

## 3. Pull request / merge procedure (prepared, not executed)

Given `main` and `19.0` are identical and have moved together on every prior commit, the natural
procedure is to bring the release branch into both the same way:

**Option A — if direct merges are permitted (no required PR):**
```bash
git checkout 19.0
git merge --no-ff release/agriware-19.0-wms-first
git checkout main
git merge --no-ff 19.0   # fast-forwards, since 19.0 now leads main by the same commits
```

**Option B — if a pull request is required (likely, for a public-facing repo):**
```bash
git push -u origin release/agriware-19.0-wms-first
gh pr create --base 19.0 --head release/agriware-19.0-wms-first \
  --title "Release 19.0.2.0.0: WMS-first integration (Phases A-H)" \
  --body-file docs/RELEASE_NOTES_WMS_FIRST.md
# after that PR is reviewed and merged, open a second PR (or fast-forward) to bring main in sync:
gh pr create --base main --head 19.0 \
  --title "Sync main with 19.0 release 19.0.2.0.0"
```
(`gh` is not installed in this session's environment — these commands are written for whoever
executes this on a machine that has it, or as the equivalent through GitHub's own web UI.)

**Suggested PR description** (for either branch):
> Merges the WMS-first rearchitecture (Phases A–H): external ID mapping, product/warehouse/
> supplier/UOM synchronization, staged inventory import with mandatory human review, lot/serial
> synchronization, and WMS-first receipt/dispatch synchronization with transaction status
> retrieval. Full verification record: `docs/FINAL_RELEASE_VERIFICATION.md`. 271/271 tests passing.
> Backward compatible — the original numeric-ID receipt/dispatch schema is unchanged.

**Not done by this session:** the branch was not pushed, no PR was opened, nothing was merged.

## 4. Release ZIP and checksum — re-verified

| Property | Value |
|---|---|
| File | `release_artifacts/agriware_connector-19.0.2.0.0.zip` |
| SHA-256 | `e9aa1d3c29023442a5e19e87060298ffb48dfbeafa697f2f8ccf88aceaa5bd7f` |
| Matches commit | `030b7f7` (re-diffed `CHANGELOG.md` and the manifest version inside the zip against `git show HEAD:...` — identical) |
| Archive integrity | `unzip -t`: no errors |

**This ZIP is the GitHub-release artifact** (git-tracked source + docs only, per Step 130's own
instruction). **It is not the same artifact that should go to the Odoo Apps Marketplace** — see
Section 5.

## 5. Supplying the four OCA dependencies to marketplace users

**Already documented precisely in this repository's own `README.md`/`docs/INSTALLATION.md` — not
invented for this step, verified directly:**

| Module | Version | Source | Pinned commit | Commit confirmed to exist |
|---|---|---|---|---|
| component | 19.0.1.0.1 | https://github.com/OCA/connector | `cce76545ea56b85864fde9a1afb69748bc766e99` | ✅ (GitHub API, HTTP 200) |
| component_event | 19.0.1.0.0 | https://github.com/OCA/connector | `cce76545ea56b85864fde9a1afb69748bc766e99` | ✅ |
| connector | 19.0.1.0.0 | https://github.com/OCA/connector | `cce76545ea56b85864fde9a1afb69748bc766e99` | ✅ |
| queue_job | 19.0.2.1.6 | https://github.com/OCA/queue | `da2664795eb525698f93dfdd63f6ba5c4c9fccba` | ✅ (GitHub API, HTTP 200) |

**The marketplace package must be built separately from `release_artifacts/agriware_connector-19.0.2.0.0.zip`**,
by fetching these four pinned commits and bundling them alongside `agriware_connector/` — exactly
the procedure `README.md`'s own "Installing from source" section already documents for developers,
applied once at packaging time instead of by every end user:

```bash
mkdir -p /tmp/marketplace_build && cd /tmp/marketplace_build
cp -r /home/root8401/Desktop/OdooWarehouseIntegration/agriware_connector .

git clone https://github.com/OCA/connector.git oca-connector
git -C oca-connector checkout cce76545ea56b85864fde9a1afb69748bc766e99
cp -r oca-connector/component oca-connector/component_event oca-connector/connector .
rm -rf oca-connector

git clone https://github.com/OCA/queue.git oca-queue
git -C oca-queue checkout da2664795eb525698f93dfdd63f6ba5c4c9fccba
cp -r oca-queue/queue_job .
rm -rf oca-queue

zip -rq agriware_connector-19.0.2.0.0-marketplace.zip \
  agriware_connector component component_event connector queue_job
sha256sum agriware_connector-19.0.2.0.0-marketplace.zip
```

**This was not run in this session** (it clones from the public internet into a scratch location
outside the repository — a build step, not a verification one; Step 130 already independently
confirmed that installing `agriware_connector` alongside these exact four modules, sourced from the
project's existing local dev copies at the same versions, succeeds cleanly). Whoever executes the
actual marketplace upload should run this, then install-test the resulting
`-marketplace.zip` once more before uploading, exactly as Step 130 tested the GitHub-release zip.

## 6. GitHub release draft — `v19.0.2.0.0`

**Tag (proposed, not created):** `v19.0.2.0.0`, on the merge commit on `19.0` once merged.

**Release title:** `AgriWare Connector 19.0.2.0.0 — WMS-First Integration`

**Release body (draft):**
> This release turns AgriWare Connector from a read-only catalog + legacy-transaction API into a
> full WMS-first integration surface. See [`CHANGELOG.md`](CHANGELOG.md) for the complete history
> and [`docs/RELEASE_NOTES_WMS_FIRST.md`](docs/RELEASE_NOTES_WMS_FIRST.md) for the full feature and
> security summary.
>
> **Highlights:** product/warehouse/supplier/UOM synchronization, lot and serial number
> synchronization, staged initial inventory import (always human-reviewed, never auto-applied),
> and WMS-first receipt/dispatch synchronization with transaction status retrieval — all addressed
> by your own external IDs, all backward-compatible with the original numeric-ID schema.
>
> **Security:** the API-key isolation vulnerability present in earlier development history was
> found and fixed before this feature set shipped (dedicated per-key integration users) — see
> `docs/RELEASE_APPROVAL_REPORT.md`.
>
> **Verification:** 271/271 automated tests passing; fresh install and upgrade from the previously
> published `19.0.1.0.0` both independently verified using the exact release package — see
> `docs/FINAL_RELEASE_VERIFICATION.md` for the complete record.
>
> **Assets:** `agriware_connector-19.0.2.0.0.zip` (SHA-256:
> `e9aa1d3c29023442a5e19e87060298ffb48dfbeafa697f2f8ccf88aceaa5bd7f`)

**Not done by this session:** no tag created, no release published.

## 7. Odoo Apps Marketplace update (prepared, not uploaded)

- **Package to upload:** the marketplace-specific build from Section 5 (bundling the four pinned
  OCA modules), **not** the GitHub-release ZIP.
- **Version field:** `19.0.2.0.0`.
- **Listing description changes:** should match the corrected capability list in
  `docs/WEBSITE_CONTENT_CORRECTIONS.md` (product/warehouse/supplier/UOM/lot synchronization, staged
  inventory import, receipt/dispatch synchronization, transaction status retrieval) — the current
  published listing (version `19.0.1.0.0`) predates all of this and should not be left describing
  only the old read-only/legacy-transaction feature set once `19.0.2.0.0` is live.
- **Screenshots:** existing ones (`static/description/screenshot_*.png`) depict API key management,
  WMS connections, and API health — still accurate; none depict the new lot/inventory-import
  screens. Consider adding one or two new screenshots of the Inventory Imports review screen and
  the Lots list, though this isn't a blocker.
- **Changelog field (if the marketplace listing has one):** the `[19.0.2.0.0]` entry from
  `CHANGELOG.md`.
- **Not done by this session:** no package uploaded, no listing edited.

## 8. Website content deployment instructions (prepared, not deployed)

For whoever has deploy access to `agriware.agricarecentres.com`'s source (the local Next.js project
under `website/`):

1. Open `website/src/content/en.ts` and `website/src/content/fr.ts`.
2. Apply the exact replacements documented in `docs/WEBSITE_CONTENT_CORRECTIONS.md` — the
   `api.capabilities` list and `limitations.items` list in both files, plus the new paragraph about
   staged inventory import requiring human review.
3. Build and preview locally (`npm run build` inside `website/`, per that project's own
   `package.json` scripts) before deploying, to catch any formatting issue in the proposed copy.
4. Deploy through whatever process this project already uses for `website/out/` (a static export —
   confirmed present in this repository) — not something this session has access to or was asked
   to perform.
5. After deployment, verify live: the corrected capability list appears, the limitations list no
   longer claims lot/serial is unsupported, and the contact form still shows its own
   "submission disabled" notice (confirmed in Phase H: the form is deliberately, visibly disabled,
   not silently broken — this should not change as a side effect of the content edit).

**Not done by this session:** the website source was not modified, nothing was built or deployed.

## 9. Backup and rollback procedures — verified, not merely documented

**Backup tooling confirmed present and functional** in the actual Postgres container that would
host a production database (`pg_dump`/`pg_restore`/`pg_dumpall` all found at `/usr/bin/`, and a
real, read-only schema-only dump was successfully performed against the existing `agriwareodoo`
database in this session as a functional check — no data was read, modified, or at risk).

**Recommended backup command, immediately before any real upgrade:**
```bash
docker exec <db-container> pg_dump -U odoo -d <production-db> -Fc -f /tmp/pre_upgrade_backup.dump
docker cp <db-container>:/tmp/pre_upgrade_backup.dump ./backups/pre_19.0.2.0.0_$(date +%Y%m%d).dump
```

**Rollback, if the upgrade misbehaves:**
```bash
docker exec <db-container> dropdb -U odoo <production-db>
docker exec <db-container> createdb -U odoo <production-db>
docker cp ./backups/pre_19.0.2.0.0_<date>.dump <db-container>:/tmp/restore.dump
docker exec <db-container> pg_restore -U odoo -d <production-db> -c /tmp/restore.dump
```
(Verified these are the correct, standard tool invocations for this project's own Postgres 16
container — not run against production in this session, and not run at all beyond the read-only
functional check above.)

**Marketplace rollback:** Odoo Apps Marketplace supports reverting a listing to a prior published
version through the seller dashboard — outside this session's access, not tested here.

**Website rollback:** redeploying the prior content through the website's own deployment/version
history — outside this session's access, not tested here.

**Code rollback:** since nothing is merged yet, "rollback" at this stage is simply not merging; once
merged, it's reverting the merge commit on `19.0`/`main`.
