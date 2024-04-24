# Copyright 2023-TODAY Rapsodoo Italia S.r.L. (www.rapsodoo.com)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import _, fields, models
from odoo.exceptions import ValidationError


class ImportTableSchemaWizard(models.TransientModel):
    _name = "import.table.schema.wizard"
    _description = "Import Table Schema Wizard"

    db_connector_id = fields.Many2one(
        "db.connector",
        string="Database Connector",
        required=True,
    )

    table_name = fields.Char(required=True)

    table_schema_id = fields.Many2one("source.table.schema")

    def import_table_schema_action(self):
        db_connector = self.db_connector_id.connect()
        if not db_connector:
            raise ValidationError(_("DB Connection Error"))

        cursor = db_connector.cursor()

        if self.db_connector_id.connector_type == "mysql":
            query = "DESCRIBE {}.{};".format(
                self.db_connector_id.database_name, self.table_name
            )
        elif self.db_connector_id.connector_type == "sql_server":
            query = "exec sp_columns {};".format(self.table_name)
        else:
            raise ValidationError(_("Connector type not found"))

        try:
            cursor.execute(query)
        except Exception as e:
            msg = getattr(e, "msg", str(e))
            raise ValidationError(_("SQL Error: ") + msg) from e

        columns = self.retrieve_table_columns(cursor)
        new_table_schema = self.env["source.table.schema"].create(
            {
                "table_name": self.table_name,
                "column_ids": [(6, 0, columns.ids)],
                "db_connector_id": self.db_connector_id.id,
            }
        )
        self.table_schema_id = new_table_schema

        cursor.close()
        db_connector.close()

        return {
            "type": "ir.actions.act_window",
            "view_mode": "form",
            "view_id": self.env.ref(
                "data_migration_tool.import_table_schema_wizard_report"
            ).id,
            "target": "new",
            "res_id": self.id,
            "res_model": "import.table.schema.wizard",
        }

    def show_schema_action(self):
        return {
            "type": "ir.actions.act_window",
            "view_mode": "form",
            "view_id": self.env.ref("data_migration_tool.source_table_schema_form").id,
            "target": "_blank",
            "res_id": self.table_schema_id.id,
            "res_model": "source.table.schema",
        }

    def retrieve_table_columns(self, cursor):
        columns = self.env["source.table.column"]
        for column in cursor:
            col_vals = {
                "name": column[0]
                if self.db_connector_id.connector_type == "mysql"
                else column[3],
                "column_type": column[1]
                if self.db_connector_id.connector_type == "mysql"
                else column[5],
                "column_null": column[2]
                if self.db_connector_id.connector_type == "mysql"
                else column[17],
                "column_key": column[3]
                if self.db_connector_id.connector_type == "mysql"
                else False,
                "column_default": column[4]
                if self.db_connector_id.connector_type == "mysql"
                else False,
                "column_extra": column[5]
                if self.db_connector_id.connector_type == "mysql"
                else False,
            }
            columns |= columns.create(col_vals)
        return columns
