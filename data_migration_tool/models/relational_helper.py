# Copyright 2023-TODAY Rapsodoo Italia S.r.L. (www.rapsodoo.com)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

import logging

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class RelationalHelper(models.Model):
    _name = "relational.helper"
    description = "Relational Helper"

    name = fields.Char(compute="_compute_name")

    model_1_id = fields.Many2one(
        "ir.model",
        string="2Many Odoo Model",
    )

    model_1_relational_field_id = fields.Many2one(
        "ir.model.fields",
        string="M2O Relational Field to Set",
        domain="[('model_id', '=', model_1_id)]",
    )

    matching_mode = fields.Selection(
        [
            ("key", "Match on key fields"),
            ("relational_match", "Match on Relational Match Record"),
        ],
        default="key",
    )

    model_1_key_field_id = fields.Many2one(
        "ir.model.fields",
        string="Key in Model 1",
        domain="[('model_id', '=', model_1_id)]",
    )

    model_2_id = fields.Many2one(
        "ir.model",
        string="2One Odoo Model",
    )

    model_2_key_field_id = fields.Many2one(
        "ir.model.fields",
        string="Key in Model 2",
        domain="[('model_id', '=', model_2_id)]",
    )

    restrict_conditions = fields.Boolean()

    matching_id_min = fields.Integer()

    matching_id_max = fields.Integer()

    relational_match_id = fields.Many2one("relational.match", string="Relational Match")

    @api.depends("model_1_id", "model_2_id", "model_1_relational_field_id")
    def _compute_name(self):
        for helper in self:
            helper.name = "Many records of {} --> One record of {}".format(
                helper.model_1_id.name, helper.model_2_id.name
            )
            if helper.model_1_relational_field_id:
                helper.name += " : relation established on {} field".format(
                    helper.model_1_relational_field_id.name
                )

    def set_relation_action(self):
        model_1_records = (
            self.env[self.model_1_id.model]
            .search([])
            .filtered(lambda record: record[self.model_1_key_field_id.name])
        )

        if self.restrict_conditions:
            model_1_records = model_1_records.filtered(
                lambda record: self.matching_id_min
                <= int(record[self.model_1_key_field_id.name])
                <= self.matching_id_max
            )

        updated_records_count = 0
        logging_counter = 0
        logging_total = len(model_1_records)
        if self.matching_mode == "key":
            for model_1_record in model_1_records:
                logging_counter += 1
                _logger.info(
                    "Setting relation for record with key = {}; {}/{}".format(
                        model_1_record[self.model_1_key_field_id.name],
                        logging_counter,
                        logging_total,
                    )
                )
                _logger.info("--------")

                model_2_record = self.env[self.model_2_id.model].search(
                    [
                        (
                            self.model_2_key_field_id.name,
                            "=",
                            model_1_record[self.model_1_key_field_id.name],
                        )
                    ],
                    order="id",
                )

                # In case more than one record of model 2 is retrieved, the many2one relation
                # will be set with the first item of the recordset (which is sorted by id)
                if model_2_record:
                    model_1_record.write(
                        {self.model_1_relational_field_id.name: model_2_record[0].id}
                    )
                    updated_records_count += 1
        elif self.matching_mode == "relational_match":
            # Check if both odoo model has the tracer field
            if not hasattr(
                self.env[self.model_1_id.model], "x_dmt_tracer_id"
            ) or not hasattr(self.env[self.model_2_id.model], "x_dmt_tracer_id"):
                raise ValidationError(
                    _(
                        "Both Odoo models must have a tracer field in order to use relation match mode!"
                    )
                )

            for model_1_record in model_1_records:
                # retrieve the tracer related to this model 1 record
                tracer_of_model_1_record = model_1_record.x_dmt_tracer_id
                if not tracer_of_model_1_record:
                    continue

                # retrieve the foreign keys of the tracer and select the one that match the relational matcher
                foreign_key = tracer_of_model_1_record.foreignkey_tracer_ids.filtered(
                    lambda fkt: fkt.related_table_id
                    == self.relational_match_id.related_source_table_schema_id
                    and fkt.key_column == self.relational_match_id.relational_column_id
                )
                if not foreign_key:
                    continue

                # retrieve the tracer of the corresponding model 2 record
                related_source_table_schema = foreign_key.related_table_id
                tracer_of_model_2_record = self.env["record.tracer"].search(
                    [
                        ("source_table_schema_id", "=", related_source_table_schema.id),
                        ("source_table_primary_key", "=", foreign_key.key_value),
                    ]
                )
                if not tracer_of_model_2_record:
                    continue

                # retrieve corresponding record of model 2
                model_2_record = self.env[self.model_2_id.model].search(
                    [("x_dmt_tracer_id", "=", tracer_of_model_2_record.id)], order="id"
                )
                if model_2_record:
                    model_1_record.write(
                        {self.model_1_relational_field_id.name: model_2_record[0].id}
                    )
                    updated_records_count += 1

        return self.show_report(updated_records_count)

    def show_report(self, updated_records_count):
        relational_helper_report_wizard = self.env[
            "relational.helper.report.wizard"
        ].create(
            {
                "records_model_name": self.model_1_id.model,
                "updated_records_count": updated_records_count,
            }
        )

        return {
            "type": "ir.actions.act_window",
            "view_mode": "form",
            "view_id": self.env.ref(
                "data_migration_tool.relational_helper_report_wizard_form"
            ).id,
            "target": "new",
            "res_id": relational_helper_report_wizard.id,
            "res_model": "relational.helper.report.wizard",
        }
