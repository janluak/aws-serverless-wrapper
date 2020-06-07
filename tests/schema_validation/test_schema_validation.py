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

    @classmethod
    def tearDownClass(cls) -> None:
        chdir(cls.actual_cwd)

    def test_basic_schema(self):
        from aws_serverless_wrapper.schema_validation import SchemaValidator

        test_item = load_single("test_data/database/item_basic.json")

        schema_file = dirname(realpath(__file__)) + "/test_data/database/schema_basic.json"
        validator = SchemaValidator(file=schema_file)

        validator.validator.validate(test_item)

    def test_basic_schema_wrong_data(self):
        from aws_serverless_wrapper.schema_validation import SchemaValidator

        test_item = load_single("test_data/database/item_basic_wrong.json")

        schema_file = dirname(realpath(__file__)) + "/test_data/database/schema_basic.json"
        validator = SchemaValidator(file=schema_file)

        try:
            validator.validator.validate(test_item)
            self.fail()
        except ValidationError:
            pass

    def test_nested_schema(self):
        from aws_serverless_wrapper.schema_validation import SchemaValidator

        test_item = load_single("test_data/database/item_nested.json")

        schema_file = dirname(realpath(__file__)) + "/test_data/database/schema_nested.json"
        validator = SchemaValidator(file=schema_file)

        validator.validator.validate(test_item)

    def test_basic_schema_without_required(self):
        from aws_serverless_wrapper.schema_validation import SchemaValidator

        test_item = load_single("test_data/database/item_basic.json")

        test_item.pop("some_float")

        schema_file = dirname(realpath(__file__)) + "/test_data/database/schema_basic.json"
        validator = SchemaValidator(file=schema_file)

        validator.validator_without_required.validate(test_item)

    def test_basic_schema_without_required_nested(self):
        from aws_serverless_wrapper.schema_validation import SchemaValidator

        test_item = load_single("test_data/database/item_basic.json")

        test_item["some_nested_dict"]["KEY1"].pop("subKEY2")

        schema_file = dirname(realpath(__file__)) + "/test_data/database/schema_basic.json"
        validator = SchemaValidator(file=schema_file)

        validator.validator_without_required.validate(test_item)

