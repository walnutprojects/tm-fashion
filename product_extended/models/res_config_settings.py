from odoo import fields, models, api


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    auto_assign_internal_reference = fields.Boolean(string="Auto Assign Internal Reference for Product")

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        params = self.env['ir.config_parameter'].sudo()
        auto_assign_internal_reference = params.get_param('auto_assign_internal_reference',
                                                 default=False)
        res.update(auto_assign_internal_reference=auto_assign_internal_reference)
        return res

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param(
            "auto_assign_internal_reference",
            self.auto_assign_internal_reference)
