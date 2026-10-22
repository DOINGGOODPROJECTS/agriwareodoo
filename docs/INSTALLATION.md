# Installation Guide

This guide is for a business that wants to connect its existing Warehouse Management System (WMS)
to Odoo 19 using AgriWare Connector. It assumes **no prior Odoo development experience** — only
that you (or someone at your organization) has administrator access to your Odoo 19 instance.

If you only need the short version, see [QUICK_START.md](QUICK_START.md). For the full REST API
reference, see [API.md](API.md). For the integration narrative aimed at the developer configuring
your WMS side, see [WMS_INTEGRATION.md](WMS_INTEGRATION.md).

## Before you start: how is your Odoo hosted?

AgriWare Connector depends on four Odoo Community Association (OCA) modules (`component`,
`component_event`, `connector`, `queue_job`) that are not part of standard Odoo. How you get those
onto your instance depends on your hosting:

| Hosting | Can you install third-party modules with external dependencies? |
|---|---|
| Self-hosted / on-premise Odoo 19 | Yes — you (or your IT provider) have full access to the server's addons path. |
| Odoo.sh | Yes — modules are added to your Odoo.sh branch's repository, typically by a developer. |
| Odoo Online (odoo.com SaaS) | Usually restricted — Odoo Online does not generally allow arbitrary third-party modules with external dependencies to be uploaded by the customer. Check with Odoo support or your Odoo partner before assuming this will work. |

