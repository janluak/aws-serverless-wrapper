from unittest import TestCase
from os import environ as os_environ
from os.path import dirname, realpath
from os import chdir, getcwd
from datesy.file_IO.json_file import load_single
from jsonschema.exceptions import ValidationError


class TestSchemaValidation(TestCase):
    actual_cwd = str()

    @classmethod
    def setUpClass(cls) -> None:
        cls.actual_cwd = getcwd()
        chdir(dirname(realpath(__file__)))
        os_environ["UnitTest"] = "True"
        os_environ["WRAPPER_DATABASE"] = "DynamoDB"
        os_environ["AWS_REGION"] = "local"

    @classmethod
    def tearDownClass(cls) -> None:
        chdir(cls.actual_cwd)

    def test_basic_schema(self):
        from aws_serverless_wrapper.schema_validation import get_validator

        test_item = load_single("test_data/database/item_basic.json")

        schema_file = dirname(realpath(__file__)) + "/test_data/database/schema_basic.json"
        validator = get_validator(schema_file)

        validator.validate(test_item)

    def test_basic_schema_wrong_data(self):
        from aws_serverless_wrapper.schema_validation import get_validator

        test_item = load_single("test_data/database/item_basic_wrong.json")

        schema_file = dirname(realpath(__file__)) + "/test_data/database/schema_basic.json"
        validator = get_validator(schema_file)

        try:
            validator.validate(test_item)
            self.fail()
        except ValidationError:
            pass

    def test_nested_schema(self):
        from aws_serverless_wrapper.schema_validation import get_validator

        test_item = load_single("test_data/database/item_nested.json")

        schema_file = dirname(realpath(__file__)) + "/test_data/database/schema_nested.json"
        validator = get_validator(schema_file)

        validator.validate(test_item)
