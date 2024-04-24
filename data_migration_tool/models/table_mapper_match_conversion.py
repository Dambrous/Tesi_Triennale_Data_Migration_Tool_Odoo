# Copyright 2023-TODAY Rapsodoo Italia S.r.L. (www.rapsodoo.com)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import api, fields, models


class TableMapperMatch(models.Model):
    _name = "table.mapper.match.conversion"
    description = "Table Mapper Match Conversion"

    name = fields.Char(compute="_compute_name")

    original_value = fields.Char()

    converted_value = fields.Char()

    @api.depends("original_value", "converted_value")
    def _compute_name(self):
        for conversion in self:
            conversion.name = "{} --> {}".format(
                conversion.original_value, conversion.converted_value
            )
