# Copyright 2022-TODAY Rapsodoo Italia S.r.L. (www.rapsodoo.com)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

{
    "name": "Data Migration Tool",
    "version": "17.0.1.2.1",
    "summary": """Middleware for data migration""",
    "author": "Rapsodoo Italia",
    "website": "http://www.rapsodoo.com",
    "category": "Tools",
    "depends": [
        "base",
    ],
    "data": [
        "security/ir.model.access.csv",
        "security/dmt_security.xml",
        "views/data_migration_tool_views.xml",
        "views/db_connector_views.xml",
        "views/source_table_schema_views.xml",
        "views/source_table_column_views.xml",
        "views/table_mapper_views.xml",
        "views/table_mapper_match_views.xml",
        "views/relational_helper_views.xml",
        "views/relational_helper_m2m_views.xml",
        "views/table_mapper_groups_views.xml",
        "wizards/import_table_schema_wizard.xml",
        "wizards/import_report_wizard.xml",
        "wizards/relational_helper_report_wizard.xml",
        "wizards/show_tables_wizard.xml",
        "wizards/create_mapper_wizard.xml",
    ],
    "license": "LGPL-3",
    "external_dependencies": {
        "python": [
            "mysql.connector",
            "pymssql",
        ],
    },
}
