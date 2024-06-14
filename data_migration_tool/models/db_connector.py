# Copyright 2023-TODAY Rapsodoo Italia S.r.L. (www.rapsodoo.com)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

import logging

import mysql.connector
import pymssql

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class DatabaseConnector(models.Model):
    _name = "db.connector"
    description = "Database Connector"

    name = fields.Char(string="Connector Name")

    connector_type = fields.Selection(
        [("mysql", "MySQL"), ("sql_server", "SQL Server"), ("azure_db", "Azure DB")],
        default="mysql",
        required=True,
    )

    user_name = fields.Char()

    database_name = fields.Char()

    url_host = fields.Char()

    password = fields.Char()

    error_message = fields.Char()

    port = fields.Char(compute="_compute_default_port", store=True, readonly=False)

    driver = fields.Char()

    @api.depends("connector_type")
    def _compute_default_port(self):
        for connector in self:
            if connector.connector_type == "mysql":
                connector.port = "3306"
            elif connector.connector_type in ["sql_server", "azure_db"]:
                connector.port = "1433"
            else:
                connector.port = ""

    def test_connection_action(self):
        connection = self.connect()
        connection_report = self.env["import.report.wizard"].create({})

        if connection:
            connection.close()
            connection_report.custom_message = "Connection OK"
        else:
            connection_report.custom_message = "Connection ERROR: {}".format(
                self.error_message
            )

        return {
            "type": "ir.actions.act_window",
            "view_mode": "form",
            "view_id": self.env.ref("data_migration_tool.import_report_wizard_form").id,
            "target": "new",
            "res_id": connection_report.id,
            "res_model": "import.report.wizard",
        }

    def connect(self):
        self.ensure_one()
        try:
            if self.connector_type == "mysql":
                db_connector = self.connect_to_mysql_db()
            elif (
                self.connector_type == "sql_server" or self.connector_type == "azure_db"
            ):
                db_connector = self.connect_to_sql_server_db()
            else:
                raise Exception()
        except Exception as e:
            msg = getattr(e, "msg", str(e))
            if not msg:
                raise ValidationError(
                    _("You must select a connector type!") + msg
                ) from e
            else:
                raise ValidationError(_("SQL ERROR: ") + msg) from e
        return db_connector

    def connect_to_mysql_db(self):
        user = self.user_name
        database = self.database_name
        host = self.url_host
        port = self.port
        password = self.password
        db_connector = mysql.connector.connect(
            user=user, database=database, host=host, password=password, port=port
        )
        return db_connector

    def connect_to_sql_server_db(self):
        conn = pymssql.connect(
            server=self.url_host,
            user=self.user_name,
            password=self.password,
            database=self.database_name,
            port=self.port,
        )

        return conn

    def show_all_tables_action(self):
        connector = self.connect()
        if connector and self.connector_type == "mysql":
            query = "SHOW TABLES"
        elif connector and self.connector_type == "sql_server":
            query = "SELECT * FROM SYSOBJECTS WHERE xtype = 'U';"
        else:
            raise UserError(_("Connector type not found"))

        cursor = connector.cursor()
        cursor.execute(query)
        tables = self.retrieve_tables(cursor)
        wizard = self.env["show.tables.wizard"].create(
            {
                "db_connector_id": self.id,
                "table_ids": [(6, 0, tables.ids)],
            }
        )
        return {
            "type": "ir.actions.act_window",
            "view_mode": "form",
            "view_id": self.env.ref("data_migration_tool.show_tables_wizard_form").id,
            "target": "new",
            "res_id": wizard.id,
            "res_model": "show.tables.wizard",
        }

    def retrieve_tables(self, cursor):
        tables = self.env["table.wizard"]
        for row in cursor:
            table_dic = {
                "name": row[0],
            }
            tables |= tables.create(table_dic)
        return tables
