# Website Content Corrections — Proposed Copy (Not Deployed)

**This document proposes corrected English and French copy for the AgriWare Connector marketing
website (`agriware.agricarecentres.com`, English at `/en/`). The live website and its local source
(`website/src/content/en.ts`, `website/src/content/fr.ts`) have NOT been modified — per this task's
own explicit instruction, this document is the deliverable, not a change to the website itself.**
A maintainer with access to deploy the website should apply the replacements below, verify them
against a staging build, and publish through the website's own normal process.

## Source of the problem, traced precisely

The stale claims on the website trace back to `docs/COMMERCIAL_STRATEGY.md`'s own "Do not
advertise... lot/serial support... none of these exist yet" instruction — written before Phase F
shipped lot/serial synchronization, and never updated afterward. That instruction has been
corrected in this same release-preparation pass (see `docs/COMMERCIAL_STRATEGY.md`). The website
copy below was evidently written following that now-corrected instruction and needs the same fix.

## What's actually implemented, verified against source (not assumed)

Checked directly against the current codebase and the Phase H production-readiness assessment:

| Capability | Status |
|---|---|
| Product synchronization | Implemented — `POST`/`PATCH /products`, `GET /products` |
| Warehouse synchronization | Implemented — `POST`/`PATCH /warehouses`, `GET /warehouses` |
| Supplier synchronization | Implemented — `POST`/`PATCH /suppliers`, `GET /suppliers` |
| Unit-of-measure mapping | Implemented — admin-configurable `agriware.uom.mapping`, layered over a small hardcoded kg/g/ton/liter/unit set |
| Lot and serial synchronization | Implemented — `POST`/`GET`/`PATCH /lots`, plus lot-aware receipts/dispatches/inventory import |
| Initial inventory import staging | Implemented — `POST /inventory-adjustments`; **staged only, human-reviewed, never auto-applied** |
| Receipt synchronization | Implemented — legacy numeric-ID schema (unchanged) plus a WMS-first external-ID schema |
| Dispatch synchronization | Implemented — same two schemas |
| Transaction status retrieval | Implemented — `GET /receipts/{external_reference}`, `GET /dispatches/{external_reference}` |

**Still genuinely not implemented** (safe to keep advertising as absent): pagination on list
endpoints, per-warehouse access control within a company, partial receipts/dispatches, scheduled/
automatic synchronization, bidirectional synchronization (Odoo never calls the WMS), built-in
WMS-specific adapters.

## English corrections

### `api.capabilities` (currently lines 85–86 of `en.ts`, under the broader `capabilities` list)

**Current:**
```
"Read product, warehouse, and inventory data",
"Incoming receipts — create and validate",
"Outgoing dispatches — create and validate",
```

**Proposed:**
```
"Read product, warehouse, and inventory data",
"Create and update products, warehouses, and suppliers, addressed by your own external IDs",
"Configure unit-of-measure mappings for units Odoo doesn't ship with by default",
"Create and resolve lots and serial numbers for traceable products",
"Stage initial inventory observations for human review — never applied automatically",
"Incoming receipts — create and validate, including lot/serial-tracked products",
"Outgoing dispatches — create and validate, including lot/serial-tracked products",
"Look up the status of a receipt or dispatch by your own external reference",
```

### `limitations.items` (lines 169–175)

**Current:**
```
"No pagination on the products, warehouses, or inventory list endpoints (capped at 100 records)",
"No per-warehouse access control within a company",
"Partial receipts and partial dispatches are not supported — quantities must match exactly",
"Lot/serial-tracked products are not supported",
"No automatic or scheduled synchronization — every request is initiated by the external WMS",
"No built-in, WMS-specific adapters — this is one generic REST API",
```

**Proposed:**
```
"No pagination on the products, warehouses, or inventory list endpoints (capped at 100 records)",
"No per-warehouse access control within a company",
"Partial receipts and partial dispatches are not supported — quantities must match exactly",
"Initial inventory imports are staged for human review — applying a reviewed count to actual Odoo
 stock still requires one manual step in Odoo's own Inventory Adjustment screen, by design",
"No automatic or scheduled synchronization — every request is initiated by the external WMS",
"No built-in, WMS-specific adapters — this is one generic REST API",
```

(The lot/serial line is removed from "limitations" entirely — it belongs in "capabilities" now.)

### A new, short section making the inventory-import safety model explicit

