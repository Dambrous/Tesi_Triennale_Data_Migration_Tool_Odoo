# Copyright 2023-TODAY Rapsodoo Italia S.r.L. (www.rapsodoo.com)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import api, fields, models


class TableMapperMatch(models.Model):
    _name = "table.mapper.match"
    description = "Table Mapper Match"

    name = fields.Char(compute="_compute_name")

    table_mapper_id = fields.Many2one(
        comodel_name="table.mapper",
        ondelete="cascade",
    )

    mapping_mode = fields.Selection(
        related="table_mapper_id.mapping_mode",
    )

    filling_mode = fields.Selection(
        [
            ("single", "Single Source Column Value"),
            ("multi", "Multiple Concatenated Source Column Values"),
            ("fixed", "Fixed Value"),
            ("sequence", "Get Odoo Sequence"),
            ("random_id", "Get Random Id"),
        ],
        default="single",
    )

    concatenation_operator = fields.Selection(
        [
            (" ", "Blank Space"),
            (" / ", "Slash"),
            (" - ", "Dash"),
            (" + ", "Plus"),
            (
                "",
                "No Space",
            ),
        ],
        default=" ",
    )

    source_table_schema_id = fields.Many2one(
        "source.table.schema", related="table_mapper_id.source_table_schema_id"
    )

    source_table_column_id = fields.Many2one(
        "source.table.column",
        domain="[('source_table_schema_id', '=', source_table_schema_id)]",
    )

    source_table_concat_column_ids = fields.Many2many(
        "source.table.column",
        domain="[('source_table_schema_id', '=', source_table_schema_id)]",
    )

    fixed_value = fields.Char()

    odoo_model_id = fields.Many2one("ir.model", related="table_mapper_id.odoo_model_id")

    odoo_model_field_id = fields.Many2one(
        "ir.model.fields", domain="[('model_id', '=', odoo_model_id)]"
    )

    exclude_duplicate = fields.Boolean()

    set_default_value_if_null = fields.Boolean()

    default_value = fields.Char()

    convert_values = fields.Boolean()

    match_conversion_ids = fields.Many2many("table.mapper.match.conversion")

    is_active = fields.Boolean(default=True)

    force_casting = fields.Selection(
        [
            ("no_casting", "No Casting"),
            ("integer", "Cast to Integer"),
            ("float", "Cast to Float"),
        ],
        default="no_casting",
    )

    force_fixed_length = fields.Boolean()

    fixed_max_length = fields.Integer(default=10)

    fixed_min_length = fields.Integer(default=10)

    padding_character = fields.Selection(
        [(" ", "Blank Space"), ("0", "Zero"), ("-", "Dash")], default="0"
    )

    padding_position = fields.Selection(
        [
            ("L", "Pad to Left"),
            ("R", "Pad to Right"),
        ],
        default="R",
    )

    truncate_side = fields.Selection(
        [
            ("L", "Truncate Left"),
            ("R", "Truncate Right"),
        ],
        default="R",
    )

    @api.depends(
        "source_table_column_id.name",
        "odoo_model_field_id.name",
        "source_table_concat_column_ids",
        "concatenation_operator",
        "filling_mode",
    )
    def _compute_name(self):
        fixed_key = 1
        sequence_key = 1
        random_key = 1
        for table_mapper_match in self:
            table_mapper_match.name = ""
            if (
                table_mapper_match.mapping_mode == "existing_records_fixed"
                or table_mapper_match.filling_mode == "fixed"
            ):
                table_mapper_match.name = '"{}"'.format(
                    "Fixed_Value_"
                    + str(fixed_key)
                    + "__"
                    + str(table_mapper_match.fixed_value)
                )
                fixed_key += 1
            elif table_mapper_match.filling_mode == "single":
                table_mapper_match.name = str(
                    table_mapper_match.source_table_column_id.name
                )
            elif table_mapper_match.filling_mode == "multi":
                table_mapper_match.name = table_mapper_match.concatenation_operator.join(
                    [
                        str(name)
                        for name in table_mapper_match.source_table_concat_column_ids.mapped(
                            "name"
                        )
                    ]
                )
            elif table_mapper_match.filling_mode == "sequence":
                table_mapper_match.name = "Odoo_Sequence" + "_" + str(sequence_key)
                sequence_key += 1
            elif table_mapper_match.filling_mode == "random_id":
                table_mapper_match.name = "Random_Id" + "_" + str(random_key)
                random_key += 1
            table_mapper_match.name += " --> {}".format(
                str(table_mapper_match.odoo_model_field_id.name)
            )