If you're not sure which applies to you, or you don't have anyone technical on hand to install the
OCA dependencies, see [Free software and paid services](../README.md#free-software-and-paid-services)
for optional paid installation help.

The remaining steps assume a self-hosted or Odoo.sh environment where a technical contact can place
files on the server. If that isn't you, forward this guide to whoever manages your Odoo hosting.

## 1. Download AgriWare Connector from Odoo Apps

Open the marketplace listing:

<https://apps.odoo.com/apps/modules/19.0/agriware_connector>

- On a self-hosted instance, use the **Download** option on that page to get the module as a zip
  file, then extract it into your Odoo addons directory (the folder your `odoo.conf`'s
  `addons_path` already includes, or a new folder you add to it).
- On Odoo.sh, add the module to your branch's repository under its custom-addons path, following
  your Odoo.sh project's normal deployment process.

Do **not** install it yet — the OCA dependencies below must be in place first, or Odoo will refuse
to install AgriWare Connector with a missing-dependency error.

## 2. Install the required OCA dependencies

Place these four modules in the same addons path as AgriWare Connector, at the exact pinned
commits below (not the latest `19.0` branch — upstream can change independently of this project):

| Module | Version | Repository | Pinned commit |
|---|---|---|---|
| component | 19.0.1.0.1 | https://github.com/OCA/connector | `cce76545ea56b85864fde9a1afb69748bc766e99` |
| component_event | 19.0.1.0.0 | https://github.com/OCA/connector | `cce76545ea56b85864fde9a1afb69748bc766e99` |
| connector | 19.0.1.0.0 | https://github.com/OCA/connector | `cce76545ea56b85864fde9a1afb69748bc766e99` |
| queue_job | 19.0.2.1.6 | https://github.com/OCA/queue | `da2664795eb525698f93dfdd63f6ba5c4c9fccba` |

For a technical contact, the commands are:

```bash
git clone https://github.com/OCA/connector.git /tmp/oca-connector
git -C /tmp/oca-connector checkout cce76545ea56b85864fde9a1afb69748bc766e99
cp -r /tmp/oca-connector/component /path/to/your/addons/
cp -r /tmp/oca-connector/component_event /path/to/your/addons/
cp -r /tmp/oca-connector/connector /path/to/your/addons/

git clone https://github.com/OCA/queue.git /tmp/oca-queue
git -C /tmp/oca-queue checkout da2664795eb525698f93dfdd63f6ba5c4c9fccba
cp -r /tmp/oca-queue/queue_job /path/to/your/addons/

rm -rf /tmp/oca-connector /tmp/oca-queue
```

Restart the Odoo service after copying these in, so Odoo picks up the new addons path contents.

## 3. Install AgriWare Connector in Odoo 19

1. Log in to Odoo as an administrator.
2. Enable developer mode (**Settings → General Settings**, scroll to the bottom, **Activate the
   developer mode**).
3. Go to the **Apps** menu.
4. Click **Update Apps List** (top-left), then **Update**.
5. Search for **AgriWare Connector**.
6. Click **Install**. Odoo installs AgriWare Connector together with `component`,
   `component_event`, `connector`, and `queue_job` in one step.

If the module does not appear in the search results, the files were not placed in a path Odoo
scans, or the service was not restarted after step 2 — recheck those before continuing.

## 4. Assign the appropriate user permissions

Installing the module does **not** by itself give anyone access to it. An administrator with
Odoo's own **Settings** access must grant the right group to the right people:

1. Go to **Settings → Users & Companies → Users**.
2. Open the user who should manage API keys (commonly, you — the business owner or IT contact).
3. Under **Access Rights**, find **AgriWare Connector** and set it to **Administrator**.
4. Click **Save**.

This grants the **AgriWare Administrator** group, which is required to generate, revoke, or replace
API keys. (The separate **AgriWare API User** group is assigned automatically to a dedicated
integration account the first time you generate a key — see step 6 — you do not assign it to a
human yourself.)

## 5. Open API Management

In the main Odoo app switcher (top-left, the grid icon, or the app menu bar), open
**AgriWare Connector → API Management**. You should see two entries:

- **API Keys** — the list of keys you've generated, with their status.
- **Generate API Key** — the form to create a new one.

If you don't see **AgriWare Connector** in your app list at all, your user is missing the
Administrator access right from step 4.

## 6. Generate an API key

1. Go to **AgriWare Connector → API Management → Generate API Key**.
2. Enter an **Integration Name** that identifies this connection (e.g. "Main Warehouse WMS").
3. If you work with more than one company in this Odoo database, choose the **Company** this key
   belongs to.
4. Continue to step 7 to set when the key expires.

## 7. Select an expiration date or Never Expires

- To set an expiration date: leave **Never Expires** unchecked, and fill in **Expiration Date**
  with a date in the future.
- To create a key that never expires on its own: check **Never Expires**.

A date-based key stops authenticating automatically once that date passes. A **Never Expires** key
remains valid until you explicitly revoke it. Prefer an expiration date unless your integration
genuinely needs a long-lived credential.

Click **Generate**.

## 8. Copy the generated API key

Odoo immediately shows the raw key in an **API Key Ready** dialog. **Copy it now and store it in
your WMS's secret/credential storage.** This is the only time the raw key is ever shown — Odoo
stores only a salted hash afterward, and the key cannot be retrieved again. If you lose it, revoke
it from the **API Keys** list and generate a replacement.

## 9. Configure your existing WMS

In your WMS's integration settings, enter:

- **API base URL** — your Odoo instance's address followed by `/agriware/api/v1`, for example
  `https://your-odoo-instance.example.com/agriware/api/v1`.
- **API key** — the value you copied in step 8.
- **Authentication method** — Bearer token: every request must carry an
  `Authorization: Bearer <your-api-key>` header.

How you enter these two values depends entirely on your WMS's own settings screen — this part is
specific to your WMS software. See [WMS_INTEGRATION.md](WMS_INTEGRATION.md) for what your WMS (or
its developer) needs to implement on its side.

## 10. Test the connection using the REST API

With a terminal (or your WMS's "test connection" feature, if it has one), check the health
endpoint first — it needs no API key:

```bash
curl -s https://your-odoo-instance.example.com/agriware/api/v1/health
```

Expected response:

```json
{"status": "success", "service": "AgriWare Connector", "api_version": "1.0", "message": "AgriWare API is running"}
```

Then confirm your API key works against a real, protected endpoint:

```bash
curl -s https://your-odoo-instance.example.com/agriware/api/v1/products \
  -H "Authorization: Bearer YOUR_API_KEY"
```

A successful response looks like:

```json
{"status": "success", "count": 2, "products": [ ... ]}
```

If you instead get a `401 Unauthorized` HTML page, the Bearer token is missing, mistyped, expired,
or revoked. If you get `{"status": "error", "message": "Access denied: AgriWare API User role
required"}`, the key's underlying integration user is missing the required group — this should not
happen with a key generated through the wizard in step 6, so contact support if it does.

## Troubleshooting

| Symptom | Likely cause |
|---|---|
| AgriWare Connector doesn't appear after Update Apps List | The OCA dependency modules aren't in the addons path, or Odoo wasn't restarted after adding them. |
| Install fails citing a missing dependency | One of `component`, `component_event`, `connector`, `queue_job` is missing or at the wrong version. |
| **AgriWare Connector** menu is missing after install | Your user doesn't have the AgriWare Administrator access right (step 4). |
| `401 Unauthorized` (HTML, not JSON) | Bad, missing, expired, or revoked API key. |
| `403` JSON error | Authenticated, but the key's integration user lacks the AgriWare API User group — shouldn't occur with wizard-generated keys. |

## Getting help

AgriWare Connector itself is free and open-source — see
[Free software and paid services](../README.md#free-software-and-paid-services) for what's
included at no cost, and what optional paid services (custom WMS integration, installation help,
support) are available. The project's GitHub Issues page is the current contact channel:

<https://github.com/DOINGGOODPROJECTS/agriwareodoo/issues>
