# Copyright 2023-TODAY Rapsodoo Italia S.r.L. (www.rapsodoo.com)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import fields, models


class CreateMapperWizard(models.TransientModel):
    _name = "create.mapper.wizard"
    _description = "Create Mapper Wizard"

    source_table_schema_id = fields.Many2one(
        "source.table.schema",
        required=True,
    )

    odoo_model_id = fields.Many2one(
        "ir.model",
        string="Odoo Model to Map",
    )

    def create_mapper_action(self):
        mapper_name = "{} - {} Mapper".format(
            self.source_table_schema_id.table_name,
            self.odoo_model_id.model,
        )

        action = self.env["ir.actions.actions"]._for_xml_id(
            "data_migration_tool.action_show_table_mappers"
        )
        action["context"] = dict(self.env.context)
        action["context"]["form_view_initial_mode"] = "edit"
        action["context"]["default_name"] = mapper_name
        action["context"][
            "default_source_table_schema_id"
        ] = self.source_table_schema_id.id
        action["context"]["default_odoo_model_id"] = self.odoo_model_id.id
        action["views"] = [
            (self.env.ref("data_migration_tool.table_mapper_form").id, "form")
        ]
        return action
