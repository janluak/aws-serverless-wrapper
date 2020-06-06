from aws_serverless_wrapper.schema_validation import (
    get_schema, get_validator
)
from jsonschema.exceptions import ValidationError
from .traverse_dict import *
from boto3 import resource
from copy import deepcopy
from inspect import stack
from os import environ as os_environ
from KaHaWa_DatabaseIO.resource_config_crafter import resource_config

dynamo_db_resource = resource("dynamodb", **resource_config)

__all__ = ["Table"]


class CustomExceptionRaiser:
    def __init__(self, table):
        self.table = table

    def not_found_message(self, not_found_item):
        raise FileNotFoundError(
            {
                "statusCode": 404,
                "body": f"{not_found_item} not found in {self.table.name}",
                "headers": {"Content-Type": "text/plain"},
            }
        )

    def _primary_key_rudimentary_message(self, provided_message):
        raise LookupError(
            {
                "statusCode": 400,
                "body": f"Wrong primary for {self.table.name}: "
                        f"required for table is {self.table.pk}; {provided_message}",
                "headers": {"Content-Type": "text/plain"}
            }
        )

    def missing_primary_key(self, missing):
        raise self._primary_key_rudimentary_message(f"missing {missing}")

    def wrong_primary_key(self, given):
        raise self._primary_key_rudimentary_message(f"given {given}")

    def wrong_data_type(self, error: ValidationError):
        if error.validator == "type":
            response = {
                "statusCode": 415,
                "body": f"Wrong value type in {self.table.name} for key={'/'.join(error.absolute_path)}:\n"
                        f"{error.message}.",
                "headers": {"Content-Type": "text/plain"},
            }
            if 'enum' in error.schema and error.schema['enum']:
                response["body"] += f"\nenum: {error.schema['enum']}"
        elif error.validator == "required":
            response = {
                "statusCode": 400,
                "body": f"{error.message} for table {self.table.name} and is missing",
                "headers": {"Content-Type": "text/plain"},
            }
        else:
            response = {
                "statusCode": 500
            }

        raise TypeError(
            response
        )

    def item_already_existing(self, item):
        item = deepcopy(item)
        raise FileExistsError(
            {
                "statusCode": 409,
                "body": f"Item is already existing.\nTable: {self.table.name}\nItem: {decimal_dict_to_float(item)}",
                "headers": {"Content-Type": "text/plain"},
            }
        )


