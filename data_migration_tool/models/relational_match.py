# Copyright 2023-TODAY Rapsodoo Italia S.r.L. (www.rapsodoo.com)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import fields, models


class RelationalMatch(models.Model):
    _name = "relational.match"
    description = "Relational Match"

    name = fields.Char(compute="_compute_name")

    table_mapper_id = fields.Many2one(
        comodel_name="table.mapper",
        ondelete="cascade",
    )

    source_table_schema_id = fields.Many2one(
        "source.table.schema", related="table_mapper_id.source_table_schema_id"
    )

    db_connector_id = fields.Many2one(
        "db.connector", related="table_mapper_id.source_table_schema_id.db_connector_id"
    )

    relational_column_id = fields.Many2one(
        "source.table.column",
        string="Relational Column",
        required=True,
        domain="[('source_table_schema_id', '=', source_table_schema_id)]",
    )

    related_source_table_schema_id = fields.Many2one(
        "source.table.schema",
        string="Related Table",
        required=True,
        domain="[('db_connector_id', '=', db_connector_id)]",
    )

    def _compute_name(self):
        for relational_match in self:
            relational_match.name = "{}: {} --> {}".format(
                relational_match.table_mapper_id.name,
                relational_match.relational_column_id.name,
                relational_match.related_source_table_schema_id.table_name,
            )
