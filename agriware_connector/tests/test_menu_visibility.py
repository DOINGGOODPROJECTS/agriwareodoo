from odoo.tests.common import TransactionCase, tagged


@tagged("-at_install", "post_install")
class TestAgriwareMenuVisibility(TransactionCase):
    """Regression guard: the `groups` shortcut on <menuitem> only ever adds
    to group_ids on module upgrade, it never removes a previously-declared
    group. A menu that changes which group restricts it (or drops the
    restriction entirely) needs an explicit (6, 0, ...) override, or an
    existing, already-upgraded database keeps the old restriction forever
    alongside the new one -- silently hiding the menu from everyone who
    only has the new group. This was caught live on a long-lived dev
    database that still carried a stale base.group_system restriction from
    this module's very first release.
    """

    def test_root_menu_has_no_stale_group_restriction(self):
        menu = self.env.ref("agriware_connector.menu_agriware_root")
        self.assertFalse(
            menu.group_ids,
            "The root menu must stay unrestricted so visibility is "
            "controlled entirely by each child menu's own groups.",
        )

    def test_wms_connections_menu_is_restricted_to_technical_features_only(self):
        menu = self.env.ref("agriware_connector.menu_agriware_connections")
        self.assertEqual(
            menu.group_ids,
            self.env.ref("base.group_no_one"),
            "WMS Connections must be hidden from normal users (including "
            "plain System Administrators) and reachable only with "
            "Technical Features enabled.",
        )

    def test_api_management_menu_is_restricted_to_agriware_administrator(self):
        menu = self.env.ref("agriware_connector.menu_agriware_api_management")
        self.assertEqual(
            menu.group_ids,
            self.env.ref("agriware_connector.group_agriware_administrator"),
        )
