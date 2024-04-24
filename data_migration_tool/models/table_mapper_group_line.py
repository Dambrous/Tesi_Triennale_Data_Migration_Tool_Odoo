# Copyright 2023-TODAY Rapsodoo Italia S.r.L. (www.rapsodoo.com)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import fields, models


class TableMapperGroupLine(models.Model):
    _name = "table.mapper.group.line"
    description = "Table Mapper Group Line"

    sequence = fields.Integer(default=10)

    table_mapper_id = fields.Many2one("table.mapper", string="Table Mapper")

    table_mapper_group_id = fields.Many2one("table.mapper.group")
