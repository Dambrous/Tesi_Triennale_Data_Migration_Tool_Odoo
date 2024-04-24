# Copyright 2023-TODAY Rapsodoo Italia S.r.L. (www.rapsodoo.com)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import fields, models


class TableWizard(models.TransientModel):
    _name = "table.wizard"
    _description = "Table Wizard"

    name = fields.Char()
    show_tables_wizard_id = fields.Many2one("show.tables.wizard", ondelete="cascade")
    selected_for_import = fields.Boolean()
