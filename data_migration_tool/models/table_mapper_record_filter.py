# Copyright 2023-TODAY Rapsodoo Italia S.r.L. (www.rapsodoo.com)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import fields, models


class TableMapperRecordFilter(models.Model):
    _name = "table.mapper.record.filter"
    description = "Table Mapper Record Filter"

    table_mapper_destination_id = fields.Many2one(
        comodel_name="table.mapper",
        ondelete="cascade",
    )

    table_mapper_source_id = fields.Many2one(
        comodel_name="table.mapper",
        ondelete="cascade",
    )

    is_active = fields.Boolean(default=True)

    filter_type = fields.Selection(
        [
            ("source", "Source Record Filter"),
            ("destination", "Destination Record Filter"),
        ],
        default="destination",
    )

    source_table_schema_id = fields.Many2one(
        "source.table.schema", related="table_mapper_source_id.source_table_schema_id"
    )

    filtering_column_id = fields.Many2one(
        "source.table.column",
        domain="[('source_table_schema_id', '=', source_table_schema_id)]",
    )

    odoo_model_id = fields.Many2one(
        "ir.model", related="table_mapper_destination_id.odoo_model_id"
    )

    filtering_field_id = fields.Many2one(
        "ir.model.fields", domain="[('model_id', '=', odoo_model_id)]"
    )

    filtering_operator = fields.Selection(
        [
            ("=", "="),
            ("!=", "!="),
            ("<", "< (for numeric field only)"),
            (">", "> (for numeric field only)"),
        ],
        default="=",
    )

    cast_to_integer = fields.Boolean()

    filtering_value = fields.Char()
