from odoo.exceptions import AccessError, ValidationError
from odoo.tests.common import tagged

from .common import AgriwareApiCommon


@tagged("-at_install", "post_install")
class TestAgriwareExternalSystems(AgriwareApiCommon):
    """agriware.external.system: creation, uniqueness, and access control."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.other_company = cls.env["res.company"].create({
            "name": "AgriWare Test Other Company",
        })

        internal_group = cls.env.ref("base.group_user")
        admin_group = cls.env.ref(
            "agriware_connector.group_agriware_administrator"
        )

        cls.other_admin_user = cls.env["res.users"].create({
            "name": "AgriWare Other Company Admin",
            "login": "agriware_other_admin_test_user",
            "group_ids": [(6, 0, [internal_group.id, admin_group.id])],
            "company_ids": [(6, 0, [cls.other_company.id])],
            "company_id": cls.other_company.id,
        })

    def test_create_external_system(self):
        system = self.env["agriware.external.system"].with_user(
            self.admin_user
        ).create({
            "name": "Main Warehouse WMS",
            "code": "primary_wms",
            "company_id": self.env.company.id,
        })

        self.assertTrue(system.active)
        self.assertEqual(system.company_id, self.env.company)

    def test_duplicate_code_same_company_rejected(self):
        Model = self.env["agriware.external.system"].with_user(self.admin_user)
        Model.create({
            "name": "Main Warehouse WMS",
            "code": "primary_wms",
            "company_id": self.env.company.id,
        })

        with self.assertRaises(Exception):
            with self.env.cr.savepoint():
                Model.create({
                    "name": "Duplicate Code System",
                    "code": "primary_wms",
                    "company_id": self.env.company.id,
                })

    def test_same_code_different_company_allowed(self):
        Model = self.env["agriware.external.system"].sudo()

        system_a = Model.create({
            "name": "Company A WMS",
            "code": "primary_wms",
            "company_id": self.env.company.id,
        })
        system_b = Model.create({
            "name": "Company B WMS",
            "code": "primary_wms",
            "company_id": self.other_company.id,
        })

        self.assertNotEqual(system_a.id, system_b.id)
        self.assertEqual(system_a.code, system_b.code)

    def test_empty_code_rejected(self):
        with self.assertRaises(ValidationError):
            self.env["agriware.external.system"].with_user(
                self.admin_user
            ).create({
                "name": "No Code System",
                "code": "   ",
                "company_id": self.env.company.id,
            })

    def test_cross_company_rule_isolation(self):
        system_a = self.env["agriware.external.system"].sudo().create({
            "name": "Company A WMS",
            "code": "primary_wms",
            "company_id": self.env.company.id,
        })

        visible_to_other = self.env["agriware.external.system"].with_user(
            self.other_admin_user
        ).search([("id", "=", system_a.id)])

        self.assertFalse(visible_to_other)

    def test_plain_user_cannot_create_external_system(self):
        with self.assertRaises(AccessError):
            self.env["agriware.external.system"].with_user(
                self.plain_user
            ).create({
                "name": "Unauthorized System",
                "code": "unauthorized",
                "company_id": self.env.company.id,
            })

    def test_api_user_cannot_create_external_system(self):
        # AgriWare API User can call the mapping SERVICE (which sudo()s
        # internally after its own checks), but has no direct ir.model.access
        # grant on agriware.external.system -- only Administrators manage
        # external systems directly.
        with self.assertRaises(AccessError):
            self.env["agriware.external.system"].with_user(
                self.api_user
            ).create({
                "name": "Unauthorized System",
                "code": "unauthorized",
                "company_id": self.env.company.id,
            })
