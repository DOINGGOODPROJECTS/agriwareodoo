from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class AgriwareExternalSystem(models.Model):
    _name = "agriware.external.system"
    _description = "AgriWare External System"
    _order = "name"

    name = fields.Char(
        required=True,
        help="A human-readable name for this external system, "
             "e.g. 'Main Warehouse WMS'.",
    )

    code = fields.Char(
        required=True,
        help="A short, stable identifier for this external system, "
             "e.g. 'primary_wms'. External ID mappings are scoped to "
             "this code, not to any specific API key, so rotating or "
             "replacing an API key never orphans existing mappings.",
    )

    company_id = fields.Many2one(
        "res.company",
        string="Company",
        required=True,
        default=lambda self: self.env.company,
    )

    active = fields.Boolean(default=True)

    description = fields.Text()

    _code_company_uniq = models.Constraint(
        "unique(company_id, code)",
        "An external system with this code already exists for this company.",
    )

    @api.constrains("code")
    def _check_code(self):
        for record in self:
            if not record.code or not record.code.strip():
                raise ValidationError(_(
                    "The external system code cannot be empty."
                ))
