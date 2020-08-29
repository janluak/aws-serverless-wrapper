from unittest import TestCase
from os.path import dirname, realpath
from datesy.file_IO.json_file import load_single


class TestSchemaLoadingFromFile(TestCase):
    def test_load_basic_schema(self):
        from aws_serverless_wrapper.schema_validation.schema_validator import (
            SchemaValidator,
        )

        schema_file = (
            f"{dirname(realpath(__file__))}/test_data/database/schema_basic.json"
        )

        expected_schema = load_single(schema_file)

        validator = SchemaValidator(file=schema_file)
        loaded_schema = validator.schema
        self.assertEqual(expected_schema, loaded_schema)

    def test_load_nested_schema(self):
        from aws_serverless_wrapper.schema_validation.schema_validator import (
            SchemaValidator,
        )

        base_schema_file = (
            f"{dirname(realpath(__file__))}/test_data/database/schema_nested.json"
        )

        expected_schema = load_single(base_schema_file)

        validator = SchemaValidator(file=base_schema_file)
        loaded_schema = validator.schema

        self.assertEqual(expected_schema, loaded_schema)


class TestSchemaLoadingFromURL(TestCase):
    pass
