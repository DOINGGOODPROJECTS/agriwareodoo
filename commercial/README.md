# Commercial tracking

This directory holds working commercial materials — not published documentation, and not part of
the application. `LEAD_TRACKER.csv` is a **blank template**; no customer records exist yet, and
none should be invented. Rows are added only as real leads materialize.

## Lead status workflow

Use these values in the `Lead status` column, in order:

1. **NEW** — identified or inbound, not yet contacted.
2. **CONTACTED** — an initial outreach message has been sent.
3. **DISCOVERY** — a discovery conversation is scheduled or in progress (see the questionnaire in
   [`docs/INTEGRATION_SERVICES.md`](../docs/INTEGRATION_SERVICES.md#customer-requirements-questionnaire)
   or its French equivalent in
   [`docs/PROSPECTION_CLIENTS_FR.md`](../docs/PROSPECTION_CLIENTS_FR.md#d-questionnaire-de-découverte-client)).
4. **QUALIFIED** — discovery is complete and the lead matches a real, assessable need (not every
   contacted company will reach this stage).
5. **PROPOSAL** — a scoped proposal (service package + indicative price) has been sent.
6. **NEGOTIATION** — the prospect is actively discussing scope or price.
7. **WON** — a paid engagement has been signed.
8. **LOST** — the lead did not convert; note why in the `Notes` column so patterns can be reviewed
   later.

## Column notes

- **Estimated project value (FCFA)** — a planning estimate at the PROPOSAL stage or later; leave
  blank before that, since estimating before discovery is guessing.
- **Existing ERP / Existing WMS** — record exactly what the prospect reports; don't assume
  Odoo-compatibility or REST-API compatibility from the name alone.
- **Integration requirements** — a short free-text summary from the discovery questionnaire, not
  the full questionnaire (keep the full answers wherever the discovery conversation was recorded).

See [`docs/COMMERCIAL_STRATEGY.md`](../docs/COMMERCIAL_STRATEGY.md) section 7 for how this tracker
fits into the overall sales funnel.
