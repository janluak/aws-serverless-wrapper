from unittest import TestCase
from os import environ as os_environ
from os.path import dirname, realpath
from os import chdir, getcwd
from datesy.file_IO.json_file import load_single
from copy import deepcopy

test_item = load_single(f"{dirname(realpath(__file__))}/test_data/items/test_item.json")
test_item_primary = {"primary_partition_key": "some_identification_string"}


class TestDynamoDBBase(TestCase):
    table_name = "TableForTests"
    actual_cwd = str()

    @classmethod
    def setUpClass(cls) -> None:
        os_environ["STAGE"] = "TEST"
        os_environ[
            "WRAPPER_CONFIG_FILE"
        ] = f"{dirname(realpath(__file__))}/dynamodb_wrapper_config.json"

        cls.actual_cwd = getcwd()
        chdir(dirname(realpath(__file__)))

        from aws_serverless_wrapper.database.noSQL.dynamo_db.create_table import (
            create_dynamo_db_table_from_schema,
        )

        cls.raw_schema = load_single(
            f"{dirname(realpath(__file__))}/test_data/tables/{cls.table_name}.json"
        )
        create_dynamo_db_table_from_schema(cls.raw_schema)

    @classmethod
    def tearDownClass(cls) -> None:
        chdir(cls.actual_cwd)


class TestDynamoDBQuery(TestDynamoDBBase):
    def test_update_query_with_attribute(self):
        expected_expression = (
            "set attribute1 = :attribute1, " "attribute2 = :attribute2"
        )
        update_data = {
            "attribute1": "new_value1",
            "attribute2": "new_value2",
        }

        from aws_serverless_wrapper.database.noSQL.dynamo_db import Table

        t = Table(self.table_name)

        calculated_expression, _ = t._create_update_expression(update_data)
        self.assertEqual(expected_expression, calculated_expression)

    def test_update_query_with_dicts(self):
        expected_expression = (
            "set parent1.child1 = :parent1child1, "
            "parent1.child2 = :parent1child2, "
            "parent2.child3 = :parent2child3"
        )
        update_data = {
            "parent1": {"child1": "new_child1", "child2": "new_child2"},
            "parent2": {"child3": "new_child3"},
        }

        from aws_serverless_wrapper.database.noSQL.dynamo_db import Table

        t = Table(self.table_name)

        calculated_expression, _ = t._create_update_expression(update_data)
        self.assertEqual(expected_expression, calculated_expression)

    def test_update_query_with_nested_dicts(self):
        expected_expression = (
            "set parent1.child1.grandchild1 = :parent1child1grandchild1, "
            "parent1.child2 = :parent1child2, "
            "parent2.child3 = :parent2child3"
        )
        update_data = {
            "parent1": {
                "child1": {"grandchild1": "new_child1"},
                "child2": "new_child2",
            },
            "parent2": {"child3": "new_child3"},
        }

        from aws_serverless_wrapper.database.noSQL.dynamo_db import Table

        t = Table(self.table_name)

        calculated_expression, _ = t._create_update_expression(update_data)
        self.assertEqual(expected_expression, calculated_expression)

    # def test_update_query_add_attribute(self):
    #     expected_expression = "add attribute1 = :attribute1, " \
    #                           "attribute2 = :attribute2"
    #     update_data = {
    #         "attribute1": "new_value1",
    #         "attribute2": "new_value2",
    #     }
    #
    #     from aws_serverless_wrapper.database.dynamo_db import Table
    #     t = Table(self.table_name)
    #
    #     calculated_expression, _ = t._create_update_replace_expression(update_data, add_instead_of_replacement=True)
    #     self.assertEqual(expected_expression, calculated_expression)
    #
    # def test_update_add_attribute(self):
    #     new_attribute = {"additional_key": "additional_value"}
    #     from aws_serverless_wrapper.database.dynamo_db import Table
    #     t = Table(self.table_name)
    #
    #     t.put(test_item)
    #
    #     t.update_add_new_attribute(test_item_primary, new_attribute)
    #
    #     self.assertEqual(new_attribute["additional_key"], t.get(**test_item_primary)["additional_key"])
    #
    #     t.delete(**test_item_primary)

    def test_append_list_with_item(self):
        expected_expression = (
            "set parent1.child1 = list_append(parent1.child1, :parent1child1), "
            "parent2.child3 = list_append(parent2.child3, :parent2child3)"
        )
        update_data = {
            "parent1": {"child1": ["new_child1", "new_child2"]},
            "parent2": {"child3": ["new_child3"]},
        }

        from aws_serverless_wrapper.database.noSQL.dynamo_db import Table

        t = Table(self.table_name)

        calculated_expression, _ = t._create_update_expression(
            update_data, list_operation=True
        )
        self.assertEqual(expected_expression, calculated_expression)


