from unittest import TestCase
from os import environ as os_environ
from os.path import dirname, realpath
from os import chdir, getcwd
from datesy.file_IO.json_file import load_single

test_item = load_single(f"{dirname(realpath(__file__))}/test_data/items/test_item.json")
test_item_primary = {"primary_partition_key": "some_identification_string"}


class TestDynamoDBBase(TestCase):
    table_name = "TableForTests"
    actual_cwd = str()

    @classmethod
    def setUpClass(cls) -> None:
        os_environ["STAGE"] = "TEST"
        os_environ["WRAPPER_CONFIG_FILE"] = "dynamodb_wrapper_config.json"

        cls.actual_cwd = getcwd()
        chdir(dirname(realpath(__file__)))

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

        from aws_serverless_wrapper.database.dynamo_db import Table

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

        from aws_serverless_wrapper.database.dynamo_db import Table

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


class TestDynamoDB(TestDynamoDBBase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()

        from aws_serverless_wrapper.database.dynamo_db import create_dynamo_db_table_from_schema

        create_dynamo_db_table_from_schema(
            load_single(f"test_data/tables/{cls.table_name}.json")
        )

    def setUp(self) -> None:
        from aws_serverless_wrapper.database.dynamo_db import Table

        t = Table(self.table_name)
        t.truncate()

    def test_put(self):
        from aws_serverless_wrapper.database.dynamo_db import Table

        t = Table(self.table_name)
        t.put(test_item)

        loaded_item = t.get_and_delete(**test_item_primary)

        self.assertEqual(test_item, loaded_item)

    def test_get_unknown_entry(self):
        get_key = {"primary_partition_key": "abc"}

        from aws_serverless_wrapper.database.dynamo_db import Table

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

        from aws_serverless_wrapper.database.dynamo_db import Table

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
        from aws_serverless_wrapper.database.dynamo_db import Table

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

        from aws_serverless_wrapper.database.dynamo_db import Table

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
        from aws_serverless_wrapper.database.dynamo_db import Table

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
        from aws_serverless_wrapper.database.dynamo_db import Table

        t = Table(self.table_name)

        t.put(test_item)

        changed_item = test_item.copy()
        changed_item.update({"some_string": "NewBee"})
        t.put(changed_item, overwrite=True)
        result = t.get(**test_item_primary)
        self.assertEqual(changed_item, result)
        t.delete(**test_item_primary)

    def test_delete_item(self):
        from aws_serverless_wrapper.database.dynamo_db import Table

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
        from aws_serverless_wrapper.database.dynamo_db import Table

        t = Table(self.table_name)

        t.put(test_item)

        t.update_attribute(test_item_primary, **updated_attribute)

        self.assertEqual(
            updated_attribute["some_float"], t.get(**test_item_primary)["some_float"],
        )

        t.delete(**test_item_primary)

    def test_update_with_attribute_of_false_type(self):
        updated_attribute = {"some_string": False}
        from aws_serverless_wrapper.database.dynamo_db import Table

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

    def test_scan_and_truncate(self):
        from aws_serverless_wrapper.database.dynamo_db import Table

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
