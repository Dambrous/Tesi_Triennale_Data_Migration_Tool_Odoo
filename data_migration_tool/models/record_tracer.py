# Copyright 2023-TODAY Rapsodoo Italia S.r.L. (www.rapsodoo.com)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import fields, models


class RecordTracer(models.Model):
    _name = "record.tracer"
    description = "Record Tracer"

    mapper_id = fields.Many2one("table.mapper", ondelete="cascade")

    source_table_schema_id = fields.Many2one(
        "source.table.schema", related="mapper_id.source_table_schema_id"
    )

    source_table_primary_key = fields.Integer()

    foreignkey_tracer_ids = fields.One2many("foreignkey.tracer", "record_tracer_id")
