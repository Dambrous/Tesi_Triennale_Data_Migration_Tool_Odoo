# Copyright 2023-TODAY Rapsodoo Italia S.r.L. (www.rapsodoo.com)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import fields, models


class RelationalHelperReportWizard(models.TransientModel):
    _name = "relational.helper.report.wizard"
    _description = "Relational Helper Report Wizard"

    updated_records_count = fields.Integer()

    records_model_name = fields.Char()