class TestGetSubSchema(TestDynamoDBBase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        from aws_serverless_wrapper.database.noSQL.dynamo_db import Table

        cls.t = Table(cls.table_name)

    def test_get_first_level(self):
        sub_schema = self.t._get_sub_schema(self.raw_schema, ["some_dict"])

        self.assertEqual(self.raw_schema["properties"]["some_dict"], sub_schema)

    def test_get_nested_dict(self):
        sub_schema = self.t._get_sub_schema(
            self.raw_schema, ["some_nested_dict", "KEY1", "subKEY2"]
        )

        self.assertEqual(
            self.raw_schema["properties"]["some_nested_dict"]["properties"]["KEY1"][
                "properties"
            ]["subKEY2"],
            sub_schema,
        )

    def test_get_array(self):
        sub_schema = self.t._get_sub_schema(self.raw_schema, ["some_array"])

        self.assertEqual(self.raw_schema["properties"]["some_array"], sub_schema)


class TestCheckSubItemType(TestDynamoDBBase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        from aws_serverless_wrapper.database.noSQL.dynamo_db import Table

        cls.t = Table(cls.table_name)

    def test_first_level_string(self):
        self.t._check_sub_attribute_type({"some_string": "abcdef"})

    def test_first_level_int(self):
        self.t._check_sub_attribute_type({"some_int": 3})

    def test_nested_dict_end_value(self):
        self.t._check_sub_attribute_type({"some_nested_dict": {"KEY1": {"subKEY2": 4}}})

    def test_nested_dict_end_value_wrong_value_with_schema_error_path(self):
        from jsonschema import ValidationError

        with self.assertRaises(ValidationError) as VE:
            self.t._check_sub_attribute_type(
                {"some_nested_dict": {"KEY1": {"subKEY3": ["string_value", 4]}}}
            )

        self.assertEqual("4 is not of type 'string'", VE.exception.args[0])
        self.assertEqual(
            ["some_nested_dict", "KEY1", "subKEY3", 1], list(VE.exception.path)
        )

    def test_nested_dict_dict_value(self):
        self.t._check_sub_attribute_type(
            {"some_nested_dict": {"KEY1": {"subKEY1": "some_string", "subKEY2": 5}}}
        )

    def test_array_item1(self):
        self.t._check_sub_attribute_type({"some_array": ["some_string"]})

    def test_array_item2(self):
        self.t._check_sub_attribute_type({"some_array": [34]})

    def test_array_item3(self):
        self.t._check_sub_attribute_type(
            {"some_array": [{"KEY1": {"subKEY1": "string", "subKEY2": 45}}]}
        )

    def test_array_item_not_given_in_list(self):
        from jsonschema import ValidationError

        with self.assertRaises(ValidationError):
            self.t._check_sub_attribute_type(
                {"some_array": "some_string_not_in_an_array"}
            )

    def test_array_item_wrong_type(self):
        from jsonschema import ValidationError

        with self.assertRaises(ValidationError):
            self.t._check_sub_attribute_type({"some_array": [[[1]]]})


class TestDynamoDB(TestDynamoDBBase):
    def setUp(self) -> None:
        from aws_serverless_wrapper.database.noSQL.dynamo_db import Table

        t = Table(self.table_name)
        t.truncate()

    def tearDown(self) -> None:
        from aws_serverless_wrapper.database.noSQL.dynamo_db import Table

        t = Table(self.table_name)
        t.truncate()

    def test_put(self):
        from aws_serverless_wrapper.database.noSQL.dynamo_db import Table

        t = Table(self.table_name)
        t.put(test_item)

        loaded_item = t.get_and_delete(**test_item_primary)

        self.assertEqual(test_item, loaded_item)

    def test_get_unknown_entry(self):
        get_key = {"primary_partition_key": "abc"}

        from aws_serverless_wrapper.database.noSQL.dynamo_db import Table

        t = Table(self.table_name)

        with self.assertRaises(FileNotFoundError) as fnf:
            t.get(**get_key)

        self.assertEqual(
            {
                "statusCode": 404,
                "body": f"{get_key} not found in {t.name}",
                "headers": {"Content-Type": "text/plain"},
            },
            fnf.exception.args[0],
        )

    def test_get_with_wrong_primary(self):
        get_key = {"wrong_key": "some_identification_string"}

        from aws_serverless_wrapper.database.noSQL.dynamo_db import Table

        t = Table(self.table_name)

        with self.assertRaises(LookupError) as LE:
            t.get(**get_key)

        self.assertEqual(
            {
                "statusCode": 400,
                "body": f"Wrong primary for {t.name}: required for table is {t.pk}; "
                f"missing {t.pk}",
                "headers": {"Content-Type": "text/plain"},
            },
            LE.exception.args[0],
        )

    def test_put_item_missing_keys(self):
        item = test_item_primary.copy()
        from aws_serverless_wrapper.database.noSQL.dynamo_db import Table

        t = Table(self.table_name)

        with self.assertRaises(TypeError) as TE:
            t.put(item)

        self.assertEqual(
            {
                "statusCode": 400,
                "body": f"'some_string' is a required property for table {self.table_name} and is missing",
                "headers": {"Content-Type": "text/plain"},
            },
            TE.exception.args[0],
        )

    def test_put_get_and_delete_item(self):

        from aws_serverless_wrapper.database.noSQL.dynamo_db import Table

        t = Table(self.table_name)

        t.put(test_item)
        result = t.get(**test_item_primary)

        self.assertEqual(test_item, result)

        t.delete(**test_item_primary)

        with self.assertRaises(FileNotFoundError) as FNF:
            t.get(**test_item_primary)

        self.assertEqual(
            {
                "statusCode": 404,
                "body": f"{test_item_primary} not found in {self.table_name}",
                "headers": {"Content-Type": "text/plain"},
            },
            FNF.exception.args[0],
        )

    def test_doubled_put_item_with_same_primary(self):
        from aws_serverless_wrapper.database.noSQL.dynamo_db import Table

        t = Table(self.table_name)

        t.put(test_item)

        with self.assertRaises(FileExistsError) as FEE:
            t.put(test_item)

        self.assertEqual(
            {
                "statusCode": 409,
                "body": f"Item is already existing.\nTable: {self.table_name}\nItem: {test_item}",
                "headers": {"Content-Type": "text/plain"},
            },
            FEE.exception.args[0],
        )

        t.delete(**test_item_primary)

    def test_doubled_put_item_with_same_primary_overwrite(self):
        from aws_serverless_wrapper.database.noSQL.dynamo_db import Table

        t = Table(self.table_name)

        t.put(test_item)

        changed_item = test_item.copy()
        changed_item.update({"some_string": "NewBee"})
        t.put(changed_item, overwrite=True)
        result = t.get(**test_item_primary)
        self.assertEqual(changed_item, result)
        t.delete(**test_item_primary)

    def test_put_item_with_unexpected_property(self):
        from aws_serverless_wrapper.database.noSQL.dynamo_db import Table

        t = Table(self.table_name)

        changed_item = deepcopy(test_item)
        changed_item["some_dict"].update({"unexpected_key": "unexpected_value"})

        with self.assertRaises(TypeError) as TE:
            t.put(changed_item)

        self.assertEqual(
            {
                "statusCode": 400,
                "body": f"Additional properties are not allowed ('unexpected_key' was unexpected) for table {self.table_name}\n"
                f"path to unexpected property: ['some_dict']",
                "headers": {"Content-Type": "text/plain"},
            },
            TE.exception.args[0],
        )

    def test_delete_item(self):
        from aws_serverless_wrapper.database.noSQL.dynamo_db import Table

        t = Table(self.table_name)
        t.put(test_item)
        t.delete(**test_item_primary)

        with self.assertRaises(FileNotFoundError) as FNF:
            t.get(**test_item_primary)

        self.assertEqual(
            {
                "statusCode": 404,
                "body": f"{test_item_primary} not found in {self.table_name}",
                "headers": {"Content-Type": "text/plain"},
            },
            FNF.exception.args[0],
        )

    def test_update_with_attribute(self):
        updated_attribute = {"some_float": 249235.93}
        from aws_serverless_wrapper.database.noSQL.dynamo_db import Table

        t = Table(self.table_name)

        t.put(test_item)

        t.update_attribute(test_item_primary, **updated_attribute)

        self.assertEqual(
            updated_attribute["some_float"], t.get(**test_item_primary)["some_float"],
        )

        t.delete(**test_item_primary)

    def test_update_with_attribute_of_false_type(self):
        updated_attribute = {"some_string": False}
        from aws_serverless_wrapper.database.noSQL.dynamo_db import Table

        t = Table(self.table_name)

        t.put(test_item)

        with self.assertRaises(TypeError) as TE:
            t.update_attribute(test_item_primary, **updated_attribute)

        t.delete(**test_item_primary)

        self.assertEqual(
            {
                "statusCode": 415,
                "body": f"Wrong value type in {t.name} for key=some_string:\n"
                f"False is not of type 'string'."
                f"\nenum: ['abcdef', 'ghijkl', 'NewBee']",
                "headers": {"Content-Type": "text/plain"},
            },
            TE.exception.args[0],
        )

    def test_append_item(self):
        from aws_serverless_wrapper.database.noSQL.dynamo_db import Table

        changed_item = deepcopy(test_item)
        changed_item["some_nested_dict"]["KEY1"]["subKEY3"].append("second_string")

        t = Table(self.table_name)
        t.put(test_item)
        t.update_append_list(
            test_item_primary,
            **{"some_nested_dict": {"KEY1": {"subKEY3": ["second_string"]}}},
        )

        result = t.get(**test_item_primary)

        self.assertEqual(changed_item, result)

    def test_scan_and_truncate(self):
        from aws_serverless_wrapper.database.noSQL.dynamo_db import Table

        t = Table(self.table_name)
        t.put(test_item)

        response = t.scan()
        self.assertEqual(test_item, response["Items"][0])
        self.assertEqual(1, response["Count"])

        test_user_copy = test_item.copy()
        for n in range(5):
            test_user_copy.update(
                {"primary_partition_key": f"some_identification_string_{n}"}
            )
            t.put(test_user_copy)

        response = t.scan()
        self.assertEqual(6, response["Count"])

        t.truncate()
        response = t.scan()
        self.assertEqual(list(), response["Items"])
