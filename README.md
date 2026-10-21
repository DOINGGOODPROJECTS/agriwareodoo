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

| Module | Version | Repository |
|---|---|---|
| component | 19.0.1.0.1 | https://github.com/OCA/connector |
| component_event | 19.0.1.0.0 | https://github.com/OCA/connector |
| connector | 19.0.1.0.0 | https://github.com/OCA/connector |
| queue_job | 19.0.2.1.6 | https://github.com/OCA/queue |

These are the versions installed in the current development environment. Exact upstream Git revisions have not yet been pinned.

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

Download the required modules from the Odoo 19.0 branches of:

- https://github.com/OCA/connector
- https://github.com/OCA/queue

Place these four module directories in the project root:

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

## Authentication

Protected endpoints require an Odoo API key.

Include the API key in the HTTP Authorization header:

```text
Authorization: Bearer YOUR_API_KEY
```

The authenticated Odoo user must belong to the AgriWare API User security group or a group that implies it.

## Security

The current implementation includes:

- Bearer-token authentication
- AgriWare-specific API access permissions
- HTTP 401 responses for unauthenticated requests
- HTTP 403 responses for users without AgriWare API permissions
- Environment-based database credentials
- Git exclusions for credentials and database backups

Additional security hardening is required before production deployment.

## Project Status

AgriWare Connector is under active development.

Its initial REST API endpoints and security controls have been implemented and tested locally with Odoo 19.

## License

LGPL-3.0

## GitHub Repository

https://github.com/DOINGGOODPROJECTS/agriwareodoo
