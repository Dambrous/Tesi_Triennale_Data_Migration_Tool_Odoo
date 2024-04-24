# Copyright 2023-TODAY Rapsodoo Italia S.r.L. (www.rapsodoo.com)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class SourceTableSchema(models.Model):
    _name = "source.table.schema"
    description = "Source Table Schema"
    _rec_name = "table_name"

    table_name = fields.Char()

    column_ids = fields.One2many(
        comodel_name="source.table.column",
        inverse_name="source_table_schema_id",
    )

    db_connector_id = fields.Many2one("db.connector", ondelete="cascade")

    @api.constrains("table_name", "db_connector_id")
    def _check_for_table_duplicates(self):
        for table in self:
            records = self.env["source.table.schema"].search_count(
                [
                    ("table_name", "=", table.table_name),
                    ("db_connector_id", "=", table.db_connector_id.id),
                ]
            )
            if records > 1:
                raise ValidationError(
                    _(
                        "The table schema {} was already imported".format(
                            table.table_name
                        )
                    )
                )

    def create_mapper_action(self):
        create_mapper_wizard = self.env["create.mapper.wizard"].create(
            {
                "source_table_schema_id": self.id,
            }
        )
        return {
            "type": "ir.actions.act_window",
            "view_mode": "form",
            "view_id": self.env.ref("data_migration_tool.create_mapper_wizard_form").id,
            "target": "new",
            "res_id": create_mapper_wizard.id,
            "res_model": "create.mapper.wizard",
        }
