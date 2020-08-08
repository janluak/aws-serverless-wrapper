from ...._helper import (
    object_with_decimal_to_float,
    object_with_float_to_decimal,
    find_path_values_in_dict,
)
from ...._helper import environ
from string import ascii_lowercase
from boto3 import resource
from botocore.exceptions import ClientError
from copy import deepcopy
from .resource_config import resource_config
from .._base_class import NoSQLTable

dynamo_db_resource = resource("dynamodb", **resource_config)

__all__ = ["Table"]

_value_update_chars = list()
for c1 in ascii_lowercase:
    for c2 in ascii_lowercase:
        _value_update_chars.append(c1 + c2)


class Table(NoSQLTable):
    def __init__(self, table_name):
        super().__init__(table_name)
        self.__table = dynamo_db_resource.Table(f"{environ['STAGE']}-{table_name}")

    @property
    def table(self):
        return self.__table

    @property
    def _item_not_exists_condition(self):
        return " and ".join([f"attribute_not_exists({pk})" for pk in self.pk])

    @property
    def _item_exists_condition(self):
        return " and ".join([f"attribute_exists({pk})" for pk in self.pk])

    def describe(self):
        from boto3 import client

        dynamo_db_client = client("dynamodb", **resource_config)
        response = dynamo_db_client.describe_table(
            TableName=f"{environ['STAGE']}-{self.name}"
        )
        return response

    def get(self, **primary_dict):
        self._primary_key_checker(primary_dict)

        response = self.__table.get_item(Key=primary_dict)

        if "Item" not in response:
            self.custom_exception.not_found_message(primary_dict)
        else:
            try:
                return object_with_decimal_to_float(response["Item"])
            except KeyError:
                return [
                    object_with_decimal_to_float(item) for item in response["Items"]
                ]

    @staticmethod
    def _create_update_expression(
        new_data: dict = None,
        *,
        paths_to_new_data=None,
        values_per_path=None,
        list_operation: (bool, list, tuple) = False,
    ):
        expression = "set "
        expression_values = dict()

        if not paths_to_new_data or not values_per_path:
            paths_to_new_data, values_per_path = find_path_values_in_dict(new_data)

        if isinstance(list_operation, bool):
            list_operation = [list_operation for i in paths_to_new_data]

        attribute_key_mapping = dict()
        letters_used = 0

        def update_expression_attribute():
            if list_operation[path_no]:
                return f"list_append({string_path_to_attribute}, :{_value_update_chars[path_no]})"
            return f":{_value_update_chars[path_no]}"

        def update_expression_value():
            expression_values[f":{_value_update_chars[path_no]}"] = values_per_path[
                path_no
            ]

        def assign_key_to_attribute_path_step(attribute_name, letter_count):
            if attribute_name not in attribute_key_mapping:
                attribute_key_mapping[
                    attribute_name
                ] = f"#{_value_update_chars[letter_count].upper()}"
                letter_count += 1
            return letter_count

        def create_path_to_attribute_with_mapped_keys(
            left_path_to_process, path_with_keys, letter_count
        ):
            for step in left_path_to_process:
                letter_count = assign_key_to_attribute_path_step(step, letter_count)

                path_with_keys.append(attribute_key_mapping[step])

            return path_with_keys, letter_count

        for path_no in range(len(paths_to_new_data)):
            path = paths_to_new_data[path_no]

            path_with_letter_keys = list()

            (
                path_with_letter_keys,
                letters_used,
            ) = create_path_to_attribute_with_mapped_keys(
                path, path_with_letter_keys, letters_used
            )

            string_path_to_attribute = ".".join(path_with_letter_keys)

            expression += (
                f"{string_path_to_attribute} = {update_expression_attribute()}, "
            )

            update_expression_value()

        return (
            expression[:-2],
            object_with_float_to_decimal(expression_values),
            {v: k for k, v in attribute_key_mapping.items()},
        )

    def __general_update(
        self,
        primary_dict,
        create_item_if_non_existent,
        list_operation=False,
        **new_data,
    ):
        self._primary_key_checker(primary_dict)

        self._validate_input(new_data)

        expression, values, expression_name_map = self._create_update_expression(
            new_data, list_operation=list_operation
        )

        update_dict = {
            "Key": primary_dict,
            "UpdateExpression": expression,
            "ExpressionAttributeValues": values,
            "ExpressionAttributeNames": expression_name_map,
        }

        if create_item_if_non_existent:
            update_dict.update(ConditionExpression=self._item_exists_condition)

        try:
            self.__table.update_item(**update_dict)
        except ClientError as CE:
            if (
                CE.response["Error"]["Code"] == "ConditionalCheckFailedException"
                and create_item_if_non_existent
            ):
                item = primary_dict.copy()
                item.update(new_data)
                self.__table.put_item(Item=object_with_float_to_decimal(item))
            elif CE.response["Error"]["Code"] == "ConditionalCheckFailedException":
                raise self.custom_exception.not_found_message(primary_dict)
            elif CE.response["Error"]["Code"] == "ValidationException" and any(
                i in CE.args[0]
                for i in [
                    "document path provided in the update expression is invalid for update",
                    "provided expression refers to an attribute that does not exist in the item",
                ]
            ):
                from ...._helper import find_new_paths_in_dict

                try:
                    item = self.get(**primary_dict)
                    path_dict, new_sub_dict = find_new_paths_in_dict(item, new_data)
                    (
                        expression,
                        values,
                        expression_name_map,
                    ) = self._create_update_expression(
                        paths_to_new_data=path_dict, values_per_path=new_sub_dict
                    )
                    update_dict = {
                        "Key": primary_dict,
                        "UpdateExpression": expression,
                        "ExpressionAttributeValues": values,
                        "ExpressionAttributeNames": expression_name_map,
                    }
                    self.__table.update_item(**update_dict)
                except FileNotFoundError:
                    item = primary_dict.copy()
                    item.update(new_data)
                    self.put(item)
            else:
                raise CE

    # https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Expressions.UpdateExpressions.html
    def add_new_attribute(self, primary_dict, new_data: dict, update_if_existent=False):
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

    def update_attribute(
        self,
        primary_dict,
        set_new_attribute_if_not_existent=False,
        create_item_if_non_existent=False,
        **new_data,
    ):
        self.__general_update(primary_dict, create_item_if_non_existent, **new_data)

    def update_list_item(self, primary_dict, item_no, **new_data):
        raise NotImplemented

    def update_append_list(
        self, primary_dict, create_item_if_non_existent=False, **new_data
    ):
        self.__general_update(
            primary_dict, create_item_if_non_existent, list_operation=True, **new_data
        )

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
            item_copy = deepcopy(item)
            self.__table.put_item(
                Item=object_with_float_to_decimal(item_copy),
                ConditionExpression=self._item_not_exists_condition,
            ) if not overwrite else self.__table.put_item(
                Item=object_with_float_to_decimal(item_copy)
            )

        except ClientError as CE:
            if CE.response["Error"]["Code"] == "ConditionalCheckFailedException":
                self.custom_exception.item_already_existing(item)
            else:
                raise CE

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
        response["Items"] = [
            object_with_decimal_to_float(item) for item in response["Items"]
        ]
        return response

    def truncate(self):
        with self.__table.batch_writer() as batch:
            for item in self.scan()["Items"]:
                batch.delete_item(Key={key: item[key] for key in self.pk})
