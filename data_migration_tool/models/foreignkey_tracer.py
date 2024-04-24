# Copyright 2023-TODAY Rapsodoo Italia S.r.L. (www.rapsodoo.com)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import fields, models


class ForeignkeyTracer(models.Model):
    _name = "foreignkey.tracer"
    description = "Foreignkey Tracer"

    key_value = fields.Integer()

    key_column = fields.Many2one("source.table.column")

    name = fields.Char(related="key_column.name")

    related_table_id = fields.Many2one("source.table.schema", ondelete="cascade")

    record_tracer_id = fields.Many2one("record.tracer", ondelete="cascade")
