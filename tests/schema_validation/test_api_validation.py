from unittest import TestCase
from os import environ as os_environ
from os.path import dirname, realpath
from os import chdir, getcwd
from datesy.file_IO.json_file import load_single
from jsonschema.exceptions import ValidationError


class TestAPIValidation(TestCase):
    actual_cwd = str()

    @classmethod
    def setUpClass(cls) -> None:
        cls.actual_cwd = getcwd()
        chdir(dirname(realpath(__file__)))
        os_environ["WRAPPER_CONFIG_FILE"] = "schema_wrapper_config.json"

    @classmethod
    def tearDownClass(cls) -> None:
        chdir(cls.actual_cwd)

    def test_basic(self):
        from aws_serverless_wrapper.schema_validation.api_validation import APIDataValidator

        api_schema_file = "test_data/api/api_basic.json"
        api_data = load_single("test_data/api/request_basic.json")
        APIDataValidator(file=api_schema_file, api_data=api_data)

    def test_basic_with_wrong_httpMethod(self):
        from aws_serverless_wrapper.schema_validation.api_validation import APIDataValidator

        api_schema_file = "test_data/api/api_basic.json"
        api_data = load_single("test_data/api/request_basic.json")
        api_data["httpMethod"] = "WRONG"

        with self.assertRaises(EnvironmentError) as TE:
            APIDataValidator(file=api_schema_file, api_data=api_data)

        self.assertEqual(
            {
                "statusCode": 501,
                "body": "API is not defined",
                "headers": {"Content-Type": "text/plain"},
            },
            TE.exception.args[0]
        )

    def test_basic_with_missing_body(self):
        from aws_serverless_wrapper.schema_validation.api_validation import APIDataValidator

        api_schema_file = "test_data/api/api_basic.json"
        api_data = load_single("test_data/api/request_basic.json")
        api_data.pop("body")

        with self.assertRaises(TypeError) as TE:
            APIDataValidator(file=api_schema_file, api_data=api_data)

        self.assertEqual(
            {
                "statusCode": 400,
                "body": "body has to be included",
                "headers": {"Content-Type": "text/plain"},
            },
            TE.exception.args[0]
        )

    def test_basic_with_wrong_body(self):
        from aws_serverless_wrapper.schema_validation.api_validation import APIDataValidator

        api_schema_file = "test_data/api/api_basic.json"
        api_data = load_single("test_data/api/request_basic.json")
        api_data["body"]["body_key1"] = 123

        with self.assertRaises(TypeError) as TE:
            APIDataValidator(file=api_schema_file, api_data=api_data)

        self.assertEqual(
            {
                "statusCode": 400,
                "body": "123 is not of type 'string'\n\n"
                        "Failed validating 'type' in "
                        "schema['properties']['body']['properties']['body_key1']:\n"
                        "    {'description': 'containing only a string', 'type': 'string'}\n\n"
                        "On instance['body']['body_key1']:\n"
                        '    123',
                "headers": {"Content-Type": "text/plain"},
            },
            TE.exception.args[0]
        )

    def test_basic_with_missing_path_parameter(self):
        from aws_serverless_wrapper.schema_validation.api_validation import APIDataValidator

        api_schema_file = "test_data/api/api_basic.json"
        api_data = load_single("test_data/api/request_basic.json")
        api_data.pop("pathParameters")

        with self.assertRaises(TypeError) as TE:
            APIDataValidator(file=api_schema_file, api_data=api_data)

        self.assertEqual(
            {
                "statusCode": 400,
                "body": "pathParameters has to be included",
                "headers": {"Content-Type": "text/plain"},
            },
            TE.exception.args[0]
        )
