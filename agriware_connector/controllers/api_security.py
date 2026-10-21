# -*- coding: utf-8 -*-

from odoo.http import request


AGRIWARE_API_GROUP = (
    "agriware_connector.group_agriware_api_user"
)


def require_agriware_api_user():
    """
    Verify that the authenticated Odoo user
    belongs to the AgriWare API User security group.

    Returns:
        True if authorized.
        False if unauthorized.
    """

    user = request.env.user

    if not user or not user.id:
        return False

    return user.has_group(AGRIWARE_API_GROUP)
