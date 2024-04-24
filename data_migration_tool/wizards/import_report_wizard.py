# Copyright 2023-TODAY Rapsodoo Italia S.r.L. (www.rapsodoo.com)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import fields, models


class ImportReportWizard(models.TransientModel):
    _name = "import.report.wizard"
    _description = "Import Report Wizard"

    records_model_name = fields.Char()
    table_mapper_name = fields.Char()
    created_records_count = fields.Integer()
    updated_records_count = fields.Integer()
    custom_message = fields.Html()
