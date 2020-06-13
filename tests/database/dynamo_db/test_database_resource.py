from unittest import TestCase
from os import environ as os_environ
from os.path import dirname, realpath
from os import chdir, getcwd
from datesy.file_IO.json_file import load_single

test_item = load_single(f"{dirname(realpath(__file__))}/test_data/items/test_item.json")
test_item_primary = {"primary_partition_key": "some_identification_string"}


class TestDynamoDBResource(TestCase):
    table_name = "TableForTests"
    actual_cwd = str()
    table = object

    @classmethod
    def setUpClass(cls) -> None:
        os_environ["STAGE"] = "TEST"
        os_environ["WRAPPER_CONFIG_FILE"] = "dynamodb_wrapper_config.json"

        cls.actual_cwd = getcwd()
        chdir(dirname(realpath(__file__)))

        from aws_serverless_wrapper.database.dynamo_db import Table
        cls.table = Table(cls.table_name)

    @classmethod
    def tearDownClass(cls) -> None:
        chdir(cls.actual_cwd)
        cls.table.delete(**test_item_primary)

    def setUp(self) -> None:
        self.table.put(test_item, overwrite=True)


class TestSimpleDynamoDBResource(TestDynamoDBResource):
    def test_get_item_from_resource(self):
        from aws_serverless_wrapper.database import DatabaseResourceController
        database_resource = DatabaseResourceController()

        loaded_item = database_resource[self.table_name].get(**test_item_primary)

        self.assertEqual(test_item, loaded_item)

    def test_resource_returns_table(self):
        from aws_serverless_wrapper.database import DatabaseResourceController
        from aws_serverless_wrapper.database.dynamo_db import Table
        database_resource = DatabaseResourceController()

        self.assertEqual(
            type(Table(self.table_name)),
            type(database_resource[self.table_name])
        )


class TestReusedDynamoDBResource(TestDynamoDBResource):
    # ToDo check re-usage of connection -> only one entry if accessing table twice
    pass
