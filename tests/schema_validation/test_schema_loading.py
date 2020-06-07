from unittest import TestCase
from os import environ as os_environ
from os.path import dirname, realpath
from os import chdir, getcwd
from datesy.file_IO.json_file import load_single


class TestSchemaLoading(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        os_environ["UnitTest"] = "True"
        os_environ["WRAPPER_DATABASE"] = "DynamoDB"
        os_environ["AWS_REGION"] = "local"


class TestSchemaLoadingFromFile(TestSchemaLoading):
    actual_cwd = str()

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.actual_cwd = getcwd()
        chdir(dirname(realpath(__file__)))

    @classmethod
    def tearDownClass(cls) -> None:
        chdir(cls.actual_cwd)

    def test_load_basic_schema(self):
        from aws_serverless_wrapper.schema_validation.schema_validator import SchemaValidator

        schema_file = "test_data/database/schema_basic.json"

        expected_schema = load_single(schema_file)

        validator = SchemaValidator(file=schema_file)
        loaded_schema = validator.schema
        self.assertEqual(expected_schema, loaded_schema)


class TestSchemaLoadingFromURL(TestSchemaLoading):
    pass
