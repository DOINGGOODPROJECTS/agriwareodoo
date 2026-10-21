{
    "name": "AgriWare Connector",
    "version": "19.0.1.0.0",
    "summary": "Connect Odoo with AgriWare Warehouse Management",
    "description": """
AgriWare — Open-Source Warehouse Management for Agribusinesses.

This module integrates an existing AgriWare installation
with Odoo ERP.

AgriWare remains a standalone application.
The connector enables communication and data synchronization
between AgriWare and Odoo.
    """,
    "category": "Inventory/Inventory",
    "author": "AgriWare",
    "license": "LGPL-3",
    "depends": [
        "base",
        "connector",
        "stock",
    ],

    "data": [
        "security/agriware_security.xml",
        "security/ir.model.access.csv",
        "views/connection_views.xml",
    ],
    "installable": True,
    "application": False,
    "auto_install": False,
}
