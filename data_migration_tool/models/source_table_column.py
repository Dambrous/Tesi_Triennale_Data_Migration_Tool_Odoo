# Copyright 2023-TODAY Rapsodoo Italia S.r.L. (www.rapsodoo.com)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import fields, models


class SourceTableColumn(models.Model):
    _name = "source.table.column"
    description = "Source Table Column"

    name = fields.Char()

    column_type = fields.Char()

    column_null = fields.Char("Null")

    column_key = fields.Char("Key")

    column_default = fields.Char("Default")

    column_extra = fields.Char("Extra")

    source_table_schema_id = fields.Many2one("source.table.schema", ondelete="cascade")
