from unittest import TestCase
from os.path import dirname, realpath
from datesy.file_IO.json_file import load_single
from os import getcwd, chdir


class TestAPIValidation(TestCase):
    def test_basic_with_schema_file(self):
        from aws_serverless_wrapper.schema_validation.api_validation import (
            APIDataValidator,
        )

        api_schema_file = f"{dirname(realpath(__file__))}/test_data/api/api_basic.json"
        api_data = load_single(
            f"{dirname(realpath(__file__))}/test_data/api/request_basic.json"
        )
        APIDataValidator(file=api_schema_file, api_data=api_data)

    def test_basic_with_schema_file_including_http_method(self):
        from aws_serverless_wrapper.schema_validation.api_validation import (
            APIDataValidator,
        )

        api_schema_file = (
            f"{dirname(realpath(__file__))}/test_data/api/api_basic-POST.json"
        )
        api_data = load_single(
            f"{dirname(realpath(__file__))}/test_data/api/request_basic.json"
        )
        APIDataValidator(file=api_schema_file, api_data=api_data)

    def test_basic_with_schema_directory(self):
        from aws_serverless_wrapper.schema_validation.api_validation import (
            APIDataValidator,
        )

        api_schema_directory = f"{dirname(realpath(__file__))}/test_data/api/"
        api_data = load_single(
            f"{dirname(realpath(__file__))}/test_data/api/request_basic.json"
        )

        def api_basic():
            APIDataValidator(file=api_schema_directory, api_data=api_data)

        api_basic()

    def test_basic_with_relative_schema_file(self):
        from aws_serverless_wrapper.schema_validation.api_validation import (
            APIDataValidator,
        )

        actual_cwd = getcwd()
        try:
            chdir(dirname(realpath(__file__)))

            api_schema_file = "./test_data/api/api_basic.json"
            api_data = load_single("./test_data/api/request_basic.json")

            APIDataValidator(file=api_schema_file, api_data=api_data)
        finally:
            chdir(actual_cwd)

    def test_basic_with_relative_schema_directory(self):
        from aws_serverless_wrapper.schema_validation.api_validation import (
            APIDataValidator,
        )

        actual_cwd = getcwd()
        try:
            chdir(dirname(realpath(__file__)))
            api_schema_directory = "./test_data/api/"
            api_data = load_single("./test_data/api/request_basic.json")

            def api_basic():
                APIDataValidator(file=api_schema_directory, api_data=api_data)

            api_basic()
        finally:
            chdir(actual_cwd)

    def test_basic_with_wrong_httpMethod(self):
        from aws_serverless_wrapper.schema_validation.api_validation import (
            APIDataValidator,
        )

        api_schema_file = f"{dirname(realpath(__file__))}/test_data/api/api_basic.json"
        api_data = load_single(
            f"{dirname(realpath(__file__))}/test_data/api/request_basic.json"
        )
        api_data["httpMethod"] = "WRONG"

        with self.assertRaises(EnvironmentError) as TE:
            APIDataValidator(file=api_schema_file, api_data=api_data)

        self.assertEqual(
            {
                "statusCode": 501,
                "body": "API is not defined",
                "headers": {"Content-Type": "text/plain"},
            },
            TE.exception.args[0],
        )

    def test_basic_with_missing_body(self):
        from aws_serverless_wrapper.schema_validation.api_validation import (
            APIDataValidator,
        )

        api_schema_file = f"{dirname(realpath(__file__))}/test_data/api/api_basic.json"
        api_data = load_single(
            f"{dirname(realpath(__file__))}/test_data/api/request_basic.json"
        )
        api_data.pop("body")

        with self.assertRaises(TypeError) as TE:
            APIDataValidator(file=api_schema_file, api_data=api_data)

        self.assertEqual(
            {
                "statusCode": 400,
                "body": "'body' is a required property",
                "headers": {"Content-Type": "text/plain"},
            },
            TE.exception.args[0],
        )

    def test_basic_with_wrong_body(self):
        from aws_serverless_wrapper.schema_validation.api_validation import (
            APIDataValidator,
        )

        api_schema_file = f"{dirname(realpath(__file__))}/test_data/api/api_basic.json"
        api_data = load_single(
            f"{dirname(realpath(__file__))}/test_data/api/request_basic.json"
        )

        from json import loads, dumps

        api_data["body"] = loads(api_data["body"])
        api_data["body"]["body_key1"] = 123
        api_data["body"] = dumps(api_data["body"])

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
                "    123",
                "headers": {"Content-Type": "text/plain"},
            },
            TE.exception.args[0],
        )

    def test_basic_with_body_directly_as_dict(self):
        from aws_serverless_wrapper.schema_validation.api_validation import (
            APIDataValidator,
        )

        api_schema_file = f"{dirname(realpath(__file__))}/test_data/api/api_basic.json"
        api_data = load_single(
            f"{dirname(realpath(__file__))}/test_data/api/request_basic.json"
        )

        from json import loads

        api_data["body"] = loads(api_data["body"])

        APIDataValidator(file=api_schema_file, api_data=api_data)

    def test_basic_with_missing_path_parameter(self):
        from aws_serverless_wrapper.schema_validation.api_validation import (
            APIDataValidator,
        )

        api_schema_file = f"{dirname(realpath(__file__))}/test_data/api/api_basic.json"
        api_data = load_single(
            f"{dirname(realpath(__file__))}/test_data/api/request_basic.json"
        )
        api_data.pop("pathParameters")

        with self.assertRaises(TypeError) as TE:
            APIDataValidator(file=api_schema_file, api_data=api_data)

        self.assertEqual(
            {
                "statusCode": 400,
                "body": "'pathParameters' is a required property",
                "headers": {"Content-Type": "text/plain"},
            },
            TE.exception.args[0],
        )

    def test_complete_aws_rest_event_data(self):
        from aws_serverless_wrapper.schema_validation.api_validation import (
            APIDataValidator,
        )

        api_schema_file = f"{dirname(realpath(__file__))}/test_data/api/api_basic.json"
        api_data = load_single(
            f"{dirname(realpath(__file__))}/test_data/api/request_aws_http_event.json"
        )
        APIDataValidator(file=api_schema_file, api_data=api_data)

    def test_non_rest_event(self):
        from aws_serverless_wrapper.schema_validation.api_validation import (
            APIDataValidator,
        )

        api_schema_file = f"{dirname(realpath(__file__))}/test_data/api/api_basic.json"
        api_data = {"body_key1": "some_string", "body_key2": {"key2.1": 2}}
        APIDataValidator(file=api_schema_file, api_data=api_data)

        api_data = {"body_key1": "some_string", "body_key2": 2}
        with self.assertRaises(TypeError):
            APIDataValidator(file=api_schema_file, api_data=api_data)
