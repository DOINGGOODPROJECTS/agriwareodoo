from odoo import api, fields, models, _
from odoo.exceptions import AccessError


class AgriwareApiKey(models.Model):
    _name = "agriware.api.key"
    _description = "AgriWare API Key"
    _order = "create_date desc"

    name = fields.Char(
        string="Integration Name",
        required=True,
        help="A label for the WMS integration this key is used by, "
             "e.g. 'Main Warehouse Integration'.",
    )

    company_id = fields.Many2one(
        "res.company",
        string="Company",
        required=True,
        default=lambda self: self.env.company,
    )

    integration_user_id = fields.Many2one(
        "res.users",
        string="Integration Identity",
        readonly=True,
        help="The dedicated, password-less Odoo user this key authenticates "
             "as when calling the AgriWare REST API.",
    )

    apikey_id = fields.Many2one(
        "res.users.apikeys",
        string="API Key Record",
        ondelete="set null",
        readonly=True,
        copy=False,
    )

    expiration_date = fields.Datetime(
        string="Expiration Date",
        readonly=True,
    )

    never_expires = fields.Boolean(
        string="Never Expires",
        readonly=True,
    )

    revoked_date = fields.Datetime(
        string="Revoked On",
        readonly=True,
        copy=False,
    )

    state = fields.Selection(
        [
            ("active", "Active"),
            ("expired", "Expired"),
            ("revoked", "Revoked"),
        ],
        string="Status",
        compute="_compute_state",
        # Deliberately not stored: "expired" depends on the current time,
        # not just on this record's own fields, so a stored value would
        # stay "Active" forever past expiration until something happened
        # to write to the record and trigger a recompute. Computing fresh
        # on every read keeps the displayed status honest.
    )

    @api.depends("apikey_id", "expiration_date", "revoked_date")
    def _compute_state(self):
        now = fields.Datetime.now()

        for record in self:
            if record.revoked_date or not record.apikey_id:
                record.state = "revoked"
            elif record.expiration_date and record.expiration_date <= now:
                record.state = "expired"
            else:
                record.state = "active"

    def _check_can_manage(self, company=None):
        """Raise unless the current user is an AgriWare Administrator for
        ``company`` (or, called on a recordset, for every record's
        company)."""
        admin_group = self.env.ref(
            "agriware_connector.group_agriware_administrator"
        )

        if admin_group not in self.env.user.all_group_ids:
            raise AccessError(_(
                "Only AgriWare Administrators can manage API keys."
            ))

        companies = [company] if company is not None else self.mapped("company_id")

        for record_company in companies:
            if record_company not in self.env.user.company_ids:
                raise AccessError(_(
                    "You do not have access to API keys for this company."
                ))

    @api.model
    def _get_or_create_integration_user(self, company):
        """Return the dedicated, password-less Odoo user that AgriWare API
        keys for ``company`` authenticate as, creating it on first use.

        This user is never given a usable password and no invitation email
        is sent, so it cannot log in interactively. It exists purely so
        Bearer API keys have an identity to attach to, matching Odoo's own
        design (``res.users.apikeys`` rows always belong to a user).
        """
        xml_id = f"integration_user_company_{company.id}"
        full_xml_id = f"agriware_connector.{xml_id}"

        user = self.env.ref(full_xml_id, raise_if_not_found=False)

        if user:
            return user.sudo()

        api_group = self.env.ref(
            "agriware_connector.group_agriware_api_user"
        )
        internal_group = self.env.ref("base.group_user")

        user = self.env["res.users"].sudo().create({
            "name": f"AgriWare API Service ({company.name})",
            "login": f"agriware-api-service-{company.id}@agriware.local",
            "company_id": company.id,
            "company_ids": [(6, 0, [company.id])],
            "group_ids": [(6, 0, [internal_group.id, api_group.id])],
        })

        self.env["ir.model.data"].sudo().create({
            "name": xml_id,
            "module": "agriware_connector",
            "model": "res.users",
            "res_id": user.id,
            "noupdate": True,
        })

        return user

    @api.model
    def generate_key(self, name, company, expiration_date=None):
        """Create a new AgriWare API key for ``company``.

        :param str name: integration label shown in the UI.
        :param res.company company: the owning company.
        :param datetime.datetime|None expiration_date: ``None`` means the
            key never expires.
        :returns: tuple of (the raw API key, the created agriware.api.key
            record). The raw key is returned exactly once and is never
            stored anywhere.
        """
        self._check_can_manage(company=company)

        integration_user = self._get_or_create_integration_user(company)

        ApiKeys = self.env["res.users.apikeys"]

        raw_key = (
            ApiKeys.with_user(integration_user)
            .sudo()
            ._generate(scope=None, name=name, expiration_date=expiration_date)
        )

        # _generate() only returns the raw key, not the created row's id.
        # The row's "index" column is the key's first 8 hex characters
        # (see INDEX_SIZE in odoo/addons/base/models/res_users.py), which is
        # how Odoo itself looks keys up, so it reliably identifies the row
        # just inserted without depending on the (user-chosen, possibly
        # reused) integration name.
        self.env.cr.execute(
            """
            SELECT id FROM res_users_apikeys
            WHERE user_id = %s AND index = %s
            """,
            (integration_user.id, raw_key[:8]),
        )
        apikey_row = self.env.cr.fetchone()
        apikey_record = ApiKeys.sudo().browse(
            apikey_row[0] if apikey_row else []
        )

        record = self.sudo().create({
            "name": name,
            "company_id": company.id,
            "integration_user_id": integration_user.id,
            "apikey_id": apikey_record.id,
            "expiration_date": expiration_date,
            "never_expires": not expiration_date,
        })

        return raw_key, record

    def action_revoke(self):
        self._check_can_manage()

        for record in self:
            if record.state == "revoked":
                continue

            if record.apikey_id:
                record.apikey_id.sudo()._remove()

            record.write({
                "revoked_date": fields.Datetime.now(),
            })

        return True

    def action_create_replacement(self):
        """Open the generate wizard pre-filled from an expired or revoked
        key, so replacing it doesn't mean re-typing the integration name
        and expiration policy from scratch."""
        self.ensure_one()
        self._check_can_manage()

        return {
            "type": "ir.actions.act_window",
            "res_model": "agriware.api.key.generate.wizard",
            "name": _("Generate Replacement API Key"),
            "views": [(
                self.env.ref(
                    "agriware_connector.view_agriware_api_key_generate_wizard_form"
                ).id,
                "form",
            )],
            "target": "new",
            "context": {
                "default_name": self.name,
                "default_company_id": self.company_id.id,
                "default_never_expires": self.never_expires,
            },
        }
