# Copyright 2023-TODAY Rapsodoo Italia S.r.L. (www.rapsodoo.com)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

import logging
from datetime import datetime

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from odoo.tests.common import Form

_logger = logging.getLogger(__name__)


class TableMapper(models.Model):
    _name = "table.mapper"
    description = "Table Mapper"

    # FIELDS DECLARATIONS
    name = fields.Char(string="Mapper Name")

    mapping_mode = fields.Selection(
        [
            ("new_records", "Primitive on new records"),
            ("existing_records", "Primitive on existing records"),
            ("existing_records_fixed", "Update existing records with fixed values"),
        ],
        default="new_records",
    )

    tracing_mode = fields.Boolean(default=True)

    concatenation_active = fields.Boolean()

    concatenation_mode = fields.Selection(
        [
            ("to_right", "Concatenate to Right"),
            ("to_left", "Concatenate to Left"),
        ],
        default="to_right",
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

    # Fields for Mapping function
    source_table_schema_id = fields.Many2one(
        "source.table.schema",
        string="Source Table",
        ondelete="cascade",
    )

    odoo_model_id = fields.Many2one(
        "ir.model",
        string="Odoo Model to Map",
    )

    match_ids = fields.One2many(
        comodel_name="table.mapper.match",
        inverse_name="table_mapper_id",
        string="Matches",
    )

    relational_match_ids = fields.One2many(
        comodel_name="relational.match",
        inverse_name="table_mapper_id",
        string="Relational Matches",
    )

    filter_source_records = fields.Boolean("Filter Source Records")

    source_record_filter_ids = fields.One2many(
        comodel_name="table.mapper.record.filter",
        inverse_name="table_mapper_source_id",
        string="Source Record Filters",
    )

    filter_destination_records = fields.Boolean("Filter Destination Records")

    destination_record_filter_ids = fields.One2many(
        comodel_name="table.mapper.record.filter",
        inverse_name="table_mapper_destination_id",
        string="Destination Record Filters",
    )

    source_table_column_ids = fields.One2many(
        "source.table.column", related="source_table_schema_id.column_ids"
    )

    condition = fields.Selection(
        [
            ("f_key_on_field", "Match Foreign Key on Odoo field"),
            ("f_key_on_tracer", "Match Foreign Key using Tracers"),
        ],
        default="f_key_on_field",
    )

    foreign_key = fields.Many2one(
        "source.table.column",
        domain="[('source_table_schema_id', '=', source_table_schema_id)]",
    )

    related_source_table = fields.Many2one(
        "source.table.schema",
        string="Related Source Table",
    )

    odoo_key = fields.Many2one(
        "ir.model.fields", domain="[('model_id', '=', odoo_model_id)]"
    )

    # Fields for Record Creation function
    limit_number_of_records = fields.Boolean()

    number_of_records_to_map = fields.Integer()

    apply_offset = fields.Boolean()

    offset = fields.Integer()

    record_creation_mode = fields.Selection(
        [
            ("db_query", "Faster (direct query to DB)"),
            ("create", "Intermediate (with create method)"),
            ("form", "Slower (with form)"),
        ],
        default="create",
    )

    primary_key_column_id = fields.Many2one(
        "source.table.column",
        domain="[('source_table_schema_id', '=', source_table_schema_id)]",
    )

    # SQL CONSTRINTS

    # DEFAULT METHODS

    # COMPUTE AND SEARCH METHODS

    # CONSTRAINTS AND ONCHANGE METHODS
    @api.onchange("mapping_mode")
    def _onchange_mapping_mode(self):
        if self.mapping_mode != "new_records":
            self.tracing_mode = False
        else:
            self.tracing_mode = True

    # CRUD METHODS

    # ACTION METHODS
    def import_data_action(self):
        if not self.source_table_schema_id.db_connector_id:
            raise ValidationError(_("Your mapper needs a db connector to import data"))

        # Retrieve connection and obtain a cursor obj
        db_connector = self.source_table_schema_id.db_connector_id.connect()
        if not db_connector:
            raise ValidationError(_("DB Connection Error"))

        cursor = db_connector.cursor()

        records_to_update = self.env[self.odoo_model_id.model]
        if self.mapping_mode == "existing_records":
            if self.condition == "f_key_on_field":
                records_to_update = records_to_update.search([]).filtered(
                    lambda record: record[self.odoo_key.name]
                )
            elif self.condition == "f_key_on_tracer":
                if "x_dmt_tracer_id" not in records_to_update._fields:
                    raise ValidationError(
                        _(
                            "Sorry, you can't use tracers mode because the selected model hasn't been traced"
                        )
                    )
                records_to_update = records_to_update.search([]).filtered(
                    lambda record: record["x_dmt_tracer_id"]
                )

        # Add destination filtering conditions
        if self.filter_destination_records:
            records_to_update = self.filter_records(records_to_update)

        if self.mapping_mode == "existing_records" and not records_to_update:
            # Close connection
            cursor.close()
            db_connector.close()

            # Return nothing created or updated
            return self.show_import_report(0, 0)

        # Build query and execute query on cursor obj
        query = self.build_query(records_to_update)
        cursor.execute(query)

        # Retrieve a list of source record dictionaries looping records retrieved by cursor
        source_record_dictionaries_list = self.build_source_record_dictionaries_list(
            cursor
        )

        # Retrieve relational data
        relational_match_dictionaries_list = []
        if self.relational_match_ids:
            query = self.build_query_for_relational_data()
            cursor.execute(query)
            relational_match_dictionaries_list = self.get_relational_match_list(cursor)

        # Build a list of odoo model vals dictionaries mapping each source record dictionary
        odoo_model_vals_dictionaries_list = (
            self.build_odoo_model_vals_dictionaries_list(
                source_record_dictionaries_list
            )
        )

        # Modification of list of dictionaries data: in this step we do every possible
        # modification of data contained in the model vals dictionaries before passing
        # them to the create function; it includes checking for uniqueness (exclude duplicate
        # values if requested), possible data casting on certain fields and so on.
        odoo_model_vals_dictionaries_list = self.check_for_duplicate(
            odoo_model_vals_dictionaries_list
        )

        odoo_model_vals_dictionaries_list = self.check_for_null_values(
            odoo_model_vals_dictionaries_list
        )

        odoo_model_vals_dictionaries_list = self.make_conversions(
            odoo_model_vals_dictionaries_list
        )

        odoo_model_vals_dictionaries_list = self.convert_special_values(
            odoo_model_vals_dictionaries_list
        )

        odoo_model_vals_dictionaries_list = self.force_casting(
            odoo_model_vals_dictionaries_list
        )

        odoo_model_vals_dictionaries_list = self.force_fixed_length(
            odoo_model_vals_dictionaries_list
        )

        odoo_model_vals_dictionaries_list = self.check_for_odoo_sequences(
            odoo_model_vals_dictionaries_list
        )

        created_records_count = 0
        updated_records_count = 0
        if odoo_model_vals_dictionaries_list:
            if self.mapping_mode == "new_records":
                # Create odoo records (of model = odoo_model_id) passing the list of odoo model vals dictionaries
                created_records_count = self.create_records(
                    odoo_model_vals_dictionaries_list,
                    source_record_dictionaries_list,
                    relational_match_dictionaries_list,
                )
            elif (
                self.mapping_mode == "existing_records"
                and not self.concatenation_active
            ):
                # Update existing records
                updated_records_count = self.update_records(
                    odoo_model_vals_dictionaries_list
                )
            elif self.mapping_mode == "existing_records" and self.concatenation_active:
                # Update existing records in concatenation mode
                updated_records_count = self.update_records_concat_mode(
                    odoo_model_vals_dictionaries_list
                )

        # Close connection
        cursor.close()
        db_connector.close()

        # Return a report message to the user
        return self.show_import_report(created_records_count, updated_records_count)

    def update_data_action(self):
        records_to_update = self.env[self.odoo_model_id.model].search([])
        update_count = 0

        # Add destination filtering conditions
        if self.filter_destination_records:
            records_to_update = self.filter_records(records_to_update)

        active_matches = self.match_ids.filtered(lambda match_id: match_id.is_active)
        for record in records_to_update:
            update_data_dic = {}
            for match in active_matches:
                update_data_dic.update(
                    {match.odoo_model_field_id.name: match.fixed_value}
                )

            # Dictionary checks/modifications
            # NOTE: check/modification methods take and return a list of dictionaries
            # so the dic is wrapped in a list and then extracted.
            dic_list = [update_data_dic]
            dic_list = self.convert_special_values(dic_list)
            dic_list = self.check_for_duplicate(dic_list)
            dic_list = self.force_casting(dic_list)
            update_data_dic = dic_list[0]

            record.write(update_data_dic)
            update_count += 1

        # Return a report message to the user
        return self.show_import_report(0, update_count)

    # BUSINESS METHODS
    def get_active_matches(self):
        active_matches = self.match_ids.filtered(lambda match_id: match_id.is_active)
        if not active_matches:
            raise ValidationError(
                _("Your mapper needs at least one active match to import something")
            )
        return active_matches

    def build_query_each_matches(self, active_matches):
        # Build the query for each type of match: single, multiple (concatenated) and fixed
        column_list = []

        for match in active_matches:
            if match.filling_mode == "single":
                column_list.append(match.source_table_column_id.name)
            elif match.filling_mode == "multi":
                concat_column = "CONCAT({})".format(
                    ", ".join(
                        [
                            col_name
                            for col_name in match.source_table_concat_column_ids.mapped(
                                "name"
                            )
                        ]
                    )
                )
                concat_column = concat_column.replace(
                    ", ", ', "{}", '.format(str(match.concatenation_operator))
                )
                column_list.append(concat_column)
            elif match.filling_mode == "fixed":
                column_list.append('"{}"'.format(match.fixed_value))
            elif match.filling_mode == "sequence":
                placeholder_sequence = match.odoo_model_id.model + "_**sequence**"
                column_list.append('"{}"'.format(placeholder_sequence))
            elif match.filling_mode == "random_id":
                random_id = self.env[match.odoo_model_field_id.relation].search(
                    [], limit=1, order="id asc"
                )
                if random_id:
                    column_list.append("{}".format(random_id.id))
                else:
                    raise ValidationError(
                        _(
                            "No record of type {} found in db".format(
                                match.odoo_model_field_id.relation
                            )
                        )
                    )
        columns = ", ".join(column_list)

        if self.mapping_mode == "existing_records":
            # in existing records' mode, add the foreign key column at the end of the list of field to import
            columns += " , {}".format(self.foreign_key.name)

        if self.tracing_mode:
            columns += " , {}".format(self.primary_key_column_id.name)

        query = "SELECT {} FROM {}".format(
            columns, self.source_table_schema_id.table_name
        )

        return query

    def add_condition_to_query(self, records_to_update, query):
        if self.mapping_mode == "existing_records" and records_to_update:
            # casting in tuple needed to obtain the correct SQL syntax with round parenthesis
            # the replace method is needed to eliminate the last comma
            record_ids = str(tuple())
            if self.condition == "f_key_on_field":
                record_ids = str(
                    tuple(records_to_update.mapped(self.odoo_key.name))
                ).replace(",)", ")")
            elif self.condition == "f_key_on_tracer":
                record_ids = str(
                    tuple(
                        records_to_update.mapped(
                            "x_dmt_tracer_id.source_table_primary_key"
                        )
                    )
                ).replace(",)", ")")

            query += " WHERE {} IN {}".format(self.foreign_key.name, record_ids)
            if self.filter_source_records:
                query += " AND "
                query = self.add_source_filter_conditions(query)
        elif self.filter_source_records:
            query += " WHERE "
            query = self.add_source_filter_conditions(query)

        if self.limit_number_of_records:
            query += " LIMIT {}".format(self.number_of_records_to_map)
        if self.apply_offset:
            query += " OFFSET {}".format(self.offset)

        return query

    def build_query(self, records_to_update):
        active_matches = self.get_active_matches()

        query = self.build_query_each_matches(active_matches)

        query = self.add_condition_to_query(records_to_update, query)

        return query

    def build_query_for_relational_data(self):
        column_list = []
        for match in self.relational_match_ids:
            column_list.append(match.relational_column_id.name)
        columns = ", ".join(column_list)

        query = "SELECT {} FROM {}".format(
            columns, self.source_table_schema_id.table_name
        )

        if self.filter_source_records:
            query += " WHERE "
            query = self.add_source_filter_conditions(query)

        query += " ORDER BY {} ASC ".format(self.primary_key_column_id.name)

        if self.limit_number_of_records:
            query += " LIMIT {}".format(self.number_of_records_to_map)
        if self.apply_offset:
            query += " OFFSET {}".format(self.offset)
        return query

    def get_relational_match_list(self, cursor):
        relational_match_dictionaries_list = []
        key_list = [
            key
            for key in self.relational_match_ids.mapped(
                "relational_column_id.name"
            )
        ]

        for row in cursor:
            value_list = []
            for column_value in row:
                value_list.append(column_value)
            record_dict = dict(zip(key_list, value_list))
            relational_match_dictionaries_list.append(record_dict)

        return relational_match_dictionaries_list

    def add_source_filter_conditions(self, query):
        for record_filter in self.source_record_filter_ids:
            if record_filter.is_active:
                query += "{} {} '{}' AND ".format(
                    record_filter.filtering_column_id.name,
                    record_filter.filtering_operator,
                    record_filter.filtering_value,
                )
        # Cut the last AND + spaces
        query = query[:-5]
        return query

    def build_source_record_dictionaries_list(self, cursor):
        source_record_dictionaries_list = []
        active_matches = self.match_ids.filtered(lambda match_id: match_id.is_active)
        key_list = [key.split(" -->")[0] for key in active_matches.mapped("name")]
        if self.mapping_mode == "existing_records":
            # in existing records' mode, add in the last position the foreign key in source table
            key_list.append(self.foreign_key.name)

        if self.tracing_mode:
            key_list.append(self.primary_key_column_id.name)
        for row in cursor:
            value_list = []
            for column_value in row:
                value_list.append(column_value)
            record_dict = dict(zip(key_list, value_list))
            source_record_dictionaries_list.append(record_dict)

        return source_record_dictionaries_list

    def build_odoo_model_vals_dictionaries_list(self, source_record_dictionaries_list):
        odoo_model_vals_dictionaries_list = []
        active_matches = self.match_ids.filtered(lambda match_id: match_id.is_active)
        key_list = [
            key for key in active_matches.mapped("odoo_model_field_id").mapped("name")
        ]
        if self.mapping_mode == "existing_records":
            # in existing records' mode, add in the last position the matching foreign key in odoo model
            if self.condition == "f_key_on_field":
                key_list.append(self.odoo_key.name)
            elif self.condition == "f_key_on_tracer":
                key_list.append("foreign_key")
        # Couple list of keys taken from odoo_model_field_id of each match object
        # with the list of values taken from each source record dictionary
        for dictionary in source_record_dictionaries_list:
            value_list = dictionary.values()
            odoo_model_vals_dictionary = dict(zip(key_list, value_list))
            odoo_model_vals_dictionaries_list.append(odoo_model_vals_dictionary)

        return odoo_model_vals_dictionaries_list

    def create_records(
        self,
        odoo_model_vals_dictionaries_list,
        source_record_dictionaries_list,
        relational_match_dictionaries_list,
    ):
        model_env = self.env[self.odoo_model_id.model]
        records = model_env
        logging_counter = 0
        logging_total = len(odoo_model_vals_dictionaries_list)

        # Check record creation mode
        if self.record_creation_mode == "create":
            _logger.info("Creating {} records (create mode)".format(logging_total))
            _logger.info("--------")
            records = model_env.create(odoo_model_vals_dictionaries_list)
        elif self.record_creation_mode == "form":
            for vals_dict in odoo_model_vals_dictionaries_list:
                logging_counter += 1
                _logger.info(
                    "Creating record {} of {} (form mode)".format(
                        logging_counter, logging_total
                    )
                )
                _logger.info("--------")
                with Form(self.env[self.odoo_model_id.model]) as form:
                    for key, val in vals_dict.items():
                        field = self.env["ir.model.fields"].search(
                            [
                                ("name", "=", key),
                                ("model_id", "=", self.odoo_model_id.id),
                            ]
                        )
                        if field.ttype == "many2one":
                            val = self.env[field.relation].browse(int(val))
                        setattr(form, key, val)

                    records |= form.save()
        elif self.record_creation_mode == "db_query":
            odoo_table = self.odoo_model_id.model.replace(".", "_")
            # Note: all dictionaries should have the same keys, so we can
            # arbitrarily take the keys of the first one to build the query string
            keys = ", ".join(odoo_model_vals_dictionaries_list[0].keys())

            # Many Odoo models have an active field; if not set it will be False and the record
            # would be created as archived; we avoid this by adding active field at the end of
            # the column list of the insert query and then giving it a value of True
            field_list = self.odoo_model_id.field_id.mapped("name")
            add_active = True if "active" in field_list else False
            if add_active:
                keys += ", active"

            insert_query = ""
            insert_query_first_part = "INSERT INTO {} ({}) ".format(odoo_table, keys)
            insert_count = 0
            for dictionary in odoo_model_vals_dictionaries_list:
                logging_counter += 1
                _logger.info(
                    "Creating record {} of {} (db_query mode)".format(
                        logging_counter, logging_total
                    )
                )
                _logger.info("--------")

                for value in dictionary.values():
                    # sanitize the quotes
                    value = str(value).replace("'", "''")

                values = list(dictionary.values())

                if add_active:
                    # add a true value at the end for the active field
                    values.append(True)

                placeholders = ["%s"] * len(values)

                insert_query = insert_query_first_part + "VALUES({})".format(
                    ", ".join(placeholders)
                )

                self.env.cr.execute(insert_query, tuple(values))
                insert_count += 1

        # Tracing function
        if self.mapping_mode == "new_records" and self.tracing_mode:
            # Add tracer field to destination model if not present
            tracer_field = self.env["ir.model.fields"].search(
                [
                    ("model_id", "=", self.odoo_model_id.id),
                    ("name", "=", "x_dmt_tracer_id"),
                ]
            )
            if not tracer_field:
                self.add_tracer_field_to_odoo_model()

            self.trace_records(
                records,
                source_record_dictionaries_list,
                relational_match_dictionaries_list,
            )

        if self.record_creation_mode == "create" or self.record_creation_mode == "form":
            return len(records)
        else:
            return insert_count

    def add_tracer_field_to_odoo_model(self):
        ir_model_fields = self.env["ir.model.fields"]
        vals = {
            "model": self.odoo_model_id.name,
            "model_id": self.odoo_model_id.id,
            "name": "x_dmt_tracer_id",
            "ttype": "many2one",
            "relation": "record.tracer",
            "store": True,
            "on_delete": "cascade",
        }
        ir_model_fields.sudo().create(vals)

    # Tracing function: for each object created by this mapper,
    # create a tracer object (type record.tracer) and assign to it
    def trace_records(
        self,
        records,
        source_record_dictionaries_list,
        relational_match_dictionaries_list,
    ):
        record_tracer = self.env["record.tracer"]

        rec_index = 0
        for record in records:
            foreignkey_tracers = self.env["foreignkey.tracer"]
            for match in self.relational_match_ids:
                key_value = relational_match_dictionaries_list[rec_index][
                    match.relational_column_id.name
                ]
                key_column = match.relational_column_id.id
                related_table_id = match.related_source_table_schema_id.id
                foreignkey_tracers |= foreignkey_tracers.create(
                    {
                        "key_value": key_value,
                        "key_column": key_column,
                        "related_table_id": related_table_id,
                    }
                )
            tracer = record_tracer.create(
                {
                    "mapper_id": self.id,
                    "source_table_primary_key": source_record_dictionaries_list[
                        rec_index
                    ][self.primary_key_column_id.name],
                }
            )

            tracer.foreignkey_tracer_ids = foreignkey_tracers
            record.x_dmt_tracer_id = tracer
            rec_index += 1

    def update_records(self, odoo_model_vals_dictionaries_list):
        updated_record_list = []
        if self.condition == "f_key_on_field":
            key = self.odoo_key.name
        elif self.condition == "f_key_on_tracer":
            key = "foreign_key"

        logging_counter = 0
        logging_total = len(odoo_model_vals_dictionaries_list)

        for dictionary in odoo_model_vals_dictionaries_list:
            record_id = dictionary.get(key)

            logging_counter += 1
            _logger.info(
                "Updating record with key = {}; {}/{}".format(
                    record_id, logging_counter, logging_total
                )
            )
            _logger.info("--------")

            # check to allow only one update for each record
            if not (record_id in updated_record_list):
                odoo_table = self.odoo_model_id.model.replace(".", "_")
                settings_string = ""
                if self.condition == "f_key_on_tracer":
                    del dictionary["foreign_key"]
                for item in dictionary.items():
                    # sanitize the quotes
                    value = str(item[1]).replace("'", "''")
                    settings_string += "{} = '{}', ".format(item[0], value)
                settings_string = settings_string[:-2]
                update_query = ""
                query_param_value = False
                if self.condition == "f_key_on_field":
                    update_query = "UPDATE {} SET {} WHERE {} ".format(
                        odoo_table, settings_string, key
                    )
                    query_param_value = record_id
                elif self.condition == "f_key_on_tracer":
                    record_traced = (
                        self.env[self.odoo_model_id.model]
                        .search([])
                        .filtered(
                            lambda record: record.x_dmt_tracer_id.source_table_primary_key
                            == record_id
                        )[0]
                    )
                    if record_traced:
                        update_query = "UPDATE {} SET {} WHERE id ".format(
                            odoo_table, settings_string
                        )
                        query_param_value = record_traced.id

                # All original null values were replaced with the sting 'None';
                # now they must be converted in the special SQL value NULL
                update_query = update_query.replace("'None'", "NULL")

                # This is needed to avoid % characters being interpreted as placeholders
                update_query = update_query.replace("%", "%%")

                # Add placeholder
                update_query += "= %s"

                if update_query:
                    self.env.cr.execute(update_query, (query_param_value,))
                    updated_record_list.append(record_id)
        return len(updated_record_list)

    def update_records_concat_mode(self, odoo_model_vals_dictionaries_list):
        updated_record_list = []
        key = self.odoo_key.name

        logging_counter = 0
        logging_total = len(odoo_model_vals_dictionaries_list)

        for dictionary in odoo_model_vals_dictionaries_list:
            record_id = dictionary.get(key)

            logging_counter += 1
            _logger.info(
                "Updating record with key = {}; {}/{}".format(
                    record_id, logging_counter, logging_total
                )
            )
            _logger.info("--------")

            for item in dictionary.items():
                # Matching key value is not needed in this mode
                if item[0] == key:
                    continue

                field = item[0]
                value = item[1]
                rec_ids = self.concatenate_value(value, field, key, record_id)
                updated_record_list.extend(rec_ids)

        return len(updated_record_list)

    def concatenate_value(self, value, field, key, record_id):
        records_to_update = self.env[self.odoo_model_id.model].search(
            [(key, "=", record_id)]
        )

        # Add destination filtering conditions
        if self.filter_destination_records:
            records_to_update = self.filter_records(records_to_update)

        concatenated_value = ""
        for record in records_to_update:
            if self.concatenation_mode == "to_right":
                concatenated_value = (
                    str(record[field]) + self.concatenation_operator + str(value)
                )
            elif self.concatenation_mode == "to_left":
                concatenated_value = (
                    str(value) + self.concatenation_operator + str(record[field])
                )
            record.write({field: concatenated_value})
        return records_to_update.ids

    def filter_records(self, records_to_update):
        for record_filter in self.destination_record_filter_ids:
            if record_filter.is_active:
                filter_field = record_filter.filtering_field_id.name
                filter_value = record_filter.filtering_value
                cast_to_integer = record_filter.cast_to_integer

                def equals(record):
                    return record[filter_field] == filter_value

                def equals_integer(record):
                    return int(record[filter_field]) == int(filter_value)

                def not_equals(record):
                    return record[filter_field] != filter_value

                def not_equals_integer(record):
                    return int(record[filter_field]) != int(filter_value)

                def less_than(record):
                    return int(record[filter_field]) < int(filter_value)

                def greater_than(record):
                    return int(record[filter_field]) > int(filter_value)

                if record_filter.filtering_operator == "=":
                    filtering_function = equals_integer if cast_to_integer else equals
                elif record_filter.filtering_operator == "!=":
                    filtering_function = (
                        not_equals_integer if cast_to_integer else not_equals
                    )
                elif record_filter.filtering_operator == "<":
                    filtering_function = less_than
                elif record_filter.filtering_operator == ">":
                    filtering_function = greater_than

                records_to_update = records_to_update.filtered(filtering_function)

        return records_to_update

    @staticmethod
    def convert_special_values(odoo_model_vals_dictionaries_list):
        """
        This method converts special fixed values, i.e. strings marked with
        a double starred notation at the beginning and at the end of the value;
        when you want to define a special value for fixed value in table match form
        use this method to convert it, adding an if condition in the loop
        """
        converted_dictionary_list = []
        for dictionary in odoo_model_vals_dictionaries_list:
            key_list = dictionary.keys()
            value_list = dictionary.values()
            if any(
                [
                    (str(value).startswith("**") and str(value).endswith("**"))
                    for value in value_list
                ]
            ):
                converted_value_list = []
                for value in value_list:
                    if value == "**timestamp**":
                        value = str(datetime.utcnow())
                    if value == "**empty_string**":
                        value = ""
                    converted_value_list.append(value)
                dictionary = dict(zip(key_list, converted_value_list))
            converted_dictionary_list.append(dictionary)
        return converted_dictionary_list

    def force_fixed_length(self, odoo_model_vals_dictionaries_list):
        force_fixed_matches = self.match_ids.filtered(
            lambda match: match.force_fixed_length
        )
        if not force_fixed_matches:
            return odoo_model_vals_dictionaries_list

        for dictionary in odoo_model_vals_dictionaries_list:
            for fixed_match in force_fixed_matches:
                key_to_fix = fixed_match.odoo_model_field_id.name

                # NOTE: All the fixed length functionality (padding and truncation)
                # are suitable just for string values; to ensure it, we cast to string
                # every value that needs to be forced to fixed length.
                dictionary[key_to_fix] = str(dictionary[key_to_fix])

                if (
                    len(str(dictionary[key_to_fix])) != 0
                    and len(dictionary[key_to_fix]) < fixed_match.fixed_min_length
                ):
                    if fixed_match.padding_position == "R":
                        dictionary[key_to_fix] = dictionary[key_to_fix].ljust(
                            fixed_match.fixed_min_length, fixed_match.padding_character
                        )
                    elif fixed_match.padding_position == "L":
                        dictionary[key_to_fix] = dictionary[key_to_fix].rjust(
                            fixed_match.fixed_min_length, fixed_match.padding_character
                        )
                elif (
                    len(dictionary[key_to_fix]) != 0
                    and len(dictionary[key_to_fix]) > fixed_match.fixed_max_length
                ):
                    if fixed_match.truncate_side == "R":
                        dictionary[key_to_fix] = dictionary[key_to_fix][
                            : fixed_match.fixed_max_length
                        ]
                    elif fixed_match.truncate_side == "L":
                        dictionary[key_to_fix] = dictionary[key_to_fix][
                            len(str(dictionary[key_to_fix]))
                            - fixed_match.fixed_max_length :
                        ]

        return odoo_model_vals_dictionaries_list

    def check_for_duplicate(self, odoo_model_vals_dictionaries_list):
        duplicate_checks = self.match_ids.filtered(
            lambda match: match.exclude_duplicate
        )
        if not duplicate_checks:
            return odoo_model_vals_dictionaries_list

        model_env = self.env[self.odoo_model_id.model]
        filtered_dictionaries_list = []
        comparing_values_dic = {}
        for dictionary in odoo_model_vals_dictionaries_list:
            add_to_list = False
            for check in duplicate_checks:
                key_to_check = check.odoo_model_field_id.name

                value = dictionary.get(key_to_check)
                recordset = model_env.search([(key_to_check, "=", value)])

                # Simultaneously check for duplicates in odoo db and
                # in the dictionary list itself
                if not recordset and not (
                    value in comparing_values_dic.get(key_to_check, [])
                ):
                    add_to_list = True
                else:
                    add_to_list = False
                    break
                if comparing_values_dic.get(key_to_check, None):
                    comparing_values_dic.get(key_to_check).append(value)
                else:
                    comparing_values_dic[key_to_check] = [value]

            if add_to_list:
                filtered_dictionaries_list.append(dictionary)

        return filtered_dictionaries_list

    def force_casting(self, odoo_model_vals_dictionaries_list):
        force_castings = self.match_ids.filtered(
            lambda match: match.force_casting != "no_casting"
        )
        if not force_castings:
            return odoo_model_vals_dictionaries_list
        for dictionary in odoo_model_vals_dictionaries_list:
            for cast in force_castings:
                key_to_cast = cast.odoo_model_field_id.name
                try:
                    if cast.force_casting == "integer":
                        dictionary[key_to_cast] = int(dictionary[key_to_cast])
                    elif cast.force_casting == "float":
                        dictionary[key_to_cast] = float(dictionary[key_to_cast])
                except ValueError:
                    # Handle the cast exception
                    _logger.info(
                        _("Exception occurred while converting {} to {}"),
                        dictionary[key_to_cast],
                        cast.force_casting,
                    )
        return odoo_model_vals_dictionaries_list

    def check_for_null_values(self, odoo_model_vals_dictionaries_list):
        checks = self.match_ids.filtered(lambda match: match.set_default_value_if_null)
        if not checks:
            return odoo_model_vals_dictionaries_list

        modified_dictionaries_list = []
        for dictionary in odoo_model_vals_dictionaries_list:
            for check in checks:
                key_to_check = check.odoo_model_field_id.name
                value = dictionary.get(key_to_check)
                if (
                    value is None
                    or not str(value)
                    or str(value) == "None"
                    or str(value) == " "
                    or str(value) == ""
                ):
                    dictionary[key_to_check] = check.default_value

            modified_dictionaries_list.append(dictionary)

        return modified_dictionaries_list

    def make_conversions(self, odoo_model_vals_dictionaries_list):
        checks = self.match_ids.filtered(lambda match: match.convert_values)
        if not checks:
            return odoo_model_vals_dictionaries_list

        modified_dictionaries_list = []
        for dictionary in odoo_model_vals_dictionaries_list:
            for check in checks:
                key_to_check = check.odoo_model_field_id.name
                value = dictionary.get(key_to_check)
                for conversion in check.match_conversion_ids:
                    if str(value) == conversion.original_value:
                        if not conversion.converted_value:
                            dictionary[key_to_check] = ""
                        else:
                            dictionary[key_to_check] = conversion.converted_value
            modified_dictionaries_list.append(dictionary)

        return modified_dictionaries_list

    def check_for_odoo_sequences(self, odoo_model_vals_dictionaries_list):
        # The check for the presence of the string "_**sequence**" among the values of the
        # dictionaries is performed just on the first dictionary of the list: as it is a
        # placeholder fixed value,it will be the same for all the dictionaries of the list.
        value_list = odoo_model_vals_dictionaries_list[0].values()
        if any([("_**sequence**" in str(value)) for value in value_list]):
            key_list = odoo_model_vals_dictionaries_list[0].keys()
            for dictionary in odoo_model_vals_dictionaries_list:
                for key in key_list:
                    if "_**sequence**" in str(dictionary[key]):
                        model = dictionary[key].replace("_**sequence**", "")
                        sequence = self.env["ir.sequence"].next_by_code(model) or _(
                            "New"
                        )
                        dictionary[key] = sequence

        return odoo_model_vals_dictionaries_list

    def show_import_report(self, created_records_count, updated_records_count):
        import_report_wizard = self.env["import.report.wizard"].create(
            {
                "records_model_name": self.odoo_model_id.model,
                "created_records_count": created_records_count,
                "updated_records_count": updated_records_count,
                "table_mapper_name": self.name,
            }
        )
        return {
            "type": "ir.actions.act_window",
            "view_mode": "form",
            "view_id": self.env.ref("data_migration_tool.import_report_wizard_form").id,
            "target": "new",
            "res_id": import_report_wizard.id,
            "res_model": "import.report.wizard",
        }

    def test_db_connection(self):
        if not self.source_table_schema_id.db_connector_id:
            raise ValidationError(_("Your mapper needs a db connector to import data"))
        self.source_table_schema_id.db_connector_id.test_connection_action()
