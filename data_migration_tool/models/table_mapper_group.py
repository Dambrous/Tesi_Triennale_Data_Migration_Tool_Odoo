# Copyright 2023-TODAY Rapsodoo Italia S.r.L. (www.rapsodoo.com)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import fields, models


class TableMapperGroup(models.Model):
    _name = "table.mapper.group"
    description = "Table Mapper Group"

    name = fields.Char(string="Mapper Group Name")

    table_mapper_group_line_ids = fields.One2many(
        comodel_name="table.mapper.group.line",
        inverse_name="table_mapper_group_id",
    )

    def mappers_data_import_action(self):
        for mapper_group in self:
            res_ids = []
            for mapper_group_line in mapper_group.table_mapper_group_line_ids.sorted(
                key=lambda record: record.sequence
            ):
                report = mapper_group_line.table_mapper_id.import_data_action()
                res_ids.append(report["res_id"])

        return {
            "type": "ir.actions.act_window",
            "view_mode": "tree",
            "name": "Import Report",
            "target": "new",
            "view_id": self.env.ref("data_migration_tool.import_report_wizard_tree").id,
            "domain": [("id", "in", res_ids)],
            "res_model": "import.report.wizard",
        }