The current page doesn't explain *how* inventory import works at all (it isn't mentioned in any
capability or limitation line beyond "inventory data"). Given this task's explicit instruction to
state the human-review requirement clearly, propose adding one short paragraph wherever the page
currently introduces receipts/dispatches:

**Proposed new paragraph:**
> "Initial stock counts from your WMS are staged in Odoo for review, not applied automatically. An
> Inventory Manager compares the WMS's count against Odoo's own records and decides what to do —
> applying an approved count to actual stock is a separate, manual action in Odoo's native
> Inventory Adjustment screen. This keeps a human in the loop for every change to your real
> inventory levels."

## French corrections (`fr.ts`)

### `api.capabilities` (lines 146–151)

**Current:**
```
"GET /health — contrôle de santé public, aucune authentification requise",
"GET /products — récupération de jusqu'à 100 produits",
"GET /warehouses — récupération des entrepôts",
"GET /inventory — récupération des quantités de stock disponibles",
"POST /receipts et /receipts/{id}/validate — création et validation des réceptions entrantes",
"POST /dispatches et /dispatches/{id}/validate — création et validation des expéditions sortantes",
```

**Proposed:**
```
"GET /health — contrôle de santé public, aucune authentification requise",
"GET /products — récupération de jusqu'à 100 produits",
"GET /warehouses — récupération des entrepôts",
"GET /inventory — récupération des quantités de stock disponibles",
"Création et mise à jour des produits, entrepôts et fournisseurs, identifiés par vos propres
 identifiants externes",
"Configuration des correspondances d'unités de mesure pour les unités non fournies par défaut
 dans Odoo",
"Création et résolution des lots et numéros de série pour les produits traçables",
"Mise en attente des observations d'inventaire initial pour révision humaine — jamais appliquées
 automatiquement",
"POST /receipts et /receipts/{id}/validate — création et validation des réceptions entrantes, y
 compris pour les produits suivis par lot ou numéro de série",
"POST /dispatches et /dispatches/{id}/validate — création et validation des expéditions
 sortantes, y compris pour les produits suivis par lot ou numéro de série",
"Consultation du statut d'une réception ou d'une expédition par votre propre référence externe",
```

### `limitations.items` (lines 169–175)

**Current:**
```
"Pas de pagination sur les endpoints produits, entrepôts ou inventaire (plafonnés à 100 enregistrements)",
"Pas de contrôle d'accès par entrepôt au sein d'une même entreprise",
"Les réceptions et expéditions partielles ne sont pas prises en charge — les quantités doivent correspondre exactement",
"Les produits suivis par lot ou numéro de série ne sont pas pris en charge",
"Aucune synchronisation automatique ou planifiée — chaque requête est initiée par le WMS externe",
"Pas d'adaptateurs intégrés spécifiques à un WMS — il s'agit d'une seule API REST générique",
```

**Proposed:**
```
"Pas de pagination sur les endpoints produits, entrepôts ou inventaire (plafonnés à 100
 enregistrements)",
"Pas de contrôle d'accès par entrepôt au sein d'une même entreprise",
"Les réceptions et expéditions partielles ne sont pas prises en charge — les quantités doivent
 correspondre exactement",
"Les imports d'inventaire initial sont mis en attente pour révision humaine — l'application d'un
 comptage validé au stock réel Odoo nécessite toujours une étape manuelle dans l'écran natif
 d'ajustement d'inventaire d'Odoo, par conception",
"Aucune synchronisation automatique ou planifiée — chaque requête est initiée par le WMS externe",
"Pas d'adaptateurs intégrés spécifiques à un WMS — il s'agit d'une seule API REST générique",
```

**Proposed new paragraph (French), matching the English one above:**
> « Les comptages de stock initiaux provenant de votre WMS sont mis en attente dans Odoo pour
> révision, et non appliqués automatiquement. Un responsable d'inventaire compare le comptage du
> WMS aux données d'Odoo et décide de la suite à donner — l'application d'un comptage approuvé au
> stock réel reste une action manuelle distincte, effectuée dans l'écran natif d'ajustement
> d'inventaire d'Odoo. Un humain reste ainsi impliqué dans chaque changement apporté à vos niveaux
> de stock réels. »

## Verification note

Every "implemented" claim above was checked directly against this phase's own test suite and the
Phase H production-readiness assessment's real-HTTP verification, not asserted from memory. Nothing
proposed here claims a capability beyond what Sections C and E of
[PRODUCTION_READINESS_REPORT.md](PRODUCTION_READINESS_REPORT.md) already confirmed.