class Table:
    def __init__(self, table_name):
        self.__table_name = table_name
        self.__error_messages = CustomExceptionRaiser(self)
        self.__table = dynamo_db_resource.Table(f"{os_environ['STAGE']}-{table_name}")

        schema_directory = os_environ["WRAPPER_DATABASE_SCHEMA_DIRECTORY"]
        self.__schema = get_schema(schema_directory + self.__table_name)
        self.__validator = get_validator(schema_directory + self.__table_name)
        self.__validator_update = get_validator(schema_directory + self.__table_name, non_required=True)

    @property
    def name(self):
        return self.__table_name

    @property
    def pk(self):
        return self.__schema["default"]

    @property
    def schema(self):
        return self.__schema

    @property
    def table(self):
        return self.__table

    def _validate_input(self, given_input):
        if "update" in stack()[1].function:
            self._primary_key_checker(given_input[0])
            try:
                self.__validator_update.validate(given_input[1])
            except ValidationError as e:
                self.__error_messages.wrong_data_type(e)

        elif "put" == stack()[1].function:
            try:
                self.__validator.validate(given_input)
            except ValidationError as e:
                self.__error_messages.wrong_data_type(e)

        else:
            self._primary_key_checker(given_input)

    def _primary_key_checker(self, given_primaries):
        if not all(pk in given_primaries for pk in self.pk):
            self.__error_messages.missing_primary_key(
                [key for key in self.pk if key not in given_primaries]
            )
        elif len(given_primaries) > len(self.pk):
            self.__error_messages.wrong_primary_key(given_primaries)

    def describe(self):
        from boto3 import client

        dynamo_db_client = client("dynamodb", **resource_config)
        response = dynamo_db_client.describe_table(
            TableName=f"{os_environ['STAGE']}-{self.name}"
        )
        return response

    def get(self, **primary_dict):
        self._primary_key_checker(primary_dict)

        response = self.__table.get_item(Key=primary_dict)

        if "Item" not in response:
            self.__error_messages.not_found_message(primary_dict)
        else:
            try:
                return decimal_dict_to_float(response["Item"])
            except KeyError:
                return [decimal_dict_to_float(item) for item in response["Items"]]

    @staticmethod
    def _create_update_expression(new_data):
        # ToDo quote AWS keywords like `status` to
        #  `#status` in expression following an ExpressionAttributeName dict with {'#status': 'status'}
        expression = "set "
        expression_values = dict()
        for root in new_data:
            if isinstance(new_data[root], dict):
                for fork in new_data[root]:
                    expression += f"{root}.{fork} = :{root}{fork}, "
                    expression_values[f":{root}{fork}"] = new_data[root][fork]
            else:
                expression += f"{root} = :{root}, "
                expression_values[f":{root}"] = new_data[root]
        return expression[:-2], float_dict_to_decimal(expression_values)

    # https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Expressions.UpdateExpressions.html
    def update_attribute(self, primary_dict, **new_data):
        self._primary_key_checker(primary_dict)

        self._validate_input((primary_dict, new_data))

        expression, values = self._create_update_expression(new_data)

        self.__table.update_item(
            Key=primary_dict,
            UpdateExpression=expression,
            ExpressionAttributeValues=values,
        )

    def update_add_new_attribute(self, primary_dict, new_data: dict):
        # self._primary_key_checker(primary_dict)
        # expression, values = self._create_update_replace_expression(new_data, add_instead_of_replacement=True)
        # print(expression)
        # self.table.update_item(
        #     Key=primary_dict,
        #     UpdateExpression=expression,
        #     ExpressionAttributeValues=values
        # )
        # expression "ADD path.to.attribute :value"
        raise NotImplemented

    def update_if_not_exists(self):
        #  expression "SET path.to.attribute = if_not_exists(path.to.attribute, :newAttribute)"
        raise NotImplemented

    def update_list_item(self, primary_dict, new_item, item_no, *path_to_list):
        raise NotImplemented

    def update_append_list(self, primary_dict, new_item, *path_to_list):
        # self._primary_key_checker(primary_dict)
        #
        # self._check_attribute_type(new_data, self.schema["properties"])
        #
        # "set history = list_append(history, :new_coffee_config)",
        #  expression "SET path.to.attribute = list_append(:newAttribute, path.to.attribute)"
        raise NotImplemented

    def update_increment(self, primary, path_of_to_increment):
        #  response = table.update_item(
        #     Key={
        #         'year': year,
        #         'title': title
        #     },
        #     UpdateExpression="set path.to.attribute = path.to.attribute + :val",
        #     ExpressionAttributeValues={
        #         ':val': decimal.Decimal(1)
        #     },
        #     ReturnValues="UPDATED_NEW"        # return the new value of the increased attribute
        # )
        raise NotImplemented

    def put(self, item, overwrite=False):
        # ToDo resource is not closed with Unittests -> quick fix: restart of docker every now and then
        self._validate_input(item)

        try:
            item = deepcopy(item)
            self.__table.put_item(
                Item=float_dict_to_decimal(item),
                ConditionExpression=" and ".join(
                    [f"attribute_not_exists({pk})" for pk in self.pk]
                ),
            ) if not overwrite else self.__table.put_item(
                Item=float_dict_to_decimal(item)
            )

        except Exception as e:
            if (
                    e.__dict__["response"]["Error"]["Code"]
                    == "ConditionalCheckFailedException"
            ):
                self.__error_messages.item_already_existing(item)
            else:
                raise e

    def remove_attribute(self, primary_dict, path_of_attribute):
        # expression "REMOVE path.to.attribute, path.to.attribute2"
        raise NotImplemented

    def remove_entry_in_list(self, primary_dict, path_to_list, position_to_delete: int):
        # expression "REMOVE path.to.list[position_to_delete]"
        raise NotImplemented

    def delete(self, **primary_dict):
        self._primary_key_checker(primary_dict.keys())
        self.__table.delete_item(Key=primary_dict)

    def get_and_delete(self, **primary_dict):
        response = self.get(**primary_dict)
        self.delete(**primary_dict)
        return response

    def scan(self):
        response = self.__table.scan()
        response["Items"] = [decimal_dict_to_float(item) for item in response["Items"]]
        return response

    def truncate(self):
        with self.__table.batch_writer() as batch:
            for item in self.scan()["Items"]:
                batch.delete_item(Key={key: item[key] for key in self.pk})
