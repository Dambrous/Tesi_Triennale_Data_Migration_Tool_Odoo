# Copyright 2023-TODAY Rapsodoo Italia S.r.L. (www.rapsodoo.com)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

import logging

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class RelationalHelperM2M(models.Model):
    _name = "relational.helper_m2m"
    description = "Relational Helper Many2Many"

    name = fields.Char(compute="_compute_name")

    model_1_id = fields.Many2one(
        "ir.model",
        string="Odoo Model 1",
    )

    model_1_relational_field_id = fields.Many2one(
        "ir.model.fields",
        string="M2M Relational Field to Set",
        domain="[('model_id', '=', model_1_id)]",
    )

    model_1_matching_mode = fields.Selection(
        [
            ("key", "Match on key fields"),
            ("tracer", "Match using tracer"),
        ],
        default="key",
    )

    model_1_key_field_id = fields.Many2one(
        "ir.model.fields",
        string="Key in model 1",
        domain="[('model_id', '=', model_1_id)]",
    )

    model_2_id = fields.Many2one(
        "ir.model",
        string="Odoo Model 2",
    )

    model_2_matching_mode = fields.Selection(
        [
            ("key", "Match on key fields"),
            ("tracer", "Match using tracer"),
        ],
        default="key",
    )

    model_2_key_field_id = fields.Many2one(
        "ir.model.fields",
        string="Key in model 2",
        domain="[('model_id', '=', model_2_id)]",
    )

    pivot_table_id = fields.Many2one(
        "source.table.schema",
        string="Pivot Table",
    )

    pivot_table_column_ids = fields.One2many(
        "source.table.column", related="pivot_table_id.column_ids"
    )

    m1_pivot_col_match_id = fields.Many2one(
        "source.table.column", domain="[('id', 'in', pivot_table_column_ids)]"
    )

    m2_pivot_col_match_id = fields.Many2one(
        "source.table.column", domain="[('id', 'in', pivot_table_column_ids)]"
    )

    @api.depends("model_1_id", "model_2_id", "model_1_relational_field_id")
    def _compute_name(self):
        for helper in self:
            helper.name = "Many records of {} --> Many records of {}".format(
                helper.model_1_id.name, helper.model_2_id.name
            )
            if helper.model_1_relational_field_id:
                helper.name += " : relation established on {} field".format(
                    helper.model_1_relational_field_id.name
                )

    def set_m2m_relation_action(self):
        if not self.pivot_table_id:
            raise ValidationError(
                _("Your M2M helper needs a db connector to import data")
            )

        if (
            self.model_1_matching_mode == "tracer"
            or self.model_2_matching_mode == "tracer"
        ):
            self.check_tracer_exists()

        # Retrieve connection and obtain a cursor obj
        db_connector = self.pivot_table_id.db_connector_id.connect()
        if not db_connector:
            raise ValidationError(_("DB Connection Error"))

        cursor = db_connector.cursor()

        query = "SELECT {}, {} FROM {}".format(
            self.m1_pivot_col_match_id.name,
            self.m2_pivot_col_match_id.name,
            self.pivot_table_id.table_name,
        )

        cursor.execute(query)

        relation_count = 0

        row_count = 0

        for row in cursor:
            _logger.info("Record {}".format(str(row_count)))
            model_1_record = False
            model_2_record = False
            # Retrieve Model 1 record
            if self.model_1_matching_mode == "key":
                model_1_record = self.env[self.model_1_id.model].search(
                    [(self.model_1_key_field_id.name, "=", row[0])], order="id", limit=1
                )
            elif self.model_1_matching_mode == "tracer":
                model_1_record = self.env[self.model_1_id.model].search(
                    [("x_dmt_tracer_id.source_table_primary_key", "=", row[0])]
                )

            # Retrieve Model 2 record
            if self.model_2_matching_mode == "key":
                model_2_record = self.env[self.model_2_id.model].search(
                    [(self.model_2_key_field_id.name, "=", row[1])], order="id", limit=1
                )
            elif self.model_2_matching_mode == "tracer":
                model_2_record = self.env[self.model_2_id.model].search(
                    [("x_dmt_tracer_id.source_table_primary_key", "=", row[1])]
                )

            if not model_1_record or not model_2_record:
                continue

            # Set relation
            model_1_record.write(
                {self.model_1_relational_field_id.name: [(4, model_2_record.id)]}
            )

            relation_count += 1

        return self.show_report(relation_count)

    def show_report(self, relation_count):
        helper_report_wizard = self.env["import.report.wizard"].create(
            {
                "custom_message": "{} relations established between model {} and model {}".format(
                    str(relation_count), self.model_1_id.model, self.model_2_id.model
                )
            }
        )

        return {
            "type": "ir.actions.act_window",
            "view_mode": "form",
            "view_id": self.env.ref("data_migration_tool.import_report_wizard_form").id,
            "target": "new",
            "res_id": helper_report_wizard.id,
            "res_model": "import.report.wizard",
        }

    def check_tracer_exists(self):
        if self.model_1_matching_mode == "tracer" and not hasattr(
            self.env[self.model_1_id.model], "x_dmt_tracer_id"
        ):
            raise ValidationError(
                _(
                    "The model {} has no tracer object! Please change matching mode."
                ).format(self.model_1_id.model)
            )

        if self.model_2_matching_mode == "tracer" and not hasattr(
            self.env[self.model_2_id.model], "x_dmt_tracer_id"
        ):
            raise ValidationError(
                _(
                    "The model {} has no tracer object! Please change matching mode."
                ).format(self.model_2_id.model)
            )
