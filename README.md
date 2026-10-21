# AgriWare Connector

AgriWare Connector is an open-source Odoo 19 module that enables agricultural warehouse management systems (WMS) to exchange information with Odoo through a standardized REST API.

The project is designed for agribusinesses, particularly those operating in Côte d'Ivoire and other African markets.

## Features

- REST API integration with Odoo 19
- Product information retrieval
- Warehouse information retrieval
- Inventory and stock visibility
- Stock receipt creation and validation
- Stock dispatch creation and validation
- API key authentication
- Role-based API access control
- Self-service API key management (generate, name, set an expiration or make
  permanent, view status, and revoke keys directly from the AgriWare
  Connector menu, without needing Odoo System Administrator access)

## Architecture

External warehouse management systems communicate with AgriWare Connector through its REST API.

```text
External Warehouse Management Systems
                |
                | REST API
                v
        AgriWare Connector
                |
                | Odoo ORM
                v
             Odoo 19
                |
                v
            PostgreSQL
```

## Requirements

- Odoo 19
- PostgreSQL 16
- Docker and Docker Compose
- Python packages: openupgradelib and cachetools

### OCA Dependencies

AgriWare Connector uses the following Odoo Community Association modules:

| Module | Version | Repository | Pinned commit |
|---|---|---|---|
| component | 19.0.1.0.1 | https://github.com/OCA/connector | `cce76545ea56b85864fde9a1afb69748bc766e99` |
| component_event | 19.0.1.0.0 | https://github.com/OCA/connector | `cce76545ea56b85864fde9a1afb69748bc766e99` |
| connector | 19.0.1.0.0 | https://github.com/OCA/connector | `cce76545ea56b85864fde9a1afb69748bc766e99` |
| queue_job | 19.0.2.1.6 | https://github.com/OCA/queue | `da2664795eb525698f93dfdd63f6ba5c4c9fccba` |

These are the exact Git revisions verified against the files installed in the current development environment (byte-for-byte identical). Use the pinned commits below rather than tracking the `19.0` branch directly, since upstream can advance independently of this project.

## Installation

### 1. Clone the Repository

```bash
git clone git@github.com:DOINGGOODPROJECTS/agriwareodoo.git
cd agriwareodoo
```

### 2. Configure Environment Variables

```bash
cp .env.example .env
nano .env
```

Replace the placeholder password with your own PostgreSQL password.

### 3. Install OCA Dependencies

Clone the upstream repositories and check out the pinned commits listed above, then copy only the needed module directories into the project root:

```bash
git clone https://github.com/OCA/connector.git /tmp/oca-connector
git -C /tmp/oca-connector checkout cce76545ea56b85864fde9a1afb69748bc766e99
cp -r /tmp/oca-connector/component ./component
cp -r /tmp/oca-connector/component_event ./component_event
cp -r /tmp/oca-connector/connector ./connector

git clone https://github.com/OCA/queue.git /tmp/oca-queue
git -C /tmp/oca-queue checkout da2664795eb525698f93dfdd63f6ba5c4c9fccba
cp -r /tmp/oca-queue/queue_job ./queue_job

rm -rf /tmp/oca-connector /tmp/oca-queue
```

This results in the following module directories at the project root (all excluded from version control by `.gitignore`, since they are third-party dependencies, not part of this project):

```text
component/
component_event/
connector/
queue_job/
```

### 4. Start Odoo

```bash
docker compose up -d --build
```

Open Odoo at:

http://localhost:8069

### 5. Install AgriWare Connector

1. Log in to Odoo.
2. Activate developer mode.
3. Navigate to Apps.
4. Update the Apps List.
5. Search for AgriWare Connector.
6. Install the module.

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/agriware/api/v1/health` | API health check |
| GET | `/agriware/api/v1/products` | Retrieve products |
| GET | `/agriware/api/v1/warehouses` | Retrieve warehouses |
| GET | `/agriware/api/v1/inventory` | Retrieve inventory |
| POST | `/agriware/api/v1/receipts` | Create stock receipt |
| POST | `/agriware/api/v1/receipts/{id}/validate` | Validate receipt |
| POST | `/agriware/api/v1/dispatches` | Create stock dispatch |
| POST | `/agriware/api/v1/dispatches/{id}/validate` | Validate dispatch |

Full request/response schemas, authentication details, and error responses for every endpoint
are documented in [docs/API.md](docs/API.md).

## Authentication

Protected endpoints require an Odoo API key.

Include the API key in the HTTP Authorization header:

```text
Authorization: Bearer YOUR_API_KEY
```

The authenticated Odoo user must belong to the AgriWare API User security group or a group that implies it.

### Generating a key

Any user in the **AgriWare Administrator** group can generate and manage API keys directly,
without needing Odoo System Administrator access:

1. Go to **AgriWare Connector → API Management → Generate API Key**.
2. Enter an integration name (e.g. "Main Warehouse Integration").
3. Choose an expiration date, or check **Never Expires**.
4. Click **Generate**. The key is shown once — copy it immediately; it cannot be retrieved again.

Manage existing keys under **AgriWare Connector → API Management → API Keys**: view creation
date, expiration, and status (Active / Expired / Revoked), and revoke a key at any time. A
revoked or expired key stops authenticating immediately. See [docs/API.md](docs/API.md) for the
full design and security model behind this.

## Security

The current implementation includes:

- Bearer-token authentication
- AgriWare-specific API access permissions
- HTTP 401 responses for unauthenticated requests
- HTTP 403 responses for users without AgriWare API permissions
- Company-scoped lookups for warehouses, partners, and products
- Transaction-scoped advisory locking to prevent duplicate receipts/dispatches from concurrent requests with the same external reference
- Reference-prefix scoping (`AGRIWARE-RCPT-` / `AGRIWARE-DISP-`) so the validate endpoints cannot confirm stock operations that were not created by AgriWare
- Self-service API key management restricted to the AgriWare Administrator group, with per-company record rules so one company can never view or revoke another company's keys
- API keys are never stored or displayed in plaintext after creation (only a salted hash is kept, matching Odoo's own API key storage); revoked and expired keys are rejected at authentication time, enforced by Odoo core, not by this module
- Environment-based database credentials
- Git exclusions for credentials and database backups

See [docs/API.md](docs/API.md#known-limitations) for known limitations (no per-warehouse access
control, no pagination, no partial receipts/dispatches). Additional security hardening is
required before production deployment.

## Project Status

AgriWare Connector is under active development.

Its initial REST API endpoints and security controls have been implemented and tested locally with Odoo 19.

## License

LGPL-3.0

## GitHub Repository

https://github.com/DOINGGOODPROJECTS/agriwareodoo
