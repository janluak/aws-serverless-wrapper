from ...._helper import (
    object_with_decimal_to_float,
    object_with_float_to_decimal,
    find_path_values_in_dict,
)
from ...._helper import environ
from boto3 import resource
from copy import deepcopy
from .resource_config import resource_config
from .._base_class import NoSQLTable

dynamo_db_resource = resource("dynamodb", **resource_config)

__all__ = ["Table"]


class Table(NoSQLTable):
    def __init__(self, table_name):
        super().__init__(table_name)
        self.__table = dynamo_db_resource.Table(f"{environ['STAGE']}-{table_name}")

    @property
    def table(self):
        return self.__table

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
    def _create_update_expression(new_data, list_operation=False):
        # ToDo quote AWS keywords like `status` to
        #  `#status` in expression following an ExpressionAttributeName dict with {'#status': 'status'}
        expression = "set "
        expression_values = dict()
        paths, values = find_path_values_in_dict(new_data)

        def update_expression_attribute():
            if list_operation:
                return (
                    f"list_append({string_path_to_attribute}, :{string_path_variable})"
                )
            return f":{string_path_variable}"

        for path_no in range(len(paths)):
            path = paths[path_no]
            string_path_to_attribute = ".".join(path)
            string_path_variable = "".join(path)

            expression += (
                f"{string_path_to_attribute} = {update_expression_attribute()}, "
            )
            expression_values[f":{string_path_variable}"] = values[path_no]

        return expression[:-2], object_with_float_to_decimal(expression_values)

    # https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Expressions.UpdateExpressions.html
    def update_attribute(self, primary_dict, **new_data):
        self._primary_key_checker(primary_dict)

        self._validate_input(new_data)

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

    def update_list_item(self, primary_dict, new_item, item_no, path_to_list):
        raise NotImplemented

    def update_append_list(self, primary_dict, **new_data):
        self._primary_key_checker(primary_dict)

        self._validate_input(new_data)

        expression, values = self._create_update_expression(
            new_data, list_operation=True
        )

        self.__table.update_item(
            Key=primary_dict,
            UpdateExpression=expression,
            ExpressionAttributeValues=values,
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
                ConditionExpression=" and ".join(
                    [f"attribute_not_exists({pk})" for pk in self.pk]
                ),
            ) if not overwrite else self.__table.put_item(
                Item=object_with_float_to_decimal(item_copy)
            )

        except Exception as e:
            if (
                e.__dict__["response"]["Error"]["Code"]
                == "ConditionalCheckFailedException"
            ):
                self.custom_exception.item_already_existing(item)
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
        response["Items"] = [
            object_with_decimal_to_float(item) for item in response["Items"]
        ]
        return response

    def truncate(self):
        with self.__table.batch_writer() as batch:
            for item in self.scan()["Items"]:
                batch.delete_item(Key={key: item[key] for key in self.pk})
