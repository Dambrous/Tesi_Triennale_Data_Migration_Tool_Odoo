# Copyright 2023-TODAY Rapsodoo Italia S.r.L. (www.rapsodoo.com)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import fields, models


class ShowTablesWizard(models.TransientModel):
    _name = "show.tables.wizard"
    _description = "Show Tables Wizard"

    db_connector_id = fields.Many2one(
        "db.connector",
        string="Database Connector",
    )
    db_name = fields.Char(related="db_connector_id.database_name", readonly=True)
    table_ids = fields.One2many(
        "table.wizard", "show_tables_wizard_id", string="Tables"
    )

    def select_deselect_action(self):
        action = self.env.context.get("select_action")
        for table in self.table_ids:
            table.selected_for_import = action

        return {
            "type": "ir.actions.act_window",
            "view_mode": "form",
            "view_id": self.env.ref("data_migration_tool.show_tables_wizard_form").id,
            "target": "new",
            "res_id": self.id,
            "res_model": "show.tables.wizard",
        }

    def import_selected_action(self):
        imported_table_count = 0
        for table in self.table_ids.filtered("selected_for_import"):
            import_wizard = self.env["import.table.schema.wizard"].create(
                {"db_connector_id": self.db_connector_id.id, "table_name": table.name}
            )
            import_wizard.import_table_schema_action()
            imported_table_count += 1

        custom_message = "Imported {} table schema{} from database {}".format(
            imported_table_count, ("", "s")[imported_table_count > 1], self.db_name
        )
        report_wizard = self.env["import.report.wizard"].create(
            {"custom_message": custom_message}
        )

        return {
            "type": "ir.actions.act_window",
            "view_mode": "form",
            "view_id": self.env.ref("data_migration_tool.import_report_wizard_form").id,
            "target": "new",
            "res_id": report_wizard.id,
            "res_model": "import.report.wizard",
        }
